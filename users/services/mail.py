import logging

from django.conf import settings
from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)


def send_contact_mail(instance):
    email_body = (
        "Neue Kontaktanfrage\n\n"
        f"Vorname: {instance.first_name}\n"
        f"Nachname: {instance.last_name}\n"
        f"E-Mail: {instance.email}\n"
        f"Telefon: {getattr(instance, 'phone', '')}\n\n"
        "Nachricht:\n"
        "----------------\n"
        f"{instance.message}"
    )

    try:
        email = EmailMessage(
            subject=f"Kontaktanfrage von {instance.first_name} {instance.last_name}",
            body=email_body,
            from_email=settings.EMAIL_HOST_USER,
            to=[
                "info@hi-pkvgmbh.de",
                "info@js-webdesigns.de",
            ],
        )

        email.send(fail_silently=False)
        logger.info("Kontakt-Mail erfolgreich versendet")

    except Exception:
        logger.exception("Kontakt-Mail Versand fehlgeschlagen")
