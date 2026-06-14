from django.contrib.auth import get_user_model
from rest_framework import viewsets

from core.models import Fund, Subscription
from core.serializers import FundSerializer, InvestorSerializer, SubscriptionSerializer


class FundViewSet(viewsets.ModelViewSet):
    queryset = Fund.objects.all()
    serializer_class = FundSerializer


class InvestorViewSet(viewsets.ModelViewSet):
    queryset = get_user_model().objects.filter(is_superuser=False)
    serializer_class = InvestorSerializer


class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
