from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.decorators import api_view
from rest_framework.response import Response
from geopy.distance import geodesic

from .models import Stock


@ensure_csrf_cookie
def accueil(request):
    """
    Page publique de recherche : formulaire + résultats affichés en JavaScript (fetch).
    @ensure_csrf_cookie garantit que le cookie CSRF est posé dès l'arrivée sur la
    page, nécessaire pour que le bouton "Réserver" (requête POST en JavaScript)
    fonctionne, même si la page ne contient elle-même aucun <form> classique.
    """
    return render(request, "pharmacies/accueil.html")


@api_view(["GET"])
def recherche_medicament(request):
    """
    Endpoint de recherche : trouve les pharmacies les plus proches d'un
    patient qui détiennent, en stock, le médicament recherché.

    Exemple d'appel :
    /api/recherche/?nom=paracetamol&lat=9.535&lng=-13.680
    """
    nom = request.query_params.get("nom", "")
    lat_param = request.query_params.get("lat")
    lng_param = request.query_params.get("lng")

    if not nom:
        return Response({"erreur": "Le paramètre 'nom' est obligatoire."}, status=400)
    if lat_param is None or lng_param is None:
        return Response({"erreur": "Les paramètres 'lat' et 'lng' sont obligatoires."}, status=400)

    try:
        lat_patient = float(lat_param)
        lng_patient = float(lng_param)
    except ValueError:
        return Response({"erreur": "'lat' et 'lng' doivent être des nombres."}, status=400)

    # 1. On ne retient que les stocks disponibles (quantité > 0) du médicament
    #    recherché, dans des pharmacies déjà vérifiées par l'ONPG/DNPM.
    #    select_related évite des requêtes SQL supplémentaires pour chaque résultat.
    resultats = Stock.objects.filter(
        medicament__nom_commercial__icontains=nom,
        quantite_disponible__gt=0,
        pharmacie__est_verifiee=True,
    ).select_related("pharmacie", "medicament")

    # 2. Calcul de la distance réelle entre le patient et chaque pharmacie
    donnees = []
    for stock in resultats:
        position_pharmacie = (float(stock.pharmacie.latitude), float(stock.pharmacie.longitude))
        distance_km = geodesic((lat_patient, lng_patient), position_pharmacie).km
        donnees.append({
            "stock_id": stock.pk,
            "pharmacie": stock.pharmacie.nom,
            "quartier": stock.pharmacie.get_quartier_display(),
            "medicament": stock.medicament.nom_commercial,
            "prix_gnf": stock.prix_unitaire_gnf,
            "quantite_disponible": stock.quantite_disponible,
            "distance_km": round(distance_km, 2),
        })

    # 3. Tri par proximité : la pharmacie la plus proche apparaît en premier
    donnees.sort(key=lambda d: d["distance_km"])

    return Response(donnees)
