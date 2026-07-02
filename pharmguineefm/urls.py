"""
URL configuration for pharmguineefm project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from pharmacies.views import accueil, tableau_de_bord

urlpatterns = [
    path('admin/', admin.site.urls),

    # Page publique de recherche (frontend)
    path('', accueil, name='accueil'),

    # Espace de gestion réservé aux gestionnaires de pharmacie
    path('pharmacie/', tableau_de_bord, name='tableau_de_bord'),

    # Inscription / connexion / déconnexion des patients
    path('patients/', include('patients.urls')),

    # Tableau de bord réservé au ministère de la Santé (comptes staff)
    path('ministere/', include('ministere.urls')),

    # Toutes les routes de l'API commencent par /api/
    # Ex : /api/recherche/?nom=paracetamol&lat=...&lng=...
    path('api/', include('pharmacies.urls')),
    path('api/commandes/', include('commandes.urls')),

    # Ajoute un lien "Log in" / "Log out" sur les pages de l'API navigable
    # (rest_framework), pratique pour tester les endpoints protégés depuis le navigateur
    path('api-auth/', include('rest_framework.urls')),
]
