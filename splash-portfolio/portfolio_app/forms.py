from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Project, ProjectImage
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.forms import FileInput


# =============== Custom User Creation Form ===============
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email


# =============== Custom User Update Form ===============
from django import forms
from .models import CustomUser
from django.forms.widgets import FileInput

class CustomUserUpdateForm(forms.ModelForm):
    new_skill = forms.CharField(
        max_length=100, required=False, label="Add New Skill"
    )
    profile_image = forms.ImageField(
        required=False,
        label="Profile Image",
        widget=FileInput(attrs={
            'class': 'form-control',
            'id': 'id_profile_image',
            'accept': 'image/*',
        })
    )
    linkedin_url = forms.URLField(
        required=False,
        label="LinkedIn URL",
        widget=forms.URLInput(attrs={'class': 'form-control'})
    )
    github_url = forms.URLField(
        required=False,
        label="GitHub URL",
        widget=forms.URLInput(attrs={'class': 'form-control'})
    )
    experience = forms.CharField(
        required=False,
        label="Work Experience",
        widget=forms.TextInput(attrs={'class': 'form-control'})  # TextInput since it's short
    )

    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'first_name', 'last_name', 'introduction',
            'profile_image', 'new_skill', 'linkedin_url', 'github_url', 'experience'
        ]

    def __init__(self, *args, **kwargs):
        super(CustomUserUpdateForm, self).__init__(*args, **kwargs)
        self.fields['profile_image'].required = False  # Make profile_image optional

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and CustomUser.objects.filter(email=email).exclude(id=self.instance.id).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and CustomUser.objects.filter(username=username).exclude(id=self.instance.id).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

from django import forms
from django.forms import FileInput
from .models import Project, ProjectImage
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from django import forms
from .models import Project

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'files']  # Include all required fields
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter project title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter project description'}),
            'files': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'POST'
        self.helper.add_input(Submit('submit', 'Save Project'))

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not title.strip():  # Title cannot be empty or just whitespace
            raise forms.ValidationError("Title cannot be empty.")
        return title



class ProjectImageForm(forms.ModelForm):
    class Meta:
        model = ProjectImage
        fields = ['image']  # Only image field for uploading images

    image = forms.ImageField(
        required=False,  # Allow no images
        widget=FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )
    
    def __init__(self, *args, **kwargs):
        super(ProjectImageForm, self).__init__(*args, **kwargs)
        self.fields['image'].required = False
from django import forms

class PaymentForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label="Amount",
        widget=forms.NumberInput(attrs={"placeholder": "Enter amount"})
    )

    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        label="Payment Method",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
