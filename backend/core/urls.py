from django.urls import path, include
from rest_framework.routers import DefaultRouter

from core.views import FundViewSet, SubscriptionViewSet, InvestorViewSet

router = DefaultRouter()
router.register("funds", FundViewSet, basename="fund")
router.register("subscriptions", SubscriptionViewSet, basename="subscription")
router.register("investors", InvestorViewSet, basename="investor")

urlpatterns = [
    path("", include(router.urls)),
]
