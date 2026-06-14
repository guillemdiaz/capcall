from django.contrib.auth import get_user_model
from rest_framework import serializers

from core.models import Fund, Subscription

Investor = get_user_model()


class FundSerializer(serializers.ModelSerializer):

    class Meta:
        fields = (
            "id",
            "fund_name",
            "vintage_year",
            "fund_size",
            "currency",
            "strategy",
            "status",
            "committed_capital",
            "called_capital",
        )
        model = Fund
        read_only_fields = ("committed_capital", "called_capital")


class InvestorSerializer(serializers.ModelSerializer):

    class Meta:
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "investor_type",
            "kyc_status",
            "country",
        )
        model = Investor
        read_only_fields = "kyc_status"


class SubscriptionSerializer(serializers.ModelSerializer):
    fund = serializers.SlugRelatedField(
        queryset=Fund.objects.all(), slug_field="fund_name"
    )
    # Read field
    investor_name = serializers.StringRelatedField(source="investor", read_only=True)

    # Write field (accepts id in POST)
    investor = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all()
    )

    class Meta:
        fields = (
            "id",
            "fund",
            "investor",
            "investor_name",
            "amount",
            "status",
            "created_at",
            "updated_at",
        )
        model = Subscription
        read_only_fields = ("created_at", "updated_at")
