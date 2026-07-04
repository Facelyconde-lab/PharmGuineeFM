from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class InscriptionForm(UserCreationForm):
    """
    Formulaire d'inscription patient : reprend le formulaire standard de
    Django (nom d'utilisateur + mot de passe), en ajoutant un champ email
    obligatoire.

    Pourquoi un email obligatoire : c'est la seule façon simple et gratuite
    d'informer automatiquement le patient quand sa commande change de statut
    (validée, préparée, en livraison, livrée) sans qu'il ait à recharger sans
    cesse la page. Aucun SMS n'est envoyé pour l'instant (ça a un coût), donc
    l'email est le canal de notification retenu pour ce projet pilote.
    """

    email = forms.EmailField(
        required=True,
        label="Adresse email",
        help_text="Utilisée uniquement pour vous informer du suivi de vos commandes.",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def save(self, commit=True):
        # On récupère l'utilisateur créé par le formulaire parent, mais sans
        # l'enregistrer tout de suite (commit=False), pour pouvoir y ajouter
        # l'email avant la sauvegarde finale en base de données.
        utilisateur = super().save(commit=False)
        utilisateur.email = self.cleaned_data["email"]
        if commit:
            utilisateur.save()
        return utilisateur
