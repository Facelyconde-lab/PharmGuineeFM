import requests
from django.conf import settings


def _envoyer_email(destinataire, sujet, corps):
    # PythonAnywhere gratuit bloque le SMTP par intermittence (pare-feu figé sur
    # des IP Gmail qui bougent côté Google - vu en prod, cf help.pythonanywhere.com/
    # pages/SMTPForFreeUsers). Donc Brevo en HTTPS si la clé est là, sinon backend
    # console de Django (juste affiché dans le terminal, pratique en local).
    if settings.BREVO_API_KEY:
        try:
            reponse = requests.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={
                    "api-key": settings.BREVO_API_KEY,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json={
                    "sender": {
                        "name": "PharmaSila Guinée",
                        "email": settings.BREVO_SENDER_EMAIL,
                    },
                    "to": [{"email": destinataire}],
                    "subject": sujet,
                    "textContent": corps,
                },
                timeout=10,
            )
            if reponse.status_code >= 300:
                # log seulement, on bloque jamais la commande pour un souci d'email
                print(f"[Brevo] Échec envoi à {destinataire} : {reponse.status_code} {reponse.text}")
        except requests.RequestException as erreur:
            print(f"[Brevo] Exception lors de l'envoi à {destinataire} : {erreur}")
    else:
        from django.core.mail import send_mail
        send_mail(
            subject=sujet,
            message=corps,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[destinataire],
            fail_silently=True,
        )


def envoyer_notification_statut(commande):
    """Email au patient à chaque changement de statut."""
    patient = commande.patient

    # comptes créés avant l'ajout du champ email obligatoire -> peuvent ne pas en avoir
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
        return  # en_attente par ex, pas de notif prévue pour ce statut

    _envoyer_email(
        destinataire=patient.email,
        sujet=f"PharmaSila — Commande #{commande.pk} : {commande.get_statut_display()}",
        corps=corps,
    )


def envoyer_notification_annulation_patient(commande):
    """Email à la pharmacie quand c'est le patient qui annule (pas elle) - pour qu'elle ne prépare pas la commande pour rien."""
    gestionnaire = commande.stock.pharmacie.compte_gestionnaire
    if not gestionnaire or not gestionnaire.email:
        return

    medicament = commande.stock.medicament.nom_commercial
    corps = (
        f"Le patient {commande.patient.username} a annulé sa commande de {medicament} "
        f"(commande #{commande.pk}). Le stock a été remis à disposition automatiquement, "
        f"rien à faire de ton côté."
    )
    _envoyer_email(
        destinataire=gestionnaire.email,
        sujet=f"PharmaSila — Commande #{commande.pk} annulée par le patient",
        corps=corps,
    )
