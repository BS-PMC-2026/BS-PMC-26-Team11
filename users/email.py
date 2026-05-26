from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


def send_package_cancellation_email(user, package_name):
    subject = 'ביטול הזמנה - חוות החריף'
    context = {
        'user_name': user.first_name or user.email,
        'package_name': package_name,
    }
    html_message = render_to_string('emails/package_cancelled.html', context)
    text_message = render_to_string('emails/package_cancelled.txt', context)

    send_mail(
        subject,
        text_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=False,
    )
