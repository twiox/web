from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string


def send_email(subject, message, to):
    subject = f"Twio X e.V. | {subject}"
    email = EmailMessage(subject, message, to=[to], cc=[settings.TO_EMAIL])
    email.send()
    return True


#
#
# Event registration
#
#


def send_participant_email(participant):
    subject = f"Anmeldung Veranstaltung: {participant.get_first_name} {participant.get_last_name}"
    message = render_to_string(
        "emails/participation_email.html",
        {
            "participant": participant,
            "event": participant.event,
        },
    )
    to = participant.get_email
    return send_email(subject, message, to)


#
#
# Probetraining
#
#


def send_trial_email(tester):
    subject = f"Anmeldung Probetraining: {tester.first_name} {tester.last_name}"
    message = render_to_string(
        "emails/trial_registration_email.html",
        {
            "tester": tester,
        },
    )
    to = tester.email
    return send_email(subject, message, to)
