from django.contrib import admin
from django.utils.html import format_html
from .models import Commande


@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = (
        "id", "patient", "stock", "quantite", "statut", "mode_livraison",
        "date_creation", "lien_ordonnance",
    )
    list_filter = ("statut", "mode_livraison")
    search_fields = ("patient__username", "numero_scelle")
    readonly_fields = ("apercu_ordonnance",)  # pour vérifier une ordonnance direct depuis l'admin

    def lien_ordonnance(self, commande):
        if commande.ordonnance:
            return format_html('<a href="{}" target="_blank">📄 Voir</a>', commande.ordonnance.url)
        return "—"
    lien_ordonnance.short_description = "Ordonnance"

    def apercu_ordonnance(self, commande):
        if commande.ordonnance:
            return format_html(
                '<a href="{0}" target="_blank">'
                '<img src="{0}" style="max-width:320px; max-height:320px; border-radius:6px;">'
                '</a>',
                commande.ordonnance.url,
            )
        return "Aucune ordonnance jointe à cette commande."
    apercu_ordonnance.short_description = "Aperçu de l'ordonnance"
