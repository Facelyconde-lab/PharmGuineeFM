from django.contrib import admin
from .models import Medicament


@admin.register(Medicament)
class MedicamentAdmin(admin.ModelAdmin):
    list_display = ("nom_commercial", "dosage", "dci", "categorie", "est_sur_ordonnance")
    search_fields = ("nom_commercial", "dci", "dosage")
    list_filter = ("categorie", "est_sur_ordonnance")
