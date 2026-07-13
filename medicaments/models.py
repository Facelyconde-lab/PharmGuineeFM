from django.db import models
from .utils import retirer_accents


class Medicament(models.Model):
    """Ex : nom_commercial="Efferalgan 500mg", dci="Paracétamol"."""

    nom_commercial = models.CharField(max_length=150)

    # nom générique, utile si le patient ne connaît que le générique (ex: "Artéméther-Luméfantrine")
    dci = models.CharField("Dénomination Commune Internationale", max_length=150)

    categorie = models.CharField(max_length=100)  # "Antalgique", "Antipaludique" etc

    description = models.TextField(blank=True)

    est_sur_ordonnance = models.BooleanField(default=False)  # -> ordonnance obligatoire à la réservation

    image = models.ImageField(upload_to="medicaments/", blank=True, null=True)

    # nom + dci sans accents/minuscule, recalculé à chaque save(), sert que pour la recherche
    cle_recherche = models.CharField(max_length=310, blank=True, editable=False, db_index=True)

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Médicament"
        verbose_name_plural = "Médicaments"
        indexes = [
            models.Index(fields=["nom_commercial"]),
            models.Index(fields=["dci"]),
        ]
        ordering = ["nom_commercial"]

    def save(self, *args, **kwargs):
        self.cle_recherche = retirer_accents(f"{self.nom_commercial} {self.dci}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nom_commercial} ({self.dci})"
