from rest_framework import serializers
from .models import Commande


class CommandeSerializer(serializers.ModelSerializer):
    # en lecture seule, évite de recharger la pharmacie/le médicament à part côté front
    pharmacie = serializers.CharField(source="stock.pharmacie.nom", read_only=True)
    medicament = serializers.CharField(source="stock.medicament.nom_commercial", read_only=True)

    class Meta:
        model = Commande
        fields = [
            "id",
            "stock",
            "pharmacie",
            "medicament",
            "quantite",
            "mode_livraison",
            "adresse_livraison",
            "ordonnance",
            "statut",
            "date_creation",
        ]
        read_only_fields = ["statut", "date_creation"]  # statut = toujours en_attente à la création

    def validate_quantite(self, value):
        if value < 1:
            raise serializers.ValidationError("La quantité doit être d'au moins 1.")
        return value

    def validate(self, data):
        stock = data["stock"]
        quantite = data.get("quantite", 1)
        if quantite > stock.quantite_disponible:
            raise serializers.ValidationError(
                f"Stock insuffisant : seulement {stock.quantite_disponible} disponible(s)."
            )

        if data.get("mode_livraison") == "livraison" and not data.get("adresse_livraison", "").strip():
            raise serializers.ValidationError(
                "Une adresse de livraison est obligatoire pour une livraison à domicile."
            )

        # sur ordonnance -> photo obligatoire, la pharmacie vérifie ensuite
        if stock.medicament.est_sur_ordonnance and not data.get("ordonnance"):
            raise serializers.ValidationError(
                "Ce médicament est vendu sur ordonnance : merci de joindre une photo de "
                "l'ordonnance pour continuer la réservation."
            )
        return data


class CommandeStatutSerializer(serializers.ModelSerializer):
    """Pour la pharmacie, juste pour changer le statut."""

    class Meta:
        model = Commande
        fields = ["id", "statut"]
