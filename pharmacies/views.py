import secrets

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.decorators import api_view
from rest_framework.response import Response
from geopy.distance import geodesic

from commandes.models import Commande
from commandes.notifications import envoyer_notification_statut
from medicaments.models import Medicament
from medicaments.utils import retirer_accents
from .models import Pharmacie, Stock


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
    #    On compare sur cle_recherche (sans accents) plutôt que sur nom_commercial,
    #    pour que "paracetamol" tapé sans accent trouve "Paracétamol".
    resultats = Stock.objects.filter(
        medicament__cle_recherche__icontains=retirer_accents(nom),
        quantite_disponible__gt=0,
        pharmacie__est_verifiee=True,
    ).select_related("pharmacie", "medicament")

    # 2. Calcul de la distance réelle entre le patient et chaque pharmacie
    donnees = []
    for stock in resultats:
        position_pharmacie = (float(stock.pharmacie.latitude), float(stock.pharmacie.longitude))
        distance_km = geodesic((lat_patient, lng_patient), position_pharmacie).km

        # request.build_absolute_uri() transforme le chemin relatif du fichier
        # (ex : /media/medicaments/xxx.png) en URL complète, utilisable tel
        # quel dans une balise <img> peu importe la page où elle est affichée.
        image_url = None
        if stock.medicament.image:
            image_url = request.build_absolute_uri(stock.medicament.image.url)

        donnees.append({
            "stock_id": stock.pk,
            "pharmacie": stock.pharmacie.nom,
            "quartier": stock.pharmacie.get_quartier_display(),
            "medicament": stock.medicament.nom_commercial,
            "image_url": image_url,
            "prix_gnf": stock.prix_unitaire_gnf,
            "quantite_disponible": stock.quantite_disponible,
            "distance_km": round(distance_km, 2),
        })

    # 3. Tri par proximité : la pharmacie la plus proche apparaît en premier
    donnees.sort(key=lambda d: d["distance_km"])

    return Response(donnees)


