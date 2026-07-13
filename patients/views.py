import itertools

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect

from commandes.models import Commande
from .forms import InscriptionForm


def inscription(request):
    if request.method == "POST":
        formulaire = InscriptionForm(request.POST)
        if formulaire.is_valid():
            utilisateur = formulaire.save()
            login(request, utilisateur)  # connecté direct, pas besoin de se reconnecter juste après
            return redirect("accueil")
    else:
        formulaire = InscriptionForm()
    return render(request, "patients/inscription.html", {"formulaire": formulaire})


def connexion(request):
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
    """Historique des commandes du patient - suivi sans dépendre que de l'email."""
    commandes = (
        Commande.objects.filter(patient=request.user)
        .select_related("stock__pharmacie", "stock__medicament")
        .order_by("-date_creation")
    )
    # un panier validé d'un coup crée plusieurs Commande (une par produit) qui
    # partagent le même groupe_commande -> on les regroupe ici pour les afficher
    # comme une seule commande à plusieurs lignes plutôt que N réservations
    # séparées. groupby marche seulement sur des éléments déjà côte à côte, ce
    # qui est le cas ici : les lignes d'un même panier sont créées à la suite,
    # donc adjacentes une fois triées par -date_creation.
    groupes = [
        {"id": cle, "lignes": list(lignes)}
        for cle, lignes in itertools.groupby(commandes, key=lambda c: c.groupe_commande)
    ]
    return render(request, "patients/mes_commandes.html", {"groupes": groupes})
