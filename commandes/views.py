import json
import uuid

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

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


class PanierCreateView(APIView):
    """
    POST /api/commandes/panier/ - réservation groupée : plusieurs produits d'une
    même pharmacie validés d'un coup (le panier côté front), plutôt qu'une
    réservation à la fois comme CommandeListCreateView. Chaque produit reste sa
    propre Commande (statut suivi séparément par la pharmacie), mais elles
    partagent un même groupe_commande pour être affichées ensemble côté patient.

    Champs attendus (multipart - il peut y avoir des photos d'ordonnance) :
      lignes : JSON '[{"stock_id": 12, "quantite": 2}, ...]'
      mode_livraison, adresse_livraison : partagés pour tout le panier
      ordonnance_0, ordonnance_1, ... : photo pour la ligne à cet index (même
      ordre que "lignes"), si son médicament est vendu sur ordonnance
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            lignes = json.loads(request.data.get("lignes", "[]"))
        except (TypeError, ValueError):
            return Response({"erreur": "Panier invalide."}, status=status.HTTP_400_BAD_REQUEST)

        if not lignes:
            return Response({"erreur": "Le panier est vide."}, status=status.HTTP_400_BAD_REQUEST)

        mode_livraison = request.data.get("mode_livraison")
        if mode_livraison not in ("retrait", "livraison"):
            return Response({"erreur": "Mode de livraison invalide."}, status=status.HTTP_400_BAD_REQUEST)

        adresse_livraison = request.data.get("adresse_livraison", "")
        if mode_livraison == "livraison" and not adresse_livraison.strip():
            return Response(
                {"erreur": "Une adresse de livraison est obligatoire pour une livraison à domicile."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # même principe que CommandeListCreateView.perform_create, mais pour N
        # lignes à la fois : tout verrouiller et tout vérifier avant de rien
        # écrire, pour ne pas décrémenter la moitié du panier puis planter sur
        # la ligne suivante.
        with transaction.atomic():
            stocks = {}
            pharmacie_id = None
            for ligne in lignes:
                stock = get_object_or_404(Stock.objects.select_for_update(), pk=ligne.get("stock_id"))
                if pharmacie_id is None:
                    pharmacie_id = stock.pharmacie_id
                elif stock.pharmacie_id != pharmacie_id:
                    return Response(
                        {"erreur": "Toutes les lignes du panier doivent venir de la même pharmacie."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                stocks[ligne.get("stock_id")] = stock

            for index, ligne in enumerate(lignes):
                stock = stocks[ligne.get("stock_id")]
                quantite = int(ligne.get("quantite", 1))
                if quantite < 1:
                    return Response({"erreur": "Quantité invalide."}, status=status.HTTP_400_BAD_REQUEST)
                if quantite > stock.quantite_disponible:
                    return Response(
                        {"erreur": f"Stock insuffisant pour {stock.medicament} : {stock.quantite_disponible} disponible(s)."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if stock.medicament.est_sur_ordonnance and f"ordonnance_{index}" not in request.FILES:
                    return Response(
                        {"erreur": f"Ordonnance obligatoire pour {stock.medicament}."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            groupe = uuid.uuid4()  # même valeur pour toutes les lignes de ce panier
            commandes_creees = []
            for index, ligne in enumerate(lignes):
                stock = stocks[ligne.get("stock_id")]
                quantite = int(ligne.get("quantite", 1))

                stock.quantite_disponible -= quantite
                stock.save(update_fields=["quantite_disponible"])

                commande = Commande.objects.create(
                    patient=request.user,
                    stock=stock,
                    quantite=quantite,
                    mode_livraison=mode_livraison,
                    adresse_livraison=adresse_livraison,
                    ordonnance=request.FILES.get(f"ordonnance_{index}"),
                    groupe_commande=groupe,
                )
                commandes_creees.append(commande.pk)

        return Response({"commandes": commandes_creees}, status=status.HTTP_201_CREATED)


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