@login_required
def tableau_de_bord(request):
    """
    Espace de gestion réservé au gestionnaire d'une pharmacie : mise à jour
    des stocks (quantités, prix), ajout de nouveaux médicaments au catalogue
    de l'officine, et traitement des commandes reçues (valider / refuser /
    marquer comme livrée).
    """
    pharmacie = Pharmacie.objects.filter(compte_gestionnaire=request.user).first()
    if pharmacie is None:
        messages.error(request, "Votre compte ne gère aucune pharmacie pour le moment.")
        return redirect("accueil")

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "maj_stock":
            # Modifier la quantité et/ou le prix d'un médicament déjà au catalogue
            stock = get_object_or_404(Stock, pk=request.POST.get("stock_id"), pharmacie=pharmacie)
            stock.quantite_disponible = int(request.POST.get("quantite_disponible", stock.quantite_disponible))
            stock.prix_unitaire_gnf = int(request.POST.get("prix_unitaire_gnf", stock.prix_unitaire_gnf))
            stock.save()
            messages.success(request, f"Stock de « {stock.medicament} » mis à jour.")

        elif action == "ajouter_stock":
            # Ajouter un médicament du catalogue national qui n'est pas encore
            # référencé pour cette officine (ou mettre à jour s'il l'est déjà)
            medicament = get_object_or_404(Medicament, pk=request.POST.get("medicament_id"))
            quantite = int(request.POST.get("nouvelle_quantite", 0) or 0)
            prix = int(request.POST.get("nouveau_prix", 0) or 0)
            stock, cree = Stock.objects.get_or_create(
                pharmacie=pharmacie,
                medicament=medicament,
                defaults={"quantite_disponible": quantite, "prix_unitaire_gnf": prix},
            )
            if not cree:
                stock.quantite_disponible = quantite
                stock.prix_unitaire_gnf = prix
                stock.save()
            messages.success(request, f"« {medicament} » ajouté à votre catalogue.")

        elif action == "valider_commande":
            commande = get_object_or_404(
                Commande, pk=request.POST.get("commande_id"), stock__pharmacie=pharmacie
            )
            commande.statut = "validee"
            commande.save(update_fields=["statut"])
            envoyer_notification_statut(commande)
            messages.success(request, f"Commande #{commande.pk} validée.")

        elif action == "refuser_commande":
            commande = get_object_or_404(
                Commande, pk=request.POST.get("commande_id"), stock__pharmacie=pharmacie
            )
            # La quantité réservée est restituée au stock puisque la commande n'aura pas lieu
            commande.stock.quantite_disponible += commande.quantite
            commande.stock.save(update_fields=["quantite_disponible"])
            commande.statut = "annulee"
            commande.save(update_fields=["statut"])
            envoyer_notification_statut(commande)
            messages.success(request, f"Commande #{commande.pk} refusée, stock restitué.")

        elif action == "marquer_preparee":
            # Étape intermédiaire entre "validée" et "livrée" : la commande est
            # physiquement préparée et scellée. On génère un numéro de scellé
            # unique, qui sert de preuve d'intégrité à la remise (le patient
            # ou le livreur peut vérifier que le scellé n'a pas été ouvert).
            commande = get_object_or_404(
                Commande, pk=request.POST.get("commande_id"), stock__pharmacie=pharmacie
            )
            commande.statut = "preparee"
            commande.numero_scelle = f"SCL-{secrets.token_hex(4).upper()}"
            commande.save(update_fields=["statut", "numero_scelle"])
            envoyer_notification_statut(commande)
            messages.success(
                request,
                f"Commande #{commande.pk} préparée et scellée (n° {commande.numero_scelle}).",
            )

        elif action == "marquer_en_livraison":
            # Uniquement pertinent pour les commandes en mode "livraison à
            # domicile" ; pour un retrait en pharmacie, on passe directement
            # de "préparée" à "livrée" via l'action ci-dessous.
            commande = get_object_or_404(
                Commande, pk=request.POST.get("commande_id"), stock__pharmacie=pharmacie
            )
            commande.statut = "en_livraison"
            commande.save(update_fields=["statut"])
            envoyer_notification_statut(commande)
            messages.success(request, f"Commande #{commande.pk} en cours de livraison.")

        elif action == "marquer_livree":
            commande = get_object_or_404(
                Commande, pk=request.POST.get("commande_id"), stock__pharmacie=pharmacie
            )
            commande.statut = "livree"
            commande.save(update_fields=["statut"])
            envoyer_notification_statut(commande)
            messages.success(request, f"Commande #{commande.pk} marquée comme livrée.")

        # Redirection après traitement pour éviter qu'un rafraîchissement de
        # page (F5) ne renvoie accidentellement le même formulaire deux fois
        return redirect("tableau_de_bord")

    stocks = pharmacie.stocks.select_related("medicament").order_by("medicament__nom_commercial")
    medicaments_deja_references = stocks.values_list("medicament_id", flat=True)
    medicaments_disponibles = Medicament.objects.exclude(pk__in=medicaments_deja_references)

    # Alerte automatique : tout médicament en rupture (0) ou en stock faible
    # (<= SEUIL_ALERTE_STOCK) est mis en avant ici, pour que le gestionnaire
    # le voie dès l'ouverture du tableau de bord sans parcourir tout le
    # tableau "Vos stocks".
    stocks_a_alerter = stocks.filter(
        quantite_disponible__lte=Stock.SEUIL_ALERTE_STOCK
    ).order_by("quantite_disponible")

    commandes = (
        Commande.objects.filter(stock__pharmacie=pharmacie)
        .exclude(statut__in=["livree", "annulee"])
        .select_related("stock__medicament", "patient")
        .order_by("-date_creation")
    )

    contexte = {
        "pharmacie": pharmacie,
        "stocks": stocks,
        "medicaments_disponibles": medicaments_disponibles,
        "commandes": commandes,
        "stocks_a_alerter": stocks_a_alerter,
    }
    return render(request, "pharmacies/tableau_de_bord.html", contexte)
