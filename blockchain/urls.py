from django.urls import path
from .views import (
    BlockchainLogsAPIView, 
    BlockchainLogsView, 
    BlockchainAddEventView,
    BlockchainDashboardView,
    BlockchainAPIView,
    BlockExplorerView
)

app_name = 'blockchain'

urlpatterns = [
    path('', BlockchainDashboardView.as_view(), name='blockchain-dashboard'),
    path('logs/', BlockchainLogsAPIView.as_view(), name='blockchain-logs'),
    path('logs/html/', BlockchainLogsView.as_view(), name='blockchain-logs-html'),
    path('add/', BlockchainAddEventView.as_view(), name='blockchain-add-event'),
    path('api/', BlockchainAPIView.as_view(), name='blockchain-api'),
    path('blocks/', BlockExplorerView.as_view(), name='block-explorer'),
] 