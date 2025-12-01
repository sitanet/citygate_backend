from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_verification_email(user, verification_code):
    """Send verification email to user"""
    subject = 'Verify Your CityGate Church Account'
    
    # Simple text message for now (you can create HTML template later)
    message = f"""
    Hello {user.first_name or user.username},

    Thank you for joining The CityGate Church! To complete your registration, please use this verification code:

    {verification_code}

    This code will expire in 10 minutes for security reasons.

    If you didn't create an account with us, please ignore this email.

    Blessings,
    The CityGate Church Team
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False