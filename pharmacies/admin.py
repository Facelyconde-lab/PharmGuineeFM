from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Pharmacie, Stock


class PharmacieResource(resources.ModelResource):
    # colonnes attendues : nom, quartier, adresse, latitude, longitude,
    # numero_agrement_onpg, telephone, est_de_garde, est_verifiee.
    # quartier = un des codes exacts (kaloum/ratoma/matoto/dixinn/matam), pas le
    # nom affiché. import_id_fields vide -> toujours des NOUVELLES fiches.
    class Meta:
        model = Pharmacie
        fields = (
            "nom", "quartier", "adresse", "latitude", "longitude",
            "numero_agrement_onpg", "telephone", "est_de_garde", "est_verifiee",
        )
        import_id_fields = ()


@admin.register(Pharmacie)
class PharmacieAdmin(ImportExportModelAdmin):
    resource_classes = [PharmacieResource]
    list_display = ("nom", "quartier", "telephone", "est_de_garde", "est_verifiee", "compte_gestionnaire")
    search_fields = ("nom", "numero_agrement_onpg")
    list_filter = ("quartier", "est_de_garde", "est_verifiee")


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ("pharmacie", "medicament", "quantite_disponible", "prix_unitaire_gnf", "date_derniere_mise_a_jour")
    list_filter = ("pharmacie",)
    search_fields = ("medicament__nom_commercial", "pharmacie__nom")
