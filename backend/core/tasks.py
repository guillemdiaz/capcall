import logging
import time

from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string

from config import settings
from core.models import Subscription

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def send_capital_call_email_task(self, subscription_id):
    logger.info(f"Starting email sending task for subscription {subscription_id}...")
    try:
        sub = Subscription.objects.get(id=subscription_id)
        time.sleep(3)

        # Prepares the data that the template will need
        context = {
            "investor_name": sub.investor.get_full_name() or sub.investor.username,
            "amount": f"{sub.amount:,.2f}",
            "fund_name": sub.fund.fund_name,
        }

        # Loads the text from the template files
        text_content = render_to_string("emails/capital_call.txt", context)
        html_content = render_to_string("emails/capital_call.html", context)

        subject = f"Action Required: Capital Call for fund {sub.fund.fund_name}"

        send_mail(
            subject=subject,
            message=text_content,
            html_message=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[sub.investor.email],
            fail_silently=False,
        )

        logger.info(f"Email sent successfully to investor {sub.investor.username}.")
        return True
    except Subscription.DoesNotExist:
        logger.error(f"Subscription {subscription_id} does not exist. Canceling task.")
        return False
