from django.conf import settings
from django.core.mail import send_mail

send_mail(
    subject="SkillLink Registration OTP",
    message=f"Your OTP for SkillLink registration is: {otp}",
    from_email=settings.EMAIL_HOST_USER,  # safer than hardcoding
    recipient_list=[email],
    fail_silently=False,
)
