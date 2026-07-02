from rest_framework import generics, permissions
from .models import Commande
from .serializers import CommandeSerializer


class CommandeListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/commandes/  -> liste des commandes du patient connecté
    POST /api/commandes/  -> créer une nouvelle réservation
    """

    serializer_class = CommandeSerializer
    # Il faut être connecté pour réserver un médicament (donnée sensible,
    # liée à une identité et potentiellement à une ordonnance)
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Un patient ne voit jamais les commandes d'un autre patient
        return Commande.objects.filter(patient=self.request.user).select_related(
            "stock__pharmacie", "stock__medicament"
        )

    def perform_create(self, serializer):
        # Le patient est déduit automatiquement du compte connecté,
        # jamais envoyé par le client (sécurité : impossible d'usurper un autre patient)
        serializer.save(patient=self.request.user)
