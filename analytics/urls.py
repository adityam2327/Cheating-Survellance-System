from django.urls import path
from .views import violations_per_type, violations_per_user, violations_over_time

app_name = 'analytics'

urlpatterns = [
    path('violations/type/', violations_per_type, name='violations-per-type'),
    path('violations/user/', violations_per_user, name='violations-per-user'),
    path('violations/time/', violations_over_time, name='violations-over-time'),
] 