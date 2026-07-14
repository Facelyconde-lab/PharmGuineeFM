from django.conf import settings
from django.db import models


class VisiteRecherche(models.Model):
    """Une ligne par recherche de médicament sur la page d'accueil, connecté ou pas."""

    date_creation = models.DateTimeField(auto_now_add=True)

    # vide si visiteur anonyme (pas connecté au moment de la recherche)
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recherches",
    )

    # identifie un visiteur anonyme sans stocker son IP (session Django, déjà
    # posée par le navigateur) -> permet de compter des visiteurs uniques et
    # pas juste un nombre brut de recherches
    session_key = models.CharField(max_length=40, blank=True)

    class Meta:
        verbose_name = "Visite (recherche)"
        verbose_name_plural = "Visites (recherches)"
        ordering = ["-date_creation"]

    def __str__(self):
        qui = self.patient.username if self.patient else f"anonyme ({self.session_key[:8]})"
        return f"Recherche par {qui} le {self.date_creation:%d/%m/%Y %H:%M}"
