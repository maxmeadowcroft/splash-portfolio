from django.apps import AppConfig


class PortfolioAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'portfolio_app'

def ready(self):
    import portfolio_app.signals