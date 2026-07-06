from rest_framework import serializers
from .models import Commande


class CommandeSerializer(serializers.ModelSerializer):
    # Champs calculés en lecture seule, pratiques pour vérifier le résultat
    # sans avoir à recharger séparément la pharmacie ou le médicament
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
        # Le patient et le statut ne sont jamais choisis par le client :
        # le patient vient du compte connecté, le statut démarre toujours à "en_attente"
        read_only_fields = ["statut", "date_creation"]

    def validate_quantite(self, value):
        if value < 1:
            raise serializers.ValidationError("La quantité doit être d'au moins 1.")
        return value

    def validate(self, data):
        # On vérifie qu'il reste bien assez de stock disponible avant d'accepter la réservation
        stock = data["stock"]
        quantite = data.get("quantite", 1)
        if quantite > stock.quantite_disponible:
            raise serializers.ValidationError(
                f"Stock insuffisant : seulement {stock.quantite_disponible} disponible(s)."
            )

        # L'adresse n'a de sens que pour une livraison à domicile ; sans elle,
        # la pharmacie/le livreur n'a aucun moyen de savoir où se rendre.
        if data.get("mode_livraison") == "livraison" and not data.get("adresse_livraison", "").strip():
            raise serializers.ValidationError(
                "Une adresse de livraison est obligatoire pour une livraison à domicile."
            )

        # Un médicament marqué "sur ordonnance" ne peut pas être réservé sans
        # qu'une photo d'ordonnance soit jointe : c'est la pharmacie qui vérifiera
        # ensuite sa validité avant de valider la commande.
        if stock.medicament.est_sur_ordonnance and not data.get("ordonnance"):
            raise serializers.ValidationError(
                "Ce médicament est vendu sur ordonnance : merci de joindre une photo de "
                "l'ordonnance pour continuer la réservation."
            )
        return data


class CommandeStatutSerializer(serializers.ModelSerializer):
    """Utilisé uniquement par la pharmacie pour changer le statut d'une commande."""

    class Meta:
        model = Commande
        fields = ["id", "statut"]
