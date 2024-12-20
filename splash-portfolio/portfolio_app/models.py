from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.timezone import now
from django.core.validators import EmailValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
import random
import datetime
from django.conf import settings



# Skill Model
class Skill(models.Model):
    name = models.CharField(max_length=250, unique=True)

    def __str__(self):
        return self.name


# Custom User Manager
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


# Custom User
class CustomUser(AbstractUser):
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(unique=True, validators=[EmailValidator(message="Enter a valid email address.")])
    skills = models.ManyToManyField('Skill', blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True, default='profile_images/default_profile.jpg')
    introduction = models.CharField(max_length=500, null=True, blank=True)
    is_premium = models.BooleanField(default=False)
    linkedin_url = models.URLField(null=True, blank=True)
    github_url = models.URLField(null=True, blank=True)
    experience = models.CharField(max_length=10, null=True, blank=True)
    signup_year = models.PositiveIntegerField(
        default=datetime.datetime.now().year,
        validators=[
            MinValueValidator(2000),
            MaxValueValidator(datetime.datetime.now().year)
        ]
    )
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    REQUIRED_FIELDS = ['first_name', 'last_name']
    USERNAME_FIELD = 'email'
    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        if not self.username:
            random_numbers = ''.join([str(random.randint(0, 9)) for _ in range(4)])
            self.username = f'{self.first_name.lower()}{self.last_name.lower()}{random_numbers}'
        super(CustomUser, self).save(*args, **kwargs)

    def __str__(self):
        return self.email


# Project Model
class Project(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)
    files = models.FileField(upload_to='project_files/', null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.id:  # Only for new projects
            projects_count = Project.objects.filter(user=self.user).count()
            if not self.user.is_premium and projects_count >= 3:
                raise ValidationError("You can only upload up to 3 projects in the free version.")
        super(Project, self).save(*args, **kwargs)

    def __str__(self):
        return self.title


# ProjectImage Model
class ProjectImage(models.Model):
    project = models.ForeignKey(Project, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='project_images/')

    def __str__(self):
        return f"Image for {self.project.title}"


# Payment Model
class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    renewal_date = models.DateTimeField(default=now)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ])
    card_last4 = models.CharField(max_length=4, blank=True, null=True)
    card_type = models.CharField(max_length=50, blank=True, null=True)
    payment_method_id = models.CharField(max_length=100, blank=True, null=True)

    def is_expired(self):
        return self.renewal_date < now()

    def __str__(self):
        return f"Payment {self.transaction_id} - {self.status}"

    def update_user_membership(self):
        """Update the user's premium status based on payment expiration."""
        latest_payment = Payment.objects.filter(user=self.user).order_by('-renewal_date').first()

        if latest_payment and latest_payment.is_expired():
            self.user.is_premium = False
        else:
            self.user.is_premium = True

        self.user.save()
