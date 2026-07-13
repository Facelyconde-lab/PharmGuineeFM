from django.db import models
from django.conf import settings
from pharmacies.models import Stock


class Commande(models.Model):
    """Réservation d'un patient sur un stock précis."""

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

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="commandes"
    )

    # PROTECT : pas le droit de supprimer un stock tant qu'il a des commandes liées
    # (sinon on perd l'historique)
    stock = models.ForeignKey(Stock, on_delete=models.PROTECT, related_name="commandes")

    quantite = models.PositiveIntegerField(default=1)

    ordonnance = models.ImageField(upload_to="ordonnances/", blank=True, null=True)  # requis si médicament sur ordonnance

    numero_scelle = models.CharField(max_length=30, blank=True)  # généré à la préparation

    statut = models.CharField(max_length=20, choices=STATUTS, default="en_attente")
    mode_livraison = models.CharField(max_length=20, choices=MODES_LIVRAISON)

    # texte libre plutôt que rue/numéro structuré - l'adressage formel
    # n'existe pas partout à Conakry, un repère suffit en pratique
    adresse_livraison = models.CharField(
        max_length=255,
        blank=True,
        help_text="Quartier + repère (ex: Dixinn, près de la pharmacie Bonfi), requis pour une livraison à domicile.",
    )

    date_creation = models.DateTimeField(auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ["-date_creation"]

    def __str__(self):
        return f"Commande #{self.pk} — {self.stock.medicament} ({self.get_statut_display()})"
