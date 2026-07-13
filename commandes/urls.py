from django.urls import path
from . import views

urlpatterns = [
    path("", views.CommandeListCreateView.as_view(), name="commandes"),
    path("panier/", views.PanierCreateView.as_view(), name="panier"),
    path("<int:pk>/statut/", views.CommandeStatutUpdateView.as_view(), name="commande_statut"),
]
