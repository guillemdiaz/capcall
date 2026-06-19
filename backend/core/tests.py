from django.core.cache import cache
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
            is_staff=True,
        )
        cls.fund = Fund.objects.create(
            fund_name="Fundcraft Tech I",
            vintage_year=2026,
            fund_size="50000000.00",
            strategy="GROWTH",
        )
        cls.list_url = reverse("fund-list")
        cls.detail_url = reverse("fund-detail", args=[cls.fund.pk])

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
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["fund_name"], "Fundcraft Tech I")

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


class AuthorizationPermissionsTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.manager = Investor.objects.create_user(
            username="manager", password="password123", is_staff=True
        )
        cls.investor1 = Investor.objects.create_user(
            username="investor1", password="password123", investor_type="INDIVIDUAL"
        )
        cls.investor2 = Investor.objects.create_user(
            username="investor2", password="password123", investor_type="ENTITY"
        )
        cls.fund = Fund.objects.create(
            fund_name="Fundcraft Security I",
            vintage_year=2026,
            fund_size="10000000.00",
            strategy="BUYOUT",
        )
        cls.sub1 = Subscription.objects.create(
            fund=cls.fund, investor=cls.investor1, amount="50000.00"
        )
        cls.sub2 = Subscription.objects.create(
            fund=cls.fund, investor=cls.investor2, amount="75000.00"
        )
        cls.sub_list_url = reverse("subscription-list")
        cls.fund_detail_url = reverse("fund-detail", args=[cls.fund.pk])

    def test_investor_cannot_see_other_investors_subscriptions(self):
        """GET /subscriptions/ isolated by user via get_queryset"""
        self.client.force_authenticate(user=self.investor1)
        response = self.client.get(self.sub_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only receive 1 subscription (the user's own one)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["amount"], "50000.00")

    def test_fund_manager_can_see_all_subscriptions(self):
        """GET /subscriptions/ returns all records for staff users"""
        self.client.force_authenticate(user=self.manager)
        response = self.client.get(self.sub_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The manager should see the 2 subscriptions
        self.assertEqual(len(response.data["results"]), 2)

    def test_investor_cannot_approve_kyc(self):
        """PATCH /investors/<id>/ ignores read_only_fields like kyc_status"""
        self.client.force_authenticate(user=self.investor1)
        url = reverse("investor-detail", args=[self.investor1.pk])

        # The investor tries to change their own KYC to APPROVED
        response = self.client.patch(url, {"kyc_status": "APPROVED"})

        # API allows editing (200 OK) because the investor is the owner...
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # ...but ignores the field because it is read_only_fields
        self.investor1.refresh_from_db()
        self.assertEqual(self.investor1.kyc_status, "PENDING")

    def test_investor_cannot_create_subscription_for_another_investor(self):
        """POST /subscriptions/ overrides malicious investor ID with request.user"""
        self.client.force_authenticate(user=self.investor1)

        # Investor 1 tries to subscribe Investor 2 with Investor 2's money
        malicious_data = {
            "fund": "Fundcraft Security I",
            "amount": "100000.00",
            "investor": self.investor2.pk,
        }
        response = self.client.post(self.sub_list_url, malicious_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verifies the backend has intercepted the ID and assigned the subscription to
        # Investor 1
        new_sub = Subscription.objects.get(id=response.data["id"])
        self.assertEqual(new_sub.investor, self.investor1)

    def test_investor_gets_404_when_accessing_other_investor_profile(self):
        """GET /investors/<other_id>/ returns 404 due to queryset isolation"""
        self.client.force_authenticate(user=self.investor1)
        url = reverse("investor-detail", args=[self.investor2.pk])

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_investor_cannot_delete_fund(self):
        """DELETE /funds/<id>/ is blocked by IsFundManager permission"""
        self.client.force_authenticate(user=self.investor1)

        response = self.client.delete(self.fund_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SubscriptionFilteringTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.manager = Investor.objects.create_user(
            username="manager", password="password123", is_staff=True
        )
        cls.fund = Fund.objects.create(
            fund_name="Filter Fund",
            vintage_year=2024,
            fund_size="1000.00",
            strategy="BUYOUT",
        )

        cls.sub_draft = Subscription.objects.create(
            fund=cls.fund, investor=cls.manager, amount="100.00", status="DRAFT"
        )
        cls.sub_submitted = Subscription.objects.create(
            fund=cls.fund, investor=cls.manager, amount="200.00", status="SUBMITTED"
        )
        cls.url = reverse("subscription-list")

    def test_filter_subscriptions_by_status(self):
        """GET /subscriptions/?status=SUBMITTED returns only matching records"""
        self.client.force_authenticate(user=self.manager)

        response = self.client.get(f"{self.url}?status=SUBMITTED")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Checks that only 1 result is returned (ignores the DRAFT one)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["status"], "SUBMITTED")


class SecurityThrottlingTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.token_url = reverse("token_obtain_pair")

    def setUp(self):
        """
        The cache is cleared before each test so that attempts
        from other tests do not interfere with the throttling counter.
        """
        cache.clear()

    def test_login_brute_force_is_throttled(self):
        """
        Simulates a brute-force attack on the login endpoint.
        The 6th request within a minute should return 429 Too Many Requests.
        """
        # 5 login attempts (the limit set in settings.py)
        for _ in range(5):
            response = self.client.post(
                self.token_url, {"username": "admin", "password": "incorrect"}
            )
            # Confirms that there is no blocking yet
            self.assertNotEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        # On the 6th request throttling should jump
        response = self.client.post(
            self.token_url, {"username": "admin", "password": "incorrect"}
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
