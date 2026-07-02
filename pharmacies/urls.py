from django.urls import path
from . import views

urlpatterns = [
    path("recherche/", views.recherche_medicament, name="recherche_medicament"),
]
