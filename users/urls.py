"""
URL patterns for users app API.
"""

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    # User management
    path('users/', views.UserListCreateView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('current/', views.current_user_view, name='current-user'),
    
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('change-password/', views.change_password, name='change_password'),
] 