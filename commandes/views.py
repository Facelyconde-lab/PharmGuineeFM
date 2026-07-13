from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError

from pharmacies.models import Stock
from .models import Commande
from .serializers import CommandeSerializer, CommandeStatutSerializer


class CommandeListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/commandes/  -> commandes du patient connecté
    POST /api/commandes/  -> nouvelle réservation
    """

    serializer_class = CommandeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Commande.objects.filter(patient=self.request.user).select_related(
            "stock__pharmacie", "stock__medicament"
        )

    def perform_create(self, serializer):
        stock_id = serializer.validated_data["stock"].pk
        quantite = serializer.validated_data["quantite"]

        # select_for_update verrouille la ligne le temps de la transaction : sans
        # ça deux réservations simultanées peuvent toutes les deux passer la
        # vérification avant que le stock soit décrémenté (double réservation).
        # La vérif dans le serializer sert juste à retourner une erreur rapide,
        # la vraie garantie c'est celle-ci, protégée par le verrou.
        with transaction.atomic():
            stock = get_object_or_404(Stock.objects.select_for_update(), pk=stock_id)

            if quantite > stock.quantite_disponible:
                raise ValidationError(
                    f"Stock insuffisant : seulement {stock.quantite_disponible} disponible(s)."
                )

            stock.quantite_disponible -= quantite
            stock.save(update_fields=["quantite_disponible"])

            serializer.save(patient=self.request.user)  # jamais le client, sécurité


class CommandeStatutUpdateView(generics.UpdateAPIView):
    """PATCH /api/commandes/<id>/statut/ - réservé au gestionnaire de la pharmacie concernée."""

    queryset = Commande.objects.select_related("stock__pharmacie")
    serializer_class = CommandeStatutSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        commande = super().get_object()
        pharmacie = commande.stock.pharmacie
        if pharmacie.compte_gestionnaire_id != self.request.user.id:
            raise PermissionDenied("Vous ne gérez pas la pharmacie concernée par cette commande.")
        return commande
