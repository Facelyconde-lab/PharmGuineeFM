import itertools
from datetime import timedelta

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.sessions.models import Session
from django.db import transaction
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from commandes.models import Commande
from commandes.notifications import envoyer_notification_annulation_patient
from pharmacies.models import Pharmacie, Stock
from .forms import InscriptionForm
from .models import VisiteRecherche

# le patient peut annuler lui-même sa commande tant que la pharmacie ne l'a pas
# encore validée ET que ce délai n'est pas dépassé - passé ça, la pharmacie a
# probablement déjà commencé à s'organiser, on ne veut pas la mettre en porte-à-faux
DELAI_ANNULATION_PATIENT = timedelta(hours=1)


def inscription(request):
    if request.method == "POST":
        formulaire = InscriptionForm(request.POST)
        if formulaire.is_valid():
            utilisateur = formulaire.save()
            login(request, utilisateur)  # connecté direct, pas besoin de se reconnecter juste après
            return redirect("accueil")
    else:
        formulaire = InscriptionForm()
    return render(request, "patients/inscription.html", {"formulaire": formulaire})


def connexion(request):
    if request.method == "POST":
        formulaire = AuthenticationForm(request, data=request.POST)
        if formulaire.is_valid():
            login(request, formulaire.get_user())
            return redirect("accueil")
    else:
        formulaire = AuthenticationForm()
    return render(request, "patients/connexion.html", {"formulaire": formulaire})


def deconnexion(request):
    logout(request)
    return redirect("accueil")


@login_required
def mes_commandes(request):
    """Historique des commandes du patient - suivi sans dépendre que de l'email."""
    commandes = (
        Commande.objects.filter(patient=request.user)
        .select_related("stock__pharmacie", "stock__medicament")
        .order_by("-date_creation")
    )
    # un panier validé d'un coup crée plusieurs Commande (une par produit) qui
    # partagent le même groupe_commande -> on les regroupe ici pour les afficher
    # comme une seule commande à plusieurs lignes plutôt que N réservations
    # séparées. groupby marche seulement sur des éléments déjà côte à côte, ce
    # qui est le cas ici : les lignes d'un même panier sont créées à la suite,
    # donc adjacentes une fois triées par -date_creation.
    groupes = [
        {"id": cle, "lignes": list(lignes)}
        for cle, lignes in itertools.groupby(commandes, key=lambda c: c.groupe_commande)
    ]

    # annulable = pas encore validée par la pharmacie + toujours dans le délai -
    # calculé ici plutôt que dans le template, une comparaison de date c'est plus
    # simple à lire en Python que dans le langage de template Django
    maintenant = timezone.now()
    for groupe in groupes:
        for ligne in groupe["lignes"]:
            ligne.annulable = (
                ligne.statut == "en_attente"
                and maintenant - ligne.date_creation <= DELAI_ANNULATION_PATIENT
            )

    return render(request, "patients/mes_commandes.html", {"groupes": groupes})


@login_required
@require_POST
def annuler_commande(request, commande_id):
    """Le patient annule lui-même une commande précise (un seul produit du panier, pas forcément tout le groupe)."""
    commande = get_object_or_404(Commande, pk=commande_id, patient=request.user)

    delai_depasse = timezone.now() - commande.date_creation > DELAI_ANNULATION_PATIENT
    if commande.statut != "en_attente" or delai_depasse:
        messages.error(
            request,
            "Cette commande ne peut plus être annulée (déjà prise en charge par la "
            "pharmacie, ou plus d'une heure s'est écoulée depuis la réservation).",
        )
        return redirect("patients:mes_commandes")

    # même verrou que pour une réservation : évite qu'un double-clic ou une
    # requête concurrente ne remette le stock en double
    with transaction.atomic():
        stock = Stock.objects.select_for_update().get(pk=commande.stock_id)
        stock.quantite_disponible += commande.quantite
        stock.save(update_fields=["quantite_disponible"])

        commande.statut = "annulee"
        commande.save(update_fields=["statut"])

    envoyer_notification_annulation_patient(commande)
    messages.success(request, "Ta commande a été annulée, le produit est de nouveau disponible.")
    return redirect("patients:mes_commandes")


