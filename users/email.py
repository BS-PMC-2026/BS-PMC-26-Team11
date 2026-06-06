from django.core.mail import send_mail
from django.conf import settings


def send_order_success_email(user, paid_items):
    subject = "הזמנה בוצעה בהצלחה"
    message = (
        f"שלום {user.full_name},\n\n"
        "ההזמנה שלך בוצעה בהצלחה.\n\n"
        "איך מתחילים את הסיור?\n"
        "1. נכנסים לקישור האתר שלנו https://hadinarim.azurewebsites.net/.\n"
        "3.מתחברים לחשבון שלכם.\n"
        "4. לוחצים בתפריט העליון על 'התחל סיור'.\n"
        "5. מזינים את קוד הגישה שנשלח אליכם במייל זה.\n"    
        "6. לאחר האישור ניתן לסרוק QR בחווה ולקבל מידע על האזור או החבילה.\n\n"
    )
    message += "\nקודי הגישה שלכם:\n\n"

    for item in paid_items:
        message += (
            f"📦 {item.package_name}\n"
            f"🔑 קוד גישה: {item.tour_access_code}\n\n"
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