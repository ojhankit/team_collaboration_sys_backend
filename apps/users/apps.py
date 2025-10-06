from django.apps import AppConfig

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'   # full Python path (needed for import)
    label = 'users'       # ✅ THIS is the app_label Django will use
