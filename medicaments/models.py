from django.db import models
from .utils import retirer_accents


class Medicament(models.Model):
    """
    Un produit pharmaceutique référencé dans le catalogue national.
    Exemple : nom_commercial="Efferalgan 500mg", dci="Paracétamol".
    """

    # Nom commercial tel qu'affiché au patient (ex : "Coartem")
    nom_commercial = models.CharField(max_length=150)

    # Dénomination Commune Internationale : le nom générique du médicament,
    # utile pour retrouver un produit même si le patient ne connaît que le
    # générique (ex : "Artéméther-Luméfantrine")
    dci = models.CharField("Dénomination Commune Internationale", max_length=150)

    # Catégorie du médicament (ex : "Antalgique", "Antipaludique")
    categorie = models.CharField(max_length=100)

    description = models.TextField(blank=True)

    # Si True, le patient devra téléverser une ordonnance avant la commande
    # (voir le protocole de dispensation sécurisée décrit dans le dossier projet)
    est_sur_ordonnance = models.BooleanField(default=False)

    image = models.ImageField(upload_to="medicaments/", blank=True, null=True)

    # Champ calculé automatiquement (voir save() ci-dessous) : nom commercial
    # + DCI, sans accents et en minuscule. Sert uniquement à la recherche,
    # pour qu'un patient tapant "paracetamol" trouve "Paracétamol" sans accent.
    cle_recherche = models.CharField(max_length=310, blank=True, editable=False, db_index=True)

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Médicament"
        verbose_name_plural = "Médicaments"
        # Un index sur le nom et la DCI accélère la recherche par nom,
        # qui est l'action la plus fréquente de la plateforme
        indexes = [
            models.Index(fields=["nom_commercial"]),
            models.Index(fields=["dci"]),
        ]
        ordering = ["nom_commercial"]

    def save(self, *args, **kwargs):
        # Recalculée à chaque enregistrement, pour rester toujours synchronisée
        # avec nom_commercial et dci, même si l'un des deux est modifié plus tard.
        self.cle_recherche = retirer_accents(f"{self.nom_commercial} {self.dci}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nom_commercial} ({self.dci})"
