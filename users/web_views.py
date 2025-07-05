"""
Web views for users app (non-API).
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import User
from .forms import UserRegistrationForm, UserProfileForm


def login_view(request):
    """User login view."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard:index')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'users/login.html', {})


@login_required
def logout_view(request):
    """User logout view."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('users:login')


class UserRegistrationView(CreateView):
    """User registration view."""
    model = User
    form_class = UserRegistrationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('users:login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Account created successfully! Please log in.')
        return response


class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    """User profile update view."""
    model = User
    form_class = UserProfileForm
    template_name = 'users/profile.html'
    success_url = reverse_lazy('users:profile')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Profile updated successfully!')
        return response


@login_required
def change_password_view(request):
    """Change password view."""
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        if not request.user.check_password(old_password):
            messages.error(request, 'Current password is incorrect.')
        elif new_password1 != new_password2:
            messages.error(request, 'New passwords do not match.')
        else:
            request.user.set_password(new_password1)
            request.user.save()
            messages.success(request, 'Password changed successfully!')
            return redirect('users:login')
    
    return render(request, 'users/change_password.html', {}) 