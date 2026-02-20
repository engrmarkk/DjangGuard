from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

# from django.core.mail import send_mail
from .models import UserLoginRecord
from api_services.logger import logger


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


@receiver(user_logged_in)
def track_and_alert_login(sender, request, user, **kwargs):
    logger.info("Signal user_logged_in")
    current_ip = get_client_ip(request)
    user_agent = request.META.get("HTTP_USER_AGENT", "unknown")

    # Check if this IP has been used by this user before
    is_known_ip = UserLoginRecord.objects.filter(
        user=user, ip_address=current_ip
    ).exists()
    logger.info(
        f"User {user.username} logged in from IP {current_ip}. Is known IP: {is_known_ip}"
    )

    # if not is_known_ip:
    #     # 1. Send Security Alert Email
    #     send_mail(
    #         subject="Security Alert: New Login to your Account",
    #         message=f"Hi {user.username}, we detected a login from a new IP: {current_ip}.",
    #         from_email="security@yourdomain.com",
    #         recipient_list=[user.email],
    #         fail_silently=False,
    #     )

    # 2. Record this login
    UserLoginRecord.objects.create(
        user=user, ip_address=current_ip, user_agent=user_agent
    )
    logger.info("Saved the login record")
