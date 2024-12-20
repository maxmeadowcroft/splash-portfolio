from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from datetime import datetime, timedelta
from django.utils import timezone
import random
import stripe
import json
from .forms import CustomUserCreationForm, CustomUserUpdateForm, ProjectForm, PaymentForm
from .models import CustomUser, Skill, Project, Payment, ProjectImage
from django.contrib.auth.forms import AuthenticationForm

stripe.api_key = '1234'  # Set your Stripe secret key

# ======================== User Authentication Views ========================

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully!")
            return redirect('accounts')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'portfolio_app/signup.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "You have logged in successfully!")
            return redirect('portfolio', username=user.username)
        else:
            messages.error(request, "Invalid credentials. Please try again.")
    else:
        form = AuthenticationForm()
    return render(request, 'portfolio_app/login.html', {'form': form})

def user_logout(request):
    logout(request)
    messages.success(request, 'You have logged out successfully.')
    return redirect('login')

# ======================== Password Reset Views ========================

def forget_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email)
            otp = random.randint(100000, 999999)
            request.session['otp'] = otp
            request.session['email'] = email
            request.session['otp_expiry'] = (datetime.now() + timedelta(minutes=10)).isoformat()

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
    return render(request, 'portfolio_app/forget_password.html')

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

            request.session.pop('otp', None)
            request.session.pop('email', None)
            request.session.pop('otp_expiry', None)

            update_session_auth_hash(request, user)
            messages.success(request, "Password reset successfully! You can now log in.")
            return redirect('login')
        except CustomUser.DoesNotExist:
            messages.error(request, "Error resetting password. Please try again.")
    return render(request, 'portfolio_app/reset_password.html')

# ======================== User Profile and Accounts Views ========================

@login_required
def accounts(request):
    if request.method == 'POST':
        form = CustomUserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save()

            # Handle skills
            for skill in user.skills.all():
                skill_id = skill.id
                skill_value = request.POST.get(f'skill_{skill_id}')
                remove_skill = request.POST.get(f'remove_skill_{skill_id}')

                if remove_skill:
                    user.skills.remove(skill)
                elif skill_value and skill_value != skill.name:
                    skill.name = skill_value
                    skill.save()

            new_skill_name = form.cleaned_data.get('new_skill')
            if new_skill_name:
                new_skill, created = Skill.objects.get_or_create(name=new_skill_name.strip())
                if new_skill not in user.skills.all():
                    user.skills.add(new_skill)

            messages.success(request, "Profile updated successfully!")
            return redirect('accounts')
        else:
            messages.error(request, "Error updating profile. Please correct the errors.")
    else:
        form = CustomUserUpdateForm(instance=request.user)

    return render(request, 'accounts.html', {'form': form})

# ======================== Portfolio and Project Views ========================

@login_required
def portfolio(request, username):
    profile_user = get_object_or_404(CustomUser, username=username)
    context = {
        'profile_user': profile_user,
        'skills': profile_user.skills.all(),
        'projects': profile_user.projects.all(),
        'linkedin_url': profile_user.linkedin_url,
        'github_url': profile_user.github_url,
        'experience': profile_user.experience,
        'profile_image': profile_user.profile_image,
    }
    return render(request, 'portfolio.html', context)

@login_required
def projects(request):
    projects = Project.objects.filter(user=request.user)
    if request.method == 'POST':
        project_form = ProjectForm(request.POST, request.FILES)
        if project_form.is_valid():
            project = project_form.save(commit=False)
            project.user = request.user
            project.save()

            for img in request.FILES.getlist('images'):
                ProjectImage.objects.create(project=project, image=img)

            messages.success(request, "Project added successfully.")
            return redirect('projects')
        else:
            messages.error(request, "Failed to add project. Please check the form.")
    else:
        project_form = ProjectForm()

    return render(request, 'projects.html', {'projects': projects, 'form': project_form})

@login_required
def edit_project(request, id):
    project = get_object_or_404(Project, id=id)
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, "Project updated successfully.")
            return redirect('projects')
    else:
        form = ProjectForm(instance=project)
    return render(request, 'edit_project.html', {'form': form})

@login_required
def delete_project(request, id):
    project = get_object_or_404(Project, id=id)
    if project.user == request.user:
        project.delete()
        messages.success(request, "Project deleted successfully.")
    else:
        messages.error(request, "You don't have permission to delete this project.")
    return redirect('projects')

@login_required
def show_project(request, id):
    project = get_object_or_404(Project, id=id)
    return render(request, 'show_project.html', {'project': project, 'images': project.images.all()})

# ======================== Payment and Subscription Views ========================

def payment_view(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            try:
                payment_intent = stripe.PaymentIntent.create(
                    amount=int(amount * 100),
                    currency='usd',
                    metadata={'integration_check': 'accept_a_payment'},
                )

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

@login_required
def transaction_history(request):
    payments = Payment.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'transaction_history.html', {'payments': payments})
