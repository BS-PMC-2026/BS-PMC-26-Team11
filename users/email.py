from django.core.mail import send_mail
from django.conf import settings


def send_order_success_email(user):
    subject = "הזמנה בוצעה בהצלחה"
    message = (
        f"שלום {user.full_name},\n\n"
        "ההזמנה שלך בוצעה בהצלחה.\n"
        "תודה שבחרת בהדינרים."
    )

    recipients = [user.email, settings.ADMIN_EMAIL]

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        recipients,
        fail_silently=False,
    )


def send_package_cancellation_email(user, package_name):
    subject = "ביטול הזמנה"
    message = (
        f"שלום {user.full_name},\n\n"
        f'ההזמנה עבור "{package_name}" בוטלה בהצלחה.\n'
        "תודה."
    )

    recipients = [user.email, settings.ADMIN_EMAIL]

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        recipients,
        fail_silently=False,
    )