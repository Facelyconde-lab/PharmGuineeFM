from django.urls import path
from . import views

urlpatterns = [
    path("", views.CommandeListCreateView.as_view(), name="commandes"),
]
