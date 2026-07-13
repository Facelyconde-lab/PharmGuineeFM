from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class InscriptionForm(UserCreationForm):
    # email obligatoire -> c'est le seul canal de notif pour l'instant (pas de SMS, ça coûte)
    email = forms.EmailField(
        required=True,
        label="Adresse email",
        help_text="Utilisée uniquement pour vous informer du suivi de vos commandes.",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def save(self, commit=True):
        utilisateur = super().save(commit=False)  # commit=False pour pouvoir rajouter l'email avant
        utilisateur.email = self.cleaned_data["email"]
        if commit:
            utilisateur.save()
        return utilisateur
