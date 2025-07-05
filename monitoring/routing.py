from django.urls import path
from . import consumers
from blockchain import consumers as blockchain_consumers

websocket_urlpatterns = [
    path('ws/monitoring/', consumers.MonitoringConsumer.as_asgi()),
    path('ws/blockchain/', blockchain_consumers.BlockchainConsumer.as_asgi()),
] 