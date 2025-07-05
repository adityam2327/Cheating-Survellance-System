from django.apps import AppConfig


class BlockchainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blockchain'

    def ready(self):
        from blockchain_logger import initialize_blockchain_logger
        initialize_blockchain_logger() 