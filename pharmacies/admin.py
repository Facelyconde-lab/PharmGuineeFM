from django.contrib import admin
from .models import Pharmacie, Stock


@admin.register(Pharmacie)
class PharmacieAdmin(admin.ModelAdmin):
    list_display = ("nom", "quartier", "telephone", "est_de_garde", "est_verifiee")
    search_fields = ("nom", "numero_agrement_onpg")
    list_filter = ("quartier", "est_de_garde", "est_verifiee")


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ("pharmacie", "medicament", "quantite_disponible", "prix_unitaire_gnf", "date_derniere_mise_a_jour")
    list_filter = ("pharmacie",)
    search_fields = ("medicament__nom_commercial", "pharmacie__nom")
