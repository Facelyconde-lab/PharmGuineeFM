from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Medicament


class MedicamentResource(resources.ModelResource):
    # colonnes attendues dans le fichier Excel/CSV : nom_commercial, dci, dosage,
    # categorie, description, est_sur_ordonnance. "id" sert juste à mettre à jour
    # une fiche déjà importée plutôt que d'en recréer une (laisser vide pour un ajout).
    class Meta:
        model = Medicament
        fields = ("id", "nom_commercial", "dci", "dosage", "categorie", "description", "est_sur_ordonnance")
        import_id_fields = ("id",)
        skip_unchanged = True


@admin.register(Medicament)
class MedicamentAdmin(ImportExportModelAdmin):
    resource_classes = [MedicamentResource]
    list_display = ("nom_commercial", "dosage", "dci", "categorie", "est_sur_ordonnance")
    search_fields = ("nom_commercial", "dci", "dosage")
    list_filter = ("categorie", "est_sur_ordonnance")
