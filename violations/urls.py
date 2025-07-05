from django.urls import path
from . import views

app_name = 'violations'

urlpatterns = [
    path('', views.violation_list, name='violation_list'),
    path('<int:violation_id>/', views.violation_detail, name='violation_detail'),
] 