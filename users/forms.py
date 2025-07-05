 """
Forms for users app.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.password_validation import validate_password
from .models import User


class UserRegistrationForm(UserCreationForm):
    """Form for user registration."""
    
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    role = forms.ChoiceField(choices=User.Role.choices, initial=User.Role.STUDENT)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 
                 'phone_number', 'department', 'student_id', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already in use.')
        return email


class UserProfileForm(forms.ModelForm):
    """Form for updating user profile."""
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number', 
                 'department', 'student_id')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This email address is already in use.')
        return email


class PasswordChangeForm(forms.Form):
    """Form for changing password."""
    
    old_password = forms.CharField(widget=forms.PasswordInput())
    new_password1 = forms.CharField(widget=forms.PasswordInput(), validators=[validate_password])
    new_password2 = forms.CharField(widget=forms.PasswordInput())
    
    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        
        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError('New passwords do not match.')
        
        return cleaned_data