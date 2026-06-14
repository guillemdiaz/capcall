from django.test import TestCase
from .models import Investor, Fund, Subscription


class CoreDomainTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.investor = Investor.objects.create_user(
            username="investor1",
            email="investor@gmail.com",
            password="password123",
            investor_type="INDIVIDUAL",
            country="ES",
        )

        cls.fund = Fund.objects.create(
            fund_name="Fundcraft Tech I",
            vintage_year=2026,
            fund_size=50000000.00,
            strategy="GROWTH",
        )

        cls.subscription = Subscription.objects.create(
            fund=cls.fund, investor=cls.investor, amount=1000000.00
        )

    def test_investor_kyc_default_status(self):
        """A new investor must always be born with KYC pending"""
        self.assertEqual(self.investor.kyc_status, "PENDING")

    def test_subscription_initial_state(self):
        """According to business rules, every subscription starts in DRAFT"""
        self.assertEqual(self.subscription.status, "DRAFT")
        self.assertEqual(self.subscription.fund, self.fund)
        self.assertEqual(self.subscription.investor, self.investor)

    def test_model_string_representations(self):
        """Ensures that admin and logs display readable info"""
        self.assertEqual(str(self.fund), "Fundcraft Tech I (2026)")
        self.assertIn("Fundcraft Tech I", str(self.subscription))
        self.assertIn("DRAFT", str(self.subscription))
