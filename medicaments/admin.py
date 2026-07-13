from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Medicament


class MedicamentResource(resources.ModelResource):
    # colonnes attendues : nom_commercial, dci, dosage, categorie, description,
    # est_sur_ordonnance. import_id_fields vide -> chaque ligne crée toujours une
    # NOUVELLE fiche (pas de mise à jour d'existant, pour éviter les soucis de
    # colonne id vide). Pour corriger une fiche déjà créée, passer par l'admin normal.
    class Meta:
        model = Medicament
        fields = ("nom_commercial", "dci", "dosage", "categorie", "description", "est_sur_ordonnance")
        import_id_fields = ()


@admin.register(Medicament)
class MedicamentAdmin(ImportExportModelAdmin):
    resource_classes = [MedicamentResource]
    list_display = ("nom_commercial", "dosage", "dci", "categorie", "est_sur_ordonnance")
    search_fields = ("nom_commercial", "dci", "dosage")
    list_filter = ("categorie", "est_sur_ordonnance")
