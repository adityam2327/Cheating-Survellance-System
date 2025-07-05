from django.urls import path
from . import views

app_name = 'exam_sessions'

urlpatterns = [
    path('', views.session_list, name='session_list'),
    path('<int:session_id>/', views.session_detail, name='session_detail'),
    path('create/', views.create_session, name='create_session'),
    path('<int:session_id>/end/', views.end_session, name='end_session'),
    path('api/sessions/', views.SessionListAPIView.as_view(), name='session_list_api'),
    path('api/sessions/<int:pk>/', views.SessionDetailAPIView.as_view(), name='session_detail_api'),
] 