from django.contrib import admin
from import_export import fields, resources
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget
from medicaments.models import Medicament
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


class StockResource(resources.ModelResource):
    # pharmacie/medicament référencés par leur clé naturelle plutôt que par id
    # (id interne inconnu au moment de préparer le fichier Excel) : pharmacie par
    # numero_agrement_onpg, medicament par nom_commercial. Importer médicaments
    # et pharmacies AVANT ce fichier, sinon la correspondance échoue.
    pharmacie = fields.Field(
        column_name="pharmacie",
        attribute="pharmacie",
        widget=ForeignKeyWidget(Pharmacie, field="numero_agrement_onpg"),
    )
    medicament = fields.Field(
        column_name="medicament",
        attribute="medicament",
        widget=ForeignKeyWidget(Medicament, field="nom_commercial"),
    )

    class Meta:
        model = Stock
        fields = ("pharmacie", "medicament", "quantite_disponible", "prix_unitaire_gnf")
        import_id_fields = ()


@admin.register(Stock)
class StockAdmin(ImportExportModelAdmin):
    resource_classes = [StockResource]
    list_display = ("pharmacie", "medicament", "quantite_disponible", "prix_unitaire_gnf", "date_derniere_mise_a_jour")
    list_filter = ("pharmacie",)
    search_fields = ("medicament__nom_commercial", "pharmacie__nom")
