from django.conf import settings
from django.core.mail import send_mail
import random

def send_otp(email):
    otp = str(random.randint(100000, 999999))
    
    # Send email
    send_mail(
        subject="SkillLink Registration OTP",
        message=f"Your OTP for SkillLink registration is: {otp}",
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False,
    )
    return otp

