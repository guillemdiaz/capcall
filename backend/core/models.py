from django.contrib.auth.models import AbstractUser
from django.db import models


class Investor(AbstractUser):
    class InvestorType(models.TextChoices):
        INDIVIDUAL = "INDIVIDUAL", "Individual"
        INSTITUTIONAL = "INSTITUTIONAL", "Institutional"

    class KycStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    investor_type = models.CharField(
        max_length=20,
        choices=InvestorType,
        default=InvestorType.INDIVIDUAL,
    )
    kyc_status = models.CharField(
        max_length=20,
        choices=KycStatus,
        default=KycStatus.PENDING,
    )
    country = models.CharField(max_length=2)

    def __str__(self):
        return f"{self.first_name} {self.last_name}" or self.email


class Fund(models.Model):
    class StrategyType(models.TextChoices):
        BUYOUT = "BUYOUT", "Buyout"
        GROWTH = "GROWTH", "Growth"
        VENTURE = "VENTURE", "Venture"
        DISTRESSED = "DISTRESSED", "Distressed"

    class StatusType(models.TextChoices):
        FUNDRAISING = "FUNDRAISING", "Fundraising"
        INVESTING = "INVESTING", "Investing"
        HARVEST = "HARVEST", "Harvest"
        LIQUIDATED = "LIQUIDATED", "Liquidated"

    fund_name = models.CharField(max_length=100)
    vintage_year = models.PositiveIntegerField()
    fund_size = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default="EUR")
    strategy = models.CharField(max_length=20, choices=StrategyType)
    status = models.CharField(
        max_length=20,
        choices=StatusType,
        default=StatusType.FUNDRAISING,
    )
    committed_capital = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    called_capital = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.fund_name} ({self.vintage_year})"


class Subscription(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        FUNDED = "FUNDED", "Funded"

    fund = models.ForeignKey(
        Fund, on_delete=models.CASCADE, related_name="subscriptions"
    )
    investor = models.ForeignKey(
        Investor, on_delete=models.CASCADE, related_name="subscriptions"
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.investor} -> {self.fund.fund_name} ({self.status})"
