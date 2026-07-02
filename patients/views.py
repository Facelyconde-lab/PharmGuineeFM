from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import render, redirect


def inscription(request):
    """Création d'un compte patient (nom d'utilisateur + mot de passe)."""
    if request.method == "POST":
        formulaire = UserCreationForm(request.POST)
        if formulaire.is_valid():
            utilisateur = formulaire.save()
            # On connecte automatiquement le patient juste après son inscription,
            # pour lui éviter une étape de connexion supplémentaire
            login(request, utilisateur)
            return redirect("accueil")
    else:
        formulaire = UserCreationForm()
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
