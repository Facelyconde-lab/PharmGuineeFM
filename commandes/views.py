from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError

from pharmacies.models import Stock
from .models import Commande
from .serializers import CommandeSerializer, CommandeStatutSerializer


class CommandeListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/commandes/  -> liste des commandes du patient connecté
    POST /api/commandes/  -> créer une nouvelle réservation
    """

    serializer_class = CommandeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Commande.objects.filter(patient=self.request.user).select_related(
            "stock__pharmacie", "stock__medicament"
        )

    def perform_create(self, serializer):
        # Le stock validé par le serializer (déjà un objet Stock, pas juste un id)
        stock_id = serializer.validated_data["stock"].pk
        quantite = serializer.validated_data["quantite"]

        # transaction.atomic + select_for_update : verrouille la ligne de stock
        # pendant l'opération, pour empêcher deux réservations simultanées de
        # passer toutes les deux la vérification avant que l'une des deux ne
        # mette à jour la quantité (cas classique de "double réservation").
        # Le contrôle fait dans le serializer (validate()) reste utile pour un
        # message d'erreur rapide, mais celui-ci, protégé par le verrou, est
        # le seul dont on peut vraiment garantir l'exactitude.
        with transaction.atomic():
            stock = get_object_or_404(Stock.objects.select_for_update(), pk=stock_id)

            if quantite > stock.quantite_disponible:
                raise ValidationError(
                    f"Stock insuffisant : seulement {stock.quantite_disponible} disponible(s)."
                )

            stock.quantite_disponible -= quantite
            stock.save(update_fields=["quantite_disponible"])

            # Le patient est déduit automatiquement du compte connecté,
            # jamais envoyé par le client (sécurité : impossible d'usurper un autre patient)
            serializer.save(patient=self.request.user)


class CommandeStatutUpdateView(generics.UpdateAPIView):
    """
    PATCH /api/commandes/<id>/statut/ -> la pharmacie change le statut
    (ex : {"statut": "validee"}). Réservé au gestionnaire de la pharmacie
    concernée par la commande.
    """

    queryset = Commande.objects.select_related("stock__pharmacie")
    serializer_class = CommandeStatutSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        commande = super().get_object()
        pharmacie = commande.stock.pharmacie
        if pharmacie.compte_gestionnaire_id != self.request.user.id:
            # On refuse, y compris si l'utilisateur est connecté, s'il ne
            # gère pas la pharmacie propriétaire de cette commande.
            raise PermissionDenied("Vous ne gérez pas la pharmacie concernée par cette commande.")
        return commande
