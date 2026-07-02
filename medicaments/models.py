from django.db import models


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

    def __str__(self):
        return f"{self.nom_commercial} ({self.dci})"
