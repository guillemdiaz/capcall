from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import (
    Fund,
    Subscription,
)

Investor = get_user_model()


class Command(BaseCommand):
    help = "Seeds the database with initial data for CapCall testing."

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding data...")

        # Creates the Fund Manager (Superuser)
        manager, created = Investor.objects.get_or_create(
            username="manager",
            defaults={
                "email": "manager@capcall.com",
                "first_name": "Admin",
                "last_name": "Manager",
                "is_staff": True,
                "is_superuser": True,
                "investor_type": Investor.InvestorType.INSTITUTIONAL,
                "kyc_status": Investor.KycStatus.APPROVED,
                "country": "LU",
            },
        )
        if created:
            manager.set_password("test12341234")
            manager.save()

        # Creates the investors (LPs)
        inv1, created = Investor.objects.get_or_create(
            username="investor1",
            defaults={
                "email": "investor1@gmail.com",
                "first_name": "Guillem",
                "last_name": "Diaz",
                "is_staff": False,
                "investor_type": Investor.InvestorType.INDIVIDUAL,
                "kyc_status": Investor.KycStatus.APPROVED,
                "country": "ES",
            },
        )
        if created:
            inv1.set_password("test12341234")
            inv1.save()

        inv2, created = Investor.objects.get_or_create(
            username="investor2",
            defaults={
                "email": "investor2@gmail.com",
                "first_name": "Joan",
                "last_name": "Garcia",
                "is_staff": False,
                "investor_type": Investor.InvestorType.INSTITUTIONAL,
                "kyc_status": Investor.KycStatus.PENDING,
                "country": "FR",
            },
        )
        if created:
            inv2.set_password("test12341234")
            inv2.save()

        # Creates the funds
        fund1, _ = Fund.objects.get_or_create(
            fund_name="Blackstone Capital",
            defaults={
                "vintage_year": 2019,
                "fund_size": 26000000000.00,
                "currency": "USD",
                "strategy": Fund.StrategyType.BUYOUT,
                "status": Fund.StatusType.INVESTING,
                "committed_capital": 26000000000.00,
                "called_capital": 15000000000.00,
            },
        )

        fund2, _ = Fund.objects.get_or_create(
            fund_name="Tech Ventures",
            defaults={
                "vintage_year": 2024,
                "fund_size": 150000000.00,
                "currency": "EUR",
                "strategy": Fund.StrategyType.VENTURE,
                "status": Fund.StatusType.FUNDRAISING,
                "committed_capital": 85000000.00,
                "called_capital": 0.00,
            },
        )

        # Creates subscriptions
        Subscription.objects.get_or_create(
            fund=fund1,
            investor=inv2,
            defaults={"amount": 25000000.00, "status": Subscription.Status.FUNDED},
        )

        Subscription.objects.get_or_create(
            fund=fund2,
            investor=inv1,
            defaults={"amount": 250000.00, "status": Subscription.Status.APPROVED},
        )

        Subscription.objects.get_or_create(
            fund=fund2,
            investor=inv2,
            defaults={"amount": 500000.00, "status": Subscription.Status.SUBMITTED},
        )

        self.stdout.write(self.style.SUCCESS("Database seeded successfully."))
