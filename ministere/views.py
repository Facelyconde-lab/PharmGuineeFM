from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.shortcuts import render

from commandes.models import Commande
from medicaments.models import Medicament
from pharmacies.models import Pharmacie, Stock


@staff_member_required
def tableau_de_bord(request):
    # is_staff plutôt qu'un nouveau champ : le ministère n'a besoin que de lecture,
    # pas de gérer des permissions fines, autant réutiliser le mécanisme staff de Django
    """Vue d'ensemble ministère : pénuries, tendances par quartier, médicaments critiques."""

    # vue d'ensemble
    total_pharmacies = Pharmacie.objects.filter(est_verifiee=True).count()
    total_medicaments = Medicament.objects.count()
    total_lignes_stock = Stock.objects.count()
    total_en_rupture = Stock.objects.filter(quantite_disponible=0).count()
    total_stock_faible = Stock.objects.filter(
        quantite_disponible__gt=0, quantite_disponible__lte=Stock.SEUIL_ALERTE_STOCK
    ).count()
    taux_rupture_global = (
        round(total_en_rupture / total_lignes_stock * 100, 1) if total_lignes_stock else 0
    )

    # pénuries par médicament (rupture dans plusieurs pharmacies = pas un cas isolé)
    penuries_par_medicament = (
        Medicament.objects.annotate(
            nb_pharmacies_total=Count(
                "stocks",
                filter=Q(stocks__pharmacie__est_verifiee=True),
                distinct=True,
            ),
            nb_pharmacies_rupture=Count(
                "stocks",
                filter=Q(
                    stocks__pharmacie__est_verifiee=True,
                    stocks__quantite_disponible=0,
                ),
                distinct=True,
            ),
        )
        .filter(nb_pharmacies_rupture__gt=0)
        .order_by("-nb_pharmacies_rupture")
    )

    # même chose mais sur le seuil d'alerte -> anticiper avant la rupture totale
    stocks_faibles_par_medicament = (
        Medicament.objects.annotate(
            nb_pharmacies_total=Count(
                "stocks",
                filter=Q(stocks__pharmacie__est_verifiee=True),
                distinct=True,
            ),
            nb_pharmacies_stock_faible=Count(
                "stocks",
                filter=Q(
                    stocks__pharmacie__est_verifiee=True,
                    stocks__quantite_disponible__gt=0,
                    stocks__quantite_disponible__lte=Stock.SEUIL_ALERTE_STOCK,
                ),
                distinct=True,
            ),
        )
        .filter(nb_pharmacies_stock_faible__gt=0)
        .order_by("-nb_pharmacies_stock_faible")
    )

    # tendances par quartier
    tendances_par_quartier = []
    for code_quartier, nom_quartier in Pharmacie.QUARTIERS:
        pharmacies_quartier = Pharmacie.objects.filter(
            quartier=code_quartier, est_verifiee=True
        )
        stocks_quartier = Stock.objects.filter(pharmacie__in=pharmacies_quartier)
        nb_lignes_stock = stocks_quartier.count()
        nb_ruptures = stocks_quartier.filter(quantite_disponible=0).count()
        tendances_par_quartier.append(
            {
                "quartier": nom_quartier,
                "nb_pharmacies": pharmacies_quartier.count(),
                "nb_lignes_stock": nb_lignes_stock,
                "nb_ruptures": nb_ruptures,
                "taux_rupture": (
                    round(nb_ruptures / nb_lignes_stock * 100, 1) if nb_lignes_stock else 0
                ),
            }
        )
    tendances_par_quartier.sort(key=lambda ligne: ligne["taux_rupture"], reverse=True)  # pires en premier

    # critique = sur ordonnance + en rupture dans au moins 2 officines -> sécurité + ampleur
    medicaments_critiques = [
        medicament
        for medicament in penuries_par_medicament
        if medicament.est_sur_ordonnance and medicament.nb_pharmacies_rupture >= 2
    ]

    # commandes par statut
    libelles_statuts = dict(Commande.STATUTS)
    commandes_par_statut = [
        {
            "statut": libelles_statuts.get(ligne["statut"], ligne["statut"]),
            "total": ligne["total"],
        }
        for ligne in Commande.objects.values("statut").annotate(total=Count("id")).order_by("-total")
    ]

    contexte = {
        "total_pharmacies": total_pharmacies,
        "total_medicaments": total_medicaments,
        "total_lignes_stock": total_lignes_stock,
        "total_en_rupture": total_en_rupture,
        "total_stock_faible": total_stock_faible,
        "taux_rupture_global": taux_rupture_global,
        "penuries_par_medicament": penuries_par_medicament,
        "stocks_faibles_par_medicament": stocks_faibles_par_medicament,
        "seuil_alerte_stock": Stock.SEUIL_ALERTE_STOCK,
        "tendances_par_quartier": tendances_par_quartier,
        "medicaments_critiques": medicaments_critiques,
        "commandes_par_statut": commandes_par_statut,
    }
    return render(request, "ministere/tableau_de_bord.html", contexte)
