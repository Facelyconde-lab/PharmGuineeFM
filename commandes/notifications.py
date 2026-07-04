import requests
from django.conf import settings


def _envoyer_email(destinataire, sujet, corps):
    """
    Envoie un email au patient.

    Pourquoi deux chemins possibles : les comptes gratuits PythonAnywhere
    bloquent le SMTP de façon intermittente (leur pare-feu code en dur les
    IP des serveurs Gmail, qui changent parfois côté Google — voir
    help.pythonanywhere.com/pages/SMTPForFreeUsers). L'API Brevo fonctionne
    elle en HTTPS classique, toujours autorisé même sur un compte gratuit.

    - Si BREVO_API_KEY est renseignée (production) : on passe par l'API
      Brevo, une simple requête HTTPS.
    - Sinon (développement local) : on utilise le backend email standard de
      Django, qui affiche juste le message dans le terminal (backend
      "console"), pratique pour tester sans compte Brevo.
    """
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
                # On ne bloque jamais le traitement de la commande pour un
                # souci d'email : on se contente d'un message dans les logs
                # PythonAnywhere (onglet Web > Log files > error log).
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

    _envoyer_email(
        destinataire=patient.email,
        sujet=f"PharmaSila — Commande #{commande.pk} : {commande.get_statut_display()}",
        corps=corps,
    )
