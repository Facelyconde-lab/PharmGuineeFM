from django.contrib import admin
from .models import VisiteRecherche


@admin.register(VisiteRecherche)
class VisiteRechercheAdmin(admin.ModelAdmin):
    list_display = ("date_creation", "patient", "session_key")
    list_filter = ("date_creation",)
    search_fields = ("patient__username", "session_key")
