from django.conf import settings
from django.core.mail import send_mail


def envoyer_notification_statut(commande):
    """
    Envoie un email au patient pour l'informer du nouveau statut de sa
    commande (validée, préparée, en livraison, livrée, refusée).

    fail_silently=True : si l'envoi échoue (mauvais identifiants SMTP,
    coupure réseau...), on ne veut surtout pas empêcher la pharmacie de
    traiter la commande. La notification est un "plus", pas une étape
    bloquante du parcours métier.
    """
    patient = commande.patient

    # Les comptes créés avant l'ajout du champ email obligatoire peuvent
    # ne pas en avoir. On ignore simplement l'envoi dans ce cas plutôt que
    # de planter la vue appelante.
    if not patient.email:
        return

    medicament = commande.stock.medicament.nom_commercial
    pharmacie = commande.stock.pharmacie.nom

    messages_par_statut = {
        "validee": (
            f"Bonne nouvelle : votre commande de {medicament} a été validée par "
            f"{pharmacie}. Elle est maintenant en cours de préparation."
        ),
        "preparee": (
            f"Votre commande de {medicament} chez {pharmacie} est prête et scellée "
            f"(numéro de scellé : {commande.numero_scelle})."
            + (
                " Elle va bientôt partir en livraison."
                if commande.mode_livraison == "livraison"
                else " Vous pouvez venir la retirer en pharmacie."
            )
        ),
        "en_livraison": (
            f"Votre commande de {medicament} est en cours de livraison depuis {pharmacie}."
        ),
        "livree": (
            f"Votre commande de {medicament} vous a bien été remise. "
            f"Merci d'avoir utilisé PharmaSila !"
        ),
        "annulee": (
            f"Votre commande de {medicament} chez {pharmacie} a été refusée par la "
            f"pharmacie. Aucun montant ne vous a été débité."
        ),
    }

    corps = messages_par_statut.get(commande.statut)
    if not corps:
        # Statut sans notification prévue (ex: "en_attente", juste après
        # la réservation) : on ne fait rien.
        return

    send_mail(
        subject=f"PharmaSila — Commande #{commande.pk} : {commande.get_statut_display()}",
        message=corps,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[patient.email],
        fail_silently=True,
    )
