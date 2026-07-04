from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect

from commandes.models import Commande
from .forms import InscriptionForm


def inscription(request):
    """Création d'un compte patient (nom d'utilisateur + email + mot de passe)."""
    if request.method == "POST":
        formulaire = InscriptionForm(request.POST)
        if formulaire.is_valid():
            utilisateur = formulaire.save()
            # On connecte automatiquement le patient juste après son inscription,
            # pour lui éviter une étape de connexion supplémentaire
            login(request, utilisateur)
            return redirect("accueil")
    else:
        formulaire = InscriptionForm()
    return render(request, "patients/inscription.html", {"formulaire": formulaire})


def connexion(request):
    """Connexion d'un patient déjà inscrit."""
    if request.method == "POST":
        formulaire = AuthenticationForm(request, data=request.POST)
        if formulaire.is_valid():
            login(request, formulaire.get_user())
            return redirect("accueil")
    else:
        formulaire = AuthenticationForm()
    return render(request, "patients/connexion.html", {"formulaire": formulaire})


def deconnexion(request):
    logout(request)
    return redirect("accueil")


@login_required
def mes_commandes(request):
    """
    Historique des commandes du patient connecté : lui permet de suivre où
    en est chaque réservation (validée, préparée, en livraison, livrée...)
    sans dépendre uniquement des emails de notification.
    """
    commandes = (
        Commande.objects.filter(patient=request.user)
        .select_related("stock__pharmacie", "stock__medicament")
        .order_by("-date_creation")
    )
    return render(request, "patients/mes_commandes.html", {"commandes": commandes})
