from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.template.loader import render_to_string
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView

from core.models import Fund, Subscription
from core.permissions import IsFundManager, IsOwnerOrFundManager
from core.serializers import FundSerializer, InvestorSerializer, SubscriptionSerializer
from django_filters.rest_framework import DjangoFilterBackend

from core.services import SubscriptionService


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Overwrites the SimpleJWT login view to add a request limit
    and prevent brute force attacks.
    """

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"


class FundViewSet(viewsets.ModelViewSet):
    queryset = Fund.objects.all()
    serializer_class = FundSerializer

    def get_permissions(self):
        # Everyone can see the funds, but only the Manager can create/edit/delete
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated()]
        return [IsFundManager()]


class InvestorViewSet(viewsets.ModelViewSet):
    queryset = get_user_model().objects.all()

    def get_queryset(self):
        is_manager = getattr(self.request.user, "is_staff", False)

        if is_manager:
            return get_user_model().objects.filter(is_superuser=False)
        # An investor can only see their own profile
        return get_user_model().objects.filter(id=self.request.user.pk)

    serializer_class = InvestorSerializer

    def get_permissions(self):
        # Everyone can view lists (limited by the queryset), but only the
        # owner (or Manager) can edit their own profile.
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated()]
        if self.action in ["update", "partial_update"]:
            return [IsOwnerOrFundManager()]
        # Removing investors is reserved exclusively for the Fund Manager
        return [IsFundManager()]


class SubscriptionCreateThrottle(ScopedRateThrottle):
    scope = "subscription_create"


class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()

    def get_queryset(self):
        is_manager = getattr(self.request.user, "is_staff", False)

        if is_manager:
            return Subscription.objects.all()
        return Subscription.objects.filter(investor=self.request.user)

    serializer_class = SubscriptionSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "fund"]

    def get_throttles(self):
        """
        Apply a request limit only to the action of creating subscriptions.
        """
        if self.action == "create":
            return [SubscriptionCreateThrottle()]
        return super().get_throttles()

    def get_permissions(self):
        # Allows the investor to create their subscription
        if self.action in ["list", "retrieve", "create", "notice"]:
            return [IsAuthenticated()]
        return [IsFundManager()]

    def perform_create(self, serializer):
        """
        Eliminates the risk of identity spoofing.
            - If it is a normal investor, the 'investor' field is forced to be itself,
            ignoring any malicious IDs that have been sent in the JSON.
            - If it is a Fund Manager, the investor can be chosen freely.
        """
        if getattr(self.request.user, "is_staff", False):
            serializer.save()
        else:
            serializer.save(investor=self.request.user)

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        """
        Custom endpoint: POST /api/v1/subscriptions/{id}/approve/
        Approves the subscription and triggers the Capital Call.
        """
        subscription = self.get_object()
        updated_subscription, newly_approved = SubscriptionService.approve_subscription(
            subscription
        )
        serializer = self.get_serializer(updated_subscription)
        if newly_approved:
            msg = "Subscription approved. Email is being sent in the background."
        else:
            msg = "Subscription was already approved. No action taken."
        return Response(
            {
                "message": msg,
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], url_path="notice")
    def notice(self, request, pk=None):
        """
        Custom endpoint: GET /api/v1/subscriptions/{id}/notice/
        Generates and returns the Capital Call Notice in HTML so the investor
        can read it.
        """
        sub = self.get_object()

        context = {
            "investor_name": sub.investor.get_full_name() or sub.investor.username,
            "amount": f"{sub.amount:,.2f}",
            "fund_name": sub.fund.fund_name,
        }

        html_content = render_to_string("emails/capital_call.html", context)
        return HttpResponse(html_content)
