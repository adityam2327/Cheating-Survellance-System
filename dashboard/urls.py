from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('data/', views.dashboard_data, name='data'),
    path('real-time-stats/', views.real_time_stats, name='real_time_stats'),
    path('monitoring/', views.start_monitoring, name='monitoring'),
    path('analytics/', views.analytics_view, name='analytics'),
] 