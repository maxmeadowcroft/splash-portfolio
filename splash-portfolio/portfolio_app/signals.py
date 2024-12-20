from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils.timezone import now
from .models import Payment

@receiver(user_logged_in)
def check_membership_on_login(sender, request, user, **kwargs):
    payment = Payment.objects.filter(user=user, status='completed').order_by('-renewal_date').first()
    if payment and payment.renewal_date < now():
        user.is_premium = False
        user.save()
