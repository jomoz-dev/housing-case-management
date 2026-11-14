from django.apps import AppConfig


class CasesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "cases"
    verbose_name = "Housing cases"

    def ready(self):
        from django.contrib import admin

        admin.site.site_header = "Housing Case Management"
        admin.site.site_title = "Case Management"
        admin.site.index_title = "Cases and notes"
