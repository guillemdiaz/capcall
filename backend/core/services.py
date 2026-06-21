import logging

from .models import Subscription
from .tasks import send_capital_call_email_task

logger = logging.getLogger(__name__)


class SubscriptionService:

    @staticmethod
    def approve_subscription(
        subscription: Subscription,
    ) -> tuple[Subscription, bool]:
        """
        Approves a subscription and triggers the Capital Call email
        to be sent asynchronously using Celery.
        """
        if subscription.status == "APPROVED":
            logger.warning(f"Subscription {subscription.pk} was already APPROVED.")
            return subscription, False

        subscription.status = "APPROVED"
        subscription.save(update_fields=["status"])

        logger.info(f"Subscription {subscription.pk} approved by the Service Layer.")

        # Dispatches the async task (Celery)
        # .delay() queues the task in Redis and returns immediately
        send_capital_call_email_task.delay(subscription.pk)

        return subscription, True
