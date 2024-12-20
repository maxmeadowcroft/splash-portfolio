from django.utils.timezone import now
from .models import Payment

class CheckMembershipMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            payment = Payment.objects.filter(user=request.user, status='completed').order_by('-renewal_date').first()
            
            # Check if the user has a completed payment and if the renewal date has passed
            if payment and payment.renewal_date < now():
                # Update the user's premium status in the database
                request.user.is_premium = False
                request.user.save()
                
                # Refresh the request.user object to reflect changes in the session
                request.user.refresh_from_db()
                
        return self.get_response(request)
