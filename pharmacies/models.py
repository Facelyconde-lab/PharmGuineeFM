from django.conf import settings
from django.db import models
from medicaments.models import Medicament


class Pharmacie(models.Model):
    """Une officine agréée, vérifiée auprès de l'Ordre National des Pharmaciens de Guinée (ONPG)."""

    # Liste de départ des quartiers de Conakry ; à compléter au fil du déploiement
    QUARTIERS = [
        ("kaloum", "Kaloum"),
        ("ratoma", "Ratoma"),
        ("matoto", "Matoto"),
        ("dixinn", "Dixinn"),
        ("matam", "Matam"),
    ]

    nom = models.CharField(max_length=150)
    quartier = models.CharField(max_length=50, choices=QUARTIERS)
    adresse = models.CharField(max_length=255)

    # Coordonnées GPS utilisées pour le calcul de distance (voir geopy dans le dossier projet)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    # Numéro d'agrément délivré par l'ONPG : sert à vérifier que l'officine
    # est légalement enregistrée avant de l'afficher aux patients
    numero_agrement_onpg = models.CharField(max_length=50, unique=True)

    telephone = models.CharField(max_length=20)

    est_de_garde = models.BooleanField("De garde actuellement", default=False)

    # Une pharmacie n'apparaît dans les résultats de recherche que si elle
    # a été validée manuellement (agrément vérifié auprès de l'ONPG/DNPM)
    est_verifiee = models.BooleanField("Vérifiée par l'ONPG/DNPM", default=False)

    # Le compte utilisateur (Django) autorisé à gérer cette officine :
    # mettre à jour les stocks, valider ou refuser les commandes.
    # SET_NULL : si le compte est supprimé, la pharmacie reste, juste sans gestionnaire.
    compte_gestionnaire = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pharmacie_geree",
    )

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pharmacie"
        verbose_name_plural = "Pharmacies"
        ordering = ["nom"]

    def __str__(self):
        return f"{self.nom} — {self.get_quartier_display()}"


class Stock(models.Model):
    """
    Fait le lien entre une pharmacie et un médicament : quantité disponible
    et prix pratiqué. C'est la table interrogée à chaque recherche patient.
    """

    pharmacie = models.ForeignKey(Pharmacie, on_delete=models.CASCADE, related_name="stocks")
    medicament = models.ForeignKey(Medicament, on_delete=models.CASCADE, related_name="stocks")

    quantite_disponible = models.PositiveIntegerField(default=0)

    # Prix affiché en francs guinéens (GNF), pas de centimes en pratique courante
    prix_unitaire_gnf = models.PositiveIntegerField("Prix unitaire (GNF)")

    date_derniere_mise_a_jour = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Stock"
        verbose_name_plural = "Stocks"
        # Une pharmacie ne peut avoir qu'une seule ligne de stock par médicament
        unique_together = ("pharmacie", "medicament")
        indexes = [models.Index(fields=["medicament", "quantite_disponible"])]

    def __str__(self):
        return f"{self.medicament} @ {self.pharmacie} ({self.quantite_disponible})"

    @property
    def est_en_rupture(self):
        return self.quantite_disponible == 0
