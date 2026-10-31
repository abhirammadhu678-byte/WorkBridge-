from django import forms
from .models import Customer
from accounts.models import CustomUser
from accounts.validators import validate_mobile_number


class CustomerRegistrationForm(forms.ModelForm):
    full_name = forms.CharField(required=True, label="Full Name / Company Name", widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Full Name'}))
    email = forms.EmailField(required=True, label="Email Address", widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'employer@example.com'}))
    mobile_number = forms.CharField(required=False, label="Phone Number", widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': '10-digit mobile'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Min 6 characters'}), required=True, min_length=6)
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Confirm password'}), required=True, min_length=6)

    class Meta:
        model = Customer
        fields = [
            'full_name',
            'email',
            'mobile_number',
            'address',
            'password'
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2, 'class': 'form-textarea', 'placeholder': 'Business or office address'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if CustomUser.objects.filter(username=email).exists() or CustomUser.objects.filter(email=email).exists() or Customer.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

    def clean_mobile_number(self):
        mobile = self.cleaned_data.get('mobile_number', '').strip()
        if mobile:
            return validate_mobile_number(mobile)
        return mobile

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")

        if password and len(password) < 6:
            raise forms.ValidationError("Password must be at least 6 characters long.")

        return cleaned_data