from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string


def send_email(subject, message, to):
    subject = f"Twio X e.V. | {subject}"
    email = EmailMessage(subject, message, to=[to], cc=[settings.TO_EMAIL])
    email.send()
    return True


def send_participant_email(participant):
    subject = f"Anmeldung Veranstaltung"
    message = render_to_string(
        "emails/participation_email.html",
        {
            "participant": participant,
            "event": participant.event,
        },
    )
    to = participant.get_email
    return send_email(subject, message, to)
