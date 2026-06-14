from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from .models import Investor, Fund, Subscription
from rest_framework.test import APITestCase


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


class FundAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = Investor.objects.create_user(
            username="test_admin",
            email="admin@gmail.com",
            password="password123",
        )
        cls.fund = Fund.objects.create(
            fund_name="Fundcraft Tech I",
            vintage_year=2026,
            fund_size="50000000.00",
            strategy="GROWTH",
        )
        cls.list_url = reverse("fund-list")
        cls.detail_url = reverse("fund-detail", args=[cls.fund.id])

    def setUp(self):
        """
        Executes before every test and authenticates the client automatically
        by force.
        """
        self.client.force_authenticate(user=self.user)

    def test_get_all_funds(self):
        """GET /api/v1/funds/ returns a list of all funds"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["fund_name"], "Fundcraft Tech I")

    def test_get_single_fund(self):
        """GET /api/v1/funds/<int:pk>/ returns a single fund"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["fund_name"], "Fundcraft Tech I")

    def test_create_fund(self):
        """POST /api/v1/funds/ creates a new fund and returns 201"""
        data = {
            "fund_name": "Fundcraft Health II",
            "vintage_year": 2027,
            "fund_size": "20000000.00",
            "strategy": "VENTURE",
            "currency": "EUR",
            "status": "FUNDRAISING",
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_delete_fund(self):
        """DELETE /api/v1/funds/<int:pk>/ removes a fund and returns 204"""
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class JWTAuthenticationTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.investor = Investor.objects.create_user(
            username="investor1",
            email="investor@gmail.com",
            password="password123",
            investor_type="INDIVIDUAL",
            country="ES",
        )
        cls.token_url = reverse("token_obtain_pair")
        cls.list_url = reverse("fund-list")

    def test_obtain_token_with_valid_credentials(self):
        """POST /api/v1/auth/token/ returns access and refresh tokens"""
        response = self.client.post(
            self.token_url,
            {
                "username": "investor1",
                "password": "password123",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_unauthenticated_request_is_rejected(self):
        """GET /api/v1/funds/ without token returns 403"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_request_is_allowed(self):
        """GET /api/v1/funds/ with valid token returns 200"""
        token = self.client.post(
            self.token_url,
            {
                "username": "investor1",
                "password": "password123",
            },
        ).data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
