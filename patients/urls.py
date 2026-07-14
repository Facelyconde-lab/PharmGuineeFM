from django.urls import path
from . import views

app_name = "patients"

urlpatterns = [
    path("inscription/", views.inscription, name="inscription"),
    path("connexion/", views.connexion, name="connexion"),
    path("deconnexion/", views.deconnexion, name="deconnexion"),
    path("mes-commandes/", views.mes_commandes, name="mes_commandes"),
    path("visiteurs/", views.visiteurs, name="visiteurs"),
]
