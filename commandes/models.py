from django.db import models
from django.conf import settings
from pharmacies.models import Stock


class Commande(models.Model):
    """Une réservation de médicament passée par un patient sur un stock précis."""

    STATUTS = [
        ("en_attente", "En attente de validation"),
        ("validee", "Validée par la pharmacie"),
        ("preparee", "Scellée et prête"),
        ("en_livraison", "En cours de livraison"),
        ("livree", "Livrée"),
        ("annulee", "Annulée"),
    ]

    MODES_LIVRAISON = [
        ("retrait", "Retrait en pharmacie"),
        ("livraison", "Livraison à domicile"),
    ]

    # Lié au modèle utilisateur Django standard (settings.AUTH_USER_MODEL) :
    # inutile de recréer un système de comptes, on l'étendra plus tard si besoin
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="commandes"
    )

    # on_delete=PROTECT : on refuse de supprimer un stock tant qu'il existe
    # des commandes liées, pour ne jamais perdre l'historique d'une transaction
    stock = models.ForeignKey(Stock, on_delete=models.PROTECT, related_name="commandes")

    quantite = models.PositiveIntegerField(default=1)

    # Photo de l'ordonnance, obligatoire uniquement si le médicament est
    # marqué "est_sur_ordonnance" côté modèle Medicament
    ordonnance = models.ImageField(upload_to="ordonnances/", blank=True, null=True)

    # Généré au moment de la préparation, imprimé sur le scellé de sécurité
    numero_scelle = models.CharField(max_length=30, blank=True)

    statut = models.CharField(max_length=20, choices=STATUTS, default="en_attente")
    mode_livraison = models.CharField(max_length=20, choices=MODES_LIVRAISON)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ["-date_creation"]

    def __str__(self):
        return f"Commande #{self.pk} — {self.stock.medicament} ({self.get_statut_display()})"
