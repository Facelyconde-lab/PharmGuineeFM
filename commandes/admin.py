from django.contrib import admin
from .models import Commande


@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "stock", "quantite", "statut", "mode_livraison", "date_creation")
    list_filter = ("statut", "mode_livraison")
    search_fields = ("patient__username", "numero_scelle")
