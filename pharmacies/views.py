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
    # ensure_csrf_cookie : la page n'a pas de <form> classique, tout passe par
    # fetch() en JS (bouton Réserver), donc sans ça pas de cookie CSRF posé
    return render(request, "pharmacies/accueil.html")


@api_view(["GET"])
def recherche_medicament(request):
    """
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

    # stock dispo + pharmacie vérifiée uniquement. cle_recherche = sans accents,
    # comparé à retirer_accents(nom) pour que "paracetamol" trouve "Paracétamol"
    resultats = Stock.objects.filter(
        medicament__cle_recherche__icontains=retirer_accents(nom),
        quantite_disponible__gt=0,
        pharmacie__est_verifiee=True,
    ).select_related("pharmacie", "medicament")

    donnees = []
    for stock in resultats:
        position_pharmacie = (float(stock.pharmacie.latitude), float(stock.pharmacie.longitude))
        distance_km = geodesic((lat_patient, lng_patient), position_pharmacie).km

        # chemin relatif -> URL complète, sinon l'image casse selon la page qui l'affiche
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
            "sur_ordonnance": stock.medicament.est_sur_ordonnance,  # pour afficher le champ photo côté front
        })

    donnees.sort(key=lambda d: d["distance_km"])  # plus proche en premier

    return Response(donnees)


@login_required
def tableau_de_bord(request):
    """Espace pharmacien : stocks + commandes."""
    pharmacie = Pharmacie.objects.filter(compte_gestionnaire=request.user).first()
    if pharmacie is None:
        messages.error(request, "Votre compte ne gère aucune pharmacie pour le moment.")
        return redirect("accueil")

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "maj_stock":
            stock = get_object_or_404(Stock, pk=request.POST.get("stock_id"), pharmacie=pharmacie)
            stock.quantite_disponible = int(request.POST.get("quantite_disponible", stock.quantite_disponible))
            stock.prix_unitaire_gnf = int(request.POST.get("prix_unitaire_gnf", stock.prix_unitaire_gnf))
            stock.save()
            messages.success(request, f"Stock de « {stock.medicament} » mis à jour.")

        elif action == "ajouter_stock":
            # get_or_create : si la ligne existe déjà on la met juste à jour plutôt que planter
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
            # on remet la quantité au stock, la commande n'aura pas lieu
            commande.stock.quantite_disponible += commande.quantite
            commande.stock.save(update_fields=["quantite_disponible"])
            commande.statut = "annulee"
            commande.save(update_fields=["statut"])
            envoyer_notification_statut(commande)
            messages.success(request, f"Commande #{commande.pk} refusée, stock restitué.")

        elif action == "marquer_preparee":
            # scellé = preuve que le colis n'a pas été ouvert avant la remise
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
            # que pour le mode livraison - un retrait passe direct de préparée à livrée
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

        return redirect("tableau_de_bord")  # évite le renvoi du formulaire si F5

    stocks = pharmacie.stocks.select_related("medicament").order_by("medicament__nom_commercial")
    medicaments_deja_references = stocks.values_list("medicament_id", flat=True)
    medicaments_disponibles = Medicament.objects.exclude(pk__in=medicaments_deja_references)

    # rupture ou stock faible en premier, pour pas que ça se perde dans le tableau complet
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
