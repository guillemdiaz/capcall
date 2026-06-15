from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from core.models import Fund, Subscription
from core.permissions import IsFundManager, IsOwnerOrFundManager
from core.serializers import FundSerializer, InvestorSerializer, SubscriptionSerializer


class FundViewSet(viewsets.ModelViewSet):
    queryset = Fund.objects.all()
    serializer_class = FundSerializer

    def get_permissions(self):
        # Everyone can see the funds, but only the Manager can create/edit/delete
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated()]
        return [IsFundManager()]


class InvestorViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        is_manager = getattr(self.request.user, "is_staff", False)

        if is_manager:
            return get_user_model().objects.filter(is_superuser=False)
        # An investor can only see their own profile
        return get_user_model().objects.filter(id=self.request.user.id)

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


class SubscriptionViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        is_manager = getattr(self.request.user, "is_staff", False)

        if is_manager:
            return Subscription.objects.all()
        return Subscription.objects.filter(investor=self.request.user)

    serializer_class = SubscriptionSerializer

    def get_permissions(self):
        # Allows the investor to create their subscription
        if self.action in ["list", "retrieve", "create"]:
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
