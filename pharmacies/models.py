from django.conf import settings
from django.db import models
from medicaments.models import Medicament


class Pharmacie(models.Model):
    """Une officine agréée, vérifiée auprès de l'ONPG."""

    # quartiers de Conakry pour commencer, à compléter plus tard
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

    # pour geopy (calcul de distance côté recherche)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    numero_agrement_onpg = models.CharField(max_length=50, unique=True)

    telephone = models.CharField(max_length=20)

    est_de_garde = models.BooleanField("De garde actuellement", default=False)

    # visible dans la recherche seulement si coché -> agrément vérifié à la main pour l'instant
    est_verifiee = models.BooleanField("Vérifiée par l'ONPG/DNPM", default=False)

    # le compte qui gère cette pharmacie (maj stocks, commandes)
    # SET_NULL plutôt que CASCADE : si le compte saute, la pharmacie reste
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
    """Pharmacie + médicament + quantité + prix. La table que la recherche interroge."""

    # seuil d'alerte stock faible - fixe pour l'instant, à voir si ça doit
    # varier par médicament plus tard (antipaludiques en saison des pluies p.ex)
    SEUIL_ALERTE_STOCK = 5

    pharmacie = models.ForeignKey(Pharmacie, on_delete=models.CASCADE, related_name="stocks")
    medicament = models.ForeignKey(Medicament, on_delete=models.CASCADE, related_name="stocks")

    quantite_disponible = models.PositiveIntegerField(default=0)

    prix_unitaire_gnf = models.PositiveIntegerField("Prix unitaire (GNF)")  # pas de centimes ici

    date_derniere_mise_a_jour = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Stock"
        verbose_name_plural = "Stocks"
        unique_together = ("pharmacie", "medicament")  # 1 ligne par médicament max
        indexes = [models.Index(fields=["medicament", "quantite_disponible"])]

    def __str__(self):
        return f"{self.medicament} @ {self.pharmacie} ({self.quantite_disponible})"

    @property
    def est_en_rupture(self):
        return self.quantite_disponible == 0

    @property
    def est_stock_faible(self):
        # > 0 pour pas compter deux fois avec est_en_rupture
        return 0 < self.quantite_disponible <= self.SEUIL_ALERTE_STOCK
