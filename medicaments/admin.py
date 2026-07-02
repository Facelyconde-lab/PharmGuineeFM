from django.contrib import admin
from .models import Medicament


@admin.register(Medicament)
class MedicamentAdmin(admin.ModelAdmin):
    # Colonnes affichées dans la liste des médicaments
    list_display = ("nom_commercial", "dci", "categorie", "est_sur_ordonnance")
    # Barre de recherche par nom commercial ou DCI
    search_fields = ("nom_commercial", "dci")
    list_filter = ("categorie", "est_sur_ordonnance")