@staff_member_required
def visiteurs(request):
    """Page staff : qui utilise le site - comptes créés, connectés maintenant, recherches."""
    Utilisateur = get_user_model()
    tous_comptes = Utilisateur.objects.all()

    # comptes créés, par catégorie
    total_comptes = tous_comptes.count()
    ids_pharmaciens = set(
        Pharmacie.objects.exclude(compte_gestionnaire=None).values_list(
            "compte_gestionnaire_id", flat=True
        )
    )
    total_staff = tous_comptes.filter(is_staff=True).count()
    total_pharmaciens = len(ids_pharmaciens)
    total_patients = total_comptes - total_staff - total_pharmaciens

    # connecté "maintenant" : pas de websocket ici, donc on prend les sessions
    # Django encore valides (pas expirées) et on regarde celles qui portent un
    # utilisateur connecté. C'est une approximation, "valide" ne veut pas dire
    # "en train de cliquer à la seconde près", mais c'est ce que Django permet
    # de savoir sans ajouter un système de présence à part.
    sessions_actives = Session.objects.filter(expire_date__gte=timezone.now())
    ids_connectes = set()
    for session in sessions_actives:
        id_utilisateur = session.get_decoded().get("_auth_user_id")
        if id_utilisateur:
            ids_connectes.add(int(id_utilisateur))

    utilisateurs_connectes = []
    for utilisateur in tous_comptes.filter(pk__in=ids_connectes):
        if utilisateur.is_staff:
            role = "Ministère / staff"
        elif utilisateur.pk in ids_pharmaciens:
            role = "Pharmacien"
        else:
            role = "Patient"
        utilisateurs_connectes.append({"utilisateur": utilisateur, "role": role})

    # recherches, connectées vs anonymes
    total_recherches = VisiteRecherche.objects.count()
    recherches_connectees = VisiteRecherche.objects.filter(patient__isnull=False).count()
    recherches_anonymes = total_recherches - recherches_connectees
    # distinct session_key = un visiteur anonyme qui cherche 5 fois compte pour 1, pas 5
    visiteurs_anonymes_uniques = (
        VisiteRecherche.objects.filter(patient__isnull=True)
        .exclude(session_key="")
        .values("session_key")
        .distinct()
        .count()
    )

    # bonus : tendance des recherches sur 7 jours, pour voir d'un coup d'oeil
    # si le trafic monte ou baisse (même logique que les graphes du tableau
    # de bord ministère)
    aujourdhui = timezone.localdate()
    tendance_recherches = []
    for decalage in range(6, -1, -1):
        jour = aujourdhui - timezone.timedelta(days=decalage)
        tendance_recherches.append({
            "jour": jour.strftime("%d/%m"),
            "total": VisiteRecherche.objects.filter(date_creation__date=jour).count(),
        })

    # bonus : nouveaux comptes sur 7 jours, pour suivre si les patients
    # s'inscrivent réellement plutôt que juste chercher sans compte
    nouveaux_comptes_7j = tous_comptes.filter(
        date_joined__date__gte=aujourdhui - timezone.timedelta(days=6)
    ).count()

    contexte = {
        "total_comptes": total_comptes,
        "total_patients": total_patients,
        "total_pharmaciens": total_pharmaciens,
        "total_staff": total_staff,
        "utilisateurs_connectes": utilisateurs_connectes,
        "total_recherches": total_recherches,
        "recherches_connectees": recherches_connectees,
        "recherches_anonymes": recherches_anonymes,
        "visiteurs_anonymes_uniques": visiteurs_anonymes_uniques,
        "tendance_recherches": tendance_recherches,
        "nouveaux_comptes_7j": nouveaux_comptes_7j,
    }
    return render(request, "patients/visiteurs.html", contexte)
