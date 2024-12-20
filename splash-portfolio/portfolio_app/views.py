from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from datetime import datetime, timedelta
import random
import stripe
import uuid
from .forms import CustomUserCreationForm, CustomUserUpdateForm, ProjectForm, PaymentForm
from .models import CustomUser, Skill, Project, Payment, ProjectImage
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
import json
# Set your Stripe secret key
stripe.api_key = settings.STRIPE_SECRET_KEY

# =============== User Signup View ===============
def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Save the user to the database
            login(request, user)  # Automatically log the user in
            messages.success(request, "Account created successfully!")
            return redirect('accounts')  # Redirect to the accounts page after signup
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'portfolio_app/signup.html', {'form': form})

# =============== User Login View ===============
def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()  # Get the user directly from the form
            login(request, user)  # Log the user in
            messages.success(request, "You have logged in successfully!")
            return redirect('accounts')  # Redirect to the accounts page after login
        else:
            messages.error(request, "Invalid credentials. Please try again.")
    else:
        form = AuthenticationForm()
    return render(request, 'portfolio_app/login.html', {'form': form})

# =============== Forget Password View ===============
def forget_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email)
            otp = random.randint(100000, 999999)  # Generate 6-digit OTP
            request.session['otp'] = otp
            request.session['email'] = email
            request.session['otp_expiry'] = (datetime.now() + timedelta(minutes=10)).isoformat()  # Set expiry

            send_mail(
                'Your Password Reset OTP',
                f'Your OTP for password reset is {otp}. It is valid for 10 minutes.',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
            messages.success(request, f"An OTP has been sent to {email}.")
            return redirect('verify_otp')
        except CustomUser.DoesNotExist:
            messages.error(request, "No user found with this email address.")
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            print(e)
    return render(request, 'portfolio_app/forget_password.html')

# =============== Verify OTP View ===============
def verify_otp(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        session_otp = request.session.get('otp')
        otp_expiry = request.session.get('otp_expiry')

        if not otp_expiry or datetime.fromisoformat(otp_expiry) < datetime.now():
            messages.error(request, "OTP has expired. Please request a new one.")
            return redirect('forget_password')

        if str(session_otp) == entered_otp:
            messages.success(request, "OTP verified successfully!")
            return redirect('reset_password')
        else:
            messages.error(request, "Invalid OTP. Please try again.")
    return render(request, 'portfolio_app/verify_otp.html')

# =============== Reset Password View ===============
def reset_password(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, "Passwords do not match. Please try again.")
            return redirect('reset_password')

        email = request.session.get('email')
        if not email:
            messages.error(request, "Session expired. Please start over.")
            return redirect('forget_password')

        try:
            user = CustomUser.objects.get(email=email)
            if user.check_password(password):
                messages.error(request, "You cannot use your current password as the new password.")
                return redirect('reset_password')

            user.set_password(password)
            user.save()

            # Clear session data
            request.session.pop('otp', None)
            request.session.pop('email', None)
            request.session.pop('otp_expiry', None)

            update_session_auth_hash(request, user)
            messages.success(request, "Password reset successfully! You can now log in.")
            return redirect('login')
        except CustomUser.DoesNotExist:
            messages.error(request, "Error resetting password. Please try again.")
    return render(request, 'portfolio_app/reset_password.html')

# =============== Accounts View ===============
@login_required
def accounts(request):
    if request.method == 'POST':
        form = CustomUserUpdateForm(request.POST, request.FILES, instance=request.user)
        
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            # Handle existing skills: update or remove
            for skill in user.skills.all():
                skill_id = skill.id
                skill_value = request.POST.get(f'skill_{skill_id}')
                remove_skill = request.POST.get(f'remove_skill_{skill_id}')

                if remove_skill:  # Ensure `remove_skill` is properly set
                    user.skills.remove(skill)  # Remove the skill from the user's skills
                else:
                    if skill_value and skill_value != skill.name:  # If skill name has changed
                        skill.name = skill_value
                        skill.save()

            # Handle new skill addition
            new_skill_name = form.cleaned_data.get('new_skill')
            if new_skill_name:
                new_skill_name = new_skill_name.strip()  # Ensure no leading/trailing spaces
                # Check for duplicate skills before adding
                new_skill, created = Skill.objects.get_or_create(name=new_skill_name)
                if new_skill not in user.skills.all():
                    user.skills.add(new_skill)

            messages.success(request, "Profile updated successfully!")
            return redirect('accounts')  # Redirect to the same page after success
        else:
            messages.error(request, "Error updating profile. Please correct the errors.")
    else:
        form = CustomUserUpdateForm(instance=request.user)

    return render(request, 'accounts.html', {'form': form})
# =============== Logout View ===============
def user_logout(request):
    logout(request)
    messages.success(request, 'You have logged out successfully.')
    return redirect('login')
# Portfolio View
@login_required
def portfolio(request):
    # Fetch logged-in user and related data
    user = request.user
    skills = user.skills.all()
    projects = user.projects.all()
    linkedin_url = user.linkedin_url
    github_url = user.github_url
    experience = user.experience
    signup_year = user.signup_year

    context = {
        'user': user,
        'skills': skills,
        'projects': projects,
        'linkedin_url': linkedin_url,
        'github_url': github_url,
        'experience': experience,
        'signup_year': signup_year,
    }
    return render(request, 'portfolio.html', context)
@login_required
def projects(request):
    projects = Project.objects.filter(user=request.user)

    if request.method == 'POST':
        project_form = ProjectForm(request.POST, request.FILES)
        if project_form.is_valid():
            try:
                project = project_form.save(commit=False)
                project.user = request.user
                project.save()

                # Handle multiple images
                images = request.FILES.getlist('images')
                for img in images:
                    ProjectImage.objects.create(project=project, image=img)

                messages.success(request, "Project added successfully.")
                return redirect('projects')
            except ValidationError as e:
                messages.error(request, e.message)
        else:
            messages.error(request, "Failed to add project. Please check the form.")
    else:
        project_form = ProjectForm()

    return render(request, 'projects.html', {'projects': projects, 'form': project_form})
# Edit Project View
@login_required
def edit_project(request, id):
    project = get_object_or_404(Project, id=id)
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            form.save()
            return redirect('projects')  # Redirect to projects list after saving
    else:
        form = ProjectForm(instance=project)
    return render(request, 'edit_project.html', {'form': form})
# Delete Project View
@login_required
def delete_project(request, id):
    project = get_object_or_404(Project, id=id)
    if project.user == request.user:  # Only the project owner can delete it
        project.delete()
        messages.success(request, "Project deleted successfully.")
    else:
        messages.error(request, "You don't have permission to delete this project.")
    return redirect('projects')

def show_project(request, id):
    # Fetch the project by its ID
    project = get_object_or_404(Project, id=id)

    # Add the project and its associated images to the context
    context = {
        'project': project,
        'images': project.images.all(),  # Get all associated images for the project
    }

    # Render the project details page
    return render(request, 'show_project.html', context)
# =============== User Signup View ===============
def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Save the user to the database
            login(request, user)  # Automatically log the user in
            messages.success(request, "Account created successfully!")
            return redirect('accounts')  # Redirect to the accounts page after signup
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'portfolio_app/signup.html', {'form': form})
# =============== User Login View ===============
def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()  # Get the user directly from the form
            login(request, user)  # Log the user in
            messages.success(request, "You have logged in successfully!")
            
            # Ensure user.username is available
            return redirect('portfolio', username=user.username)  # Redirect to the portfolio page after login
        else:
            messages.error(request, "Invalid credentials. Please try again.")
    else:
        form = AuthenticationForm()
    return render(request, 'portfolio_app/login.html', {'form': form})

# =============== Forget Password View ===============
def forget_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email)
            otp = random.randint(100000, 999999)  # Generate 6-digit OTP
            request.session['otp'] = otp
            request.session['email'] = email
            request.session['otp_expiry'] = (datetime.now() + timedelta(minutes=10)).isoformat()  # Set expiry

            send_mail(
                'Your Password Reset OTP',
                f'Your OTP for password reset is {otp}. It is valid for 10 minutes.',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
            messages.success(request, f"An OTP has been sent to {email}.")
            return redirect('verify_otp')
        except CustomUser.DoesNotExist:
            messages.error(request, "No user found with this email address.")
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            print(e)
    return render(request, 'portfolio_app/forget_password.html')

# =============== Verify OTP View ===============
def verify_otp(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        session_otp = request.session.get('otp')
        otp_expiry = request.session.get('otp_expiry')

        if not otp_expiry or datetime.fromisoformat(otp_expiry) < datetime.now():
            messages.error(request, "OTP has expired. Please request a new one.")
            return redirect('forget_password')

        if str(session_otp) == entered_otp:
            messages.success(request, "OTP verified successfully!")
            return redirect('reset_password')
        else:
            messages.error(request, "Invalid OTP. Please try again.")
    return render(request, 'portfolio_app/verify_otp.html')

# =============== Reset Password View ===============
def reset_password(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, "Passwords do not match. Please try again.")
            return redirect('reset_password')

        email = request.session.get('email')
        if not email:
            messages.error(request, "Session expired. Please start over.")
            return redirect('forget_password')

        try:
            user = CustomUser.objects.get(email=email)
            if user.check_password(password):
                messages.error(request, "You cannot use your current password as the new password.")
                return redirect('reset_password')

            user.set_password(password)
            user.save()

            # Clear session data
            request.session.pop('otp', None)
            request.session.pop('email', None)
            request.session.pop('otp_expiry', None)
            update_session_auth_hash(request, user)
            messages.success(request, "Password reset successfully! You can now log in.")
            return redirect('login')
        except CustomUser.DoesNotExist:
            messages.error(request, "Error resetting password. Please try again.")
    return render(request, 'portfolio_app/reset_password.html')

# =============== Accounts View ===============
@login_required
def accounts(request):
    if request.method == 'POST':
        form = CustomUserUpdateForm(request.POST, request.FILES, instance=request.user)
        
        if form.is_valid():
            user = form.save(commit=False)
            user.save()

            # Handle existing skills: update or remove
            for skill in user.skills.all():
                skill_id = skill.id
                skill_value = request.POST.get(f'skill_{skill_id}')
                remove_skill = request.POST.get(f'remove_skill_{skill_id}')

                if remove_skill:  # Ensure `remove_skill` is properly set
                    user.skills.remove(skill)  # Remove the skill from the user's skills
                else:
                    if skill_value and skill_value != skill.name:  # If skill name has changed
                        skill.name = skill_value
                        skill.save()

            # Handle new skill addition
            new_skill_name = form.cleaned_data.get('new_skill')
            if new_skill_name:
                new_skill_name = new_skill_name.strip()  # Ensure no leading/trailing spaces
                # Check for duplicate skills before adding
                new_skill, created = Skill.objects.get_or_create(name=new_skill_name)
                if new_skill not in user.skills.all():
                    user.skills.add(new_skill)

            messages.success(request, "Profile updated successfully!")
            return redirect('accounts')  # Redirect to the same page after success
        else:
            messages.error(request, "Error updating profile. Please correct the errors.")
    else:
        form = CustomUserUpdateForm(instance=request.user)

    return render(request, 'accounts.html', {'form': form})

# =============== Logout View ===============
def user_logout(request):
    logout(request)
    messages.success(request, 'You have logged out successfully.')
    return redirect('login')
from django.contrib.auth.decorators import login_required

def portfolio(request, username):
    # Fetch the profile user based on the username parameter
    profile_user = get_object_or_404(CustomUser, username=username)
    skills = profile_user.skills.all()
    projects = profile_user.projects.all()
    linkedin_url = profile_user.linkedin_url
    github_url = profile_user.github_url
    experience = profile_user.experience
    signup_year = profile_user.signup_year
    profile_image=profile_user.profile_image

    context = {
        'profile_user': profile_user,  # Use a different key
        'skills': skills,
        'projects': projects,
        'linkedin_url': linkedin_url,
        'github_url': github_url,
        'experience': experience,
        'signup_year': signup_year,
        'profile_image':profile_image,
    }
    return render(request, 'portfolio.html', context)


@login_required
def projects(request):
    projects = Project.objects.filter(user=request.user)
    project_limit = 3  # Maximum number of free projects
    show_upgrade_popup = False

    # Check if user exceeds project limit
    if not request.user.is_premium and projects.count() >= project_limit:
        show_upgrade_popup = True

    if request.method == 'POST':
        project_form = ProjectForm(request.POST, request.FILES)
        if project_form.is_valid():
            if not request.user.is_premium and projects.count() >= project_limit:
                show_upgrade_popup = True
                return JsonResponse({'show_upgrade_popup': show_upgrade_popup})

            project = project_form.save(commit=False)
            project.user = request.user
            project.save()

            # Save multiple images
            for img in request.FILES.getlist('images'):
                ProjectImage.objects.create(project=project, image=img)

            return JsonResponse({'show_upgrade_popup': False})
        else:
            return JsonResponse({'show_upgrade_popup': show_upgrade_popup})
    else:
        project_form = ProjectForm()

    return render(request, 'projects.html', {
        'projects': projects,
        'form': project_form,
        'show_upgrade_popup': show_upgrade_popup,
    })
# Edit Project View
@login_required
def edit_project(request, id):
    project = get_object_or_404(Project, id=id)
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            form.save()
            return redirect('projects')  # Redirect to projects list after saving
    else:
        form = ProjectForm(instance=project)
    return render(request, 'edit_project.html', {'form': form})

# Delete Project View
@login_required
def delete_project(request, id):
    project = get_object_or_404(Project, id=id)
    if project.user == request.user:  # Only the project owner can delete it
        project.delete()
        messages.success(request, "Project deleted successfully.")
    else:
        messages.error(request, "You don't have permission to delete this project.")
    return redirect('projects')

def show_project(request, id):
    # Fetch the project by its ID
    project = get_object_or_404(Project, id=id)

    # Add the project and its associated images to the context
    context = {
        'project': project,
        'images': project.images.all(),  # Get all associated images for the project
    }

    # Render the project details page
    return render(request, 'show_project.html', context)
# Payment view to display the form and process payments
def payment_view(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            # Get the amount from the form
            amount = form.cleaned_data['amount']

            # Create a Stripe PaymentIntent
            try:
                # Create a PaymentIntent with the amount in cents
                payment_intent = stripe.PaymentIntent.create(
                    amount=int(amount * 100),  # Amount in cents
                    currency='usd',  # Currency
                    metadata={'integration_check': 'accept_a_payment'},
                )

                # Create a new payment record in the database
                payment = Payment.objects.create(
                    user=request.user,
                    amount=amount,
                    transaction_id=payment_intent.id,
                    status='pending'
                )

                return render(request, 'payment_confirmation.html', {
                    'client_secret': payment_intent.client_secret,
                    'payment_id': payment.id
                })

            except stripe.error.StripeError as e:
                messages.error(request, f"Stripe error: {e.user_message}")
                return redirect('payment')
            except Exception as e:
                messages.error(request, f"An unexpected error occurred: {str(e)}")
                return redirect('payment')

    else:
        form = PaymentForm()

    return render(request, 'payment.html', {'form': form})

def process_payment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            payment_method_id = data.get('payment_method_id')
            payment_id = data.get('payment_id')  # Get the payment ID from the request body

            # Check if payment_id is empty
            if not payment_id:
                return JsonResponse({'error': 'Payment ID is required'}, status=400)

            # Try to retrieve the payment object using the payment_id
            payment = Payment.objects.get(id=payment_id)  # Assuming `id` is a valid field

            if payment.status == 'completed':
                return JsonResponse({'error': 'Payment already completed'}, status=400)

            # Confirm the payment using the payment method ID
            payment_intent = stripe.PaymentIntent.confirm(
                payment.transaction_id,
                payment_method=payment_method_id
            )

            if payment_intent.status == 'succeeded':
                payment.status = 'completed'
                payment.save()

                return JsonResponse({'paymentIntent': payment_intent}, status=200)

            return JsonResponse({'error': 'Payment failed'}, status=400)

        except Payment.DoesNotExist:
            return JsonResponse({'error': 'Invalid payment ID'}, status=400)

        except stripe.error.StripeError as e:
            return JsonResponse({'error': f"Stripe error: {e.user_message}"}, status=400)

        except Exception as e:
            return JsonResponse({'error': f"An unexpected error occurred: {str(e)}"}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

def confirm_payment(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        payment_method_id = data.get('payment_method_id')
        payment_id = data.get('payment_id')

        try:
            payment = Payment.objects.get(id=payment_id)

            if payment.status == 'completed':
                return JsonResponse({'error': 'Payment already completed'}, status=400)

            # Confirm the payment using the payment method ID
            payment_intent = stripe.PaymentIntent.confirm(
                payment.transaction_id,
                payment_method=payment_method_id
            )

            if payment_intent.status == 'succeeded':
                payment.status = 'completed'
                payment.save()

                return JsonResponse({'paymentIntent': payment_intent}, status=200)

            return JsonResponse({'error': 'Payment failed'}, status=400)

        except Payment.DoesNotExist:
            return JsonResponse({'error': 'Invalid payment'}, status=400)

        except stripe.error.StripeError as e:
            return JsonResponse({'error': f"Stripe error: {e.user_message}"}, status=400)

        except Exception as e:
            return JsonResponse({'error': f"An unexpected error occurred: {str(e)}"}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def subscribe_to_premium(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            payment_method_id = data.get('payment_method_id')
            payment_method = data.get('payment_method')

            if not payment_method_id:
                messages.error(request, 'No payment method provided')
                return JsonResponse({'error': 'No payment method provided'}, status=400)

            if payment_method == 'card':
                # Create a Stripe Customer and attach the payment method
                customer = stripe.Customer.create(
                    payment_method=payment_method_id,
                    email=request.user.email,
                    invoice_settings={'default_payment_method': payment_method_id},
                )

                # Create the subscription for the customer
                subscription = stripe.Subscription.create(
                    customer=customer.id,
                    items=[{'price': 'price_1QRHrHBopiD2AhCIiVEp1VrM'}],  # Replace with your actual price ID
                    expand=['latest_invoice.payment_intent'],
                )

                payment_intent = subscription.latest_invoice.payment_intent

                # Extract card details directly from payment_method
                payment_method_obj = stripe.PaymentMethod.retrieve(payment_method_id)
                card_details = payment_method_obj.card

                if payment_intent.status == 'succeeded':
                    # Payment was successful
                    payment = Payment.objects.create(
                        user=request.user,
                        amount=2.00,  # For $2 per month subscription
                        transaction_id=subscription.id,
                        status='completed',
                        renewal_date=timezone.now() + timezone.timedelta(days=30),
                        card_last4=card_details['last4'],
                        card_type=card_details['brand'],
                    )

                    # Mark user as premium
                    user_profile = CustomUser.objects.get(id=request.user.id)
                    user_profile.is_premium = True
                    user_profile.save()

                    messages.success(request, 'Subscription successful!')
                    return JsonResponse({'status': 'success', 'subscription': subscription}, status=200)
                elif payment_intent.status == 'canceled':
                    messages.error(request, 'Payment canceled by user')
                    return JsonResponse({'error': 'Payment canceled by user'}, status=400)
                else:
                    messages.error(request, 'Payment failed')
                    return JsonResponse({'error': 'Payment failed'}, status=400)

            elif payment_method == 'paypal':
                # Handle PayPal integration here
                pass

        except stripe.error.StripeError as e:
            messages.error(request, f"Stripe error: {e.user_message}")
            return JsonResponse({'error': f"Stripe error: {e.user_message}"}, status=400)
        except Exception as e:
            messages.error(request, f"Unexpected error: {str(e)}")
            return JsonResponse({'error': f"Unexpected error: {str(e)}"}, status=500)

    return render(request, 'premium_subscription.html')

@login_required
def transaction_history(request):
    # Print the currently logged-in user for debugging
    payments = Payment.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'transaction_history.html', {'payments': payments})
def contact(request, username):
    # Handle the username here, e.g., get the user object
    profile_user = get_object_or_404(CustomUser, username=username)
    return render(request, 'contact.html', {'profile_user': profile_user})
