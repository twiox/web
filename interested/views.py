from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from django.contrib.auth.decorators import permission_required
from django.views.generic import (
    CreateView,
    UpdateView,
    DeleteView,
    DetailView,
    ListView,
)
from django.contrib import messages
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from .forms import ProbetrainingForm
from members.models import Chairman
from .models import Tester
from members.views import chairman_check, trainer_check


def interested_index(request):
    chairmen = Chairman.objects.filter(show__contains="interested_site")

    if request.method == "POST":
        form = ProbetrainingForm(request.POST)  # if no files
        if form.is_valid():
            # get Form data
            test = form.save()
            test.save()

            mail_subject = (
                f"Anfrage Probetraining von {test.first_name} {test.last_name}"
            )
            message = render_to_string(
                "interested/probe_email.html",
                {
                    "object": test,
                },
            )
            email = EmailMessage(mail_subject, message, to=[settings.TO_EMAIL])
            email.send()
            # And the message to the interested
            message2 = render_to_string(
                "interested/probe_email_answer.html",
                {
                    "object": test,
                },
            )
            EmailMessage(
                f"Twio X e.V. - Deine Anfrage auf Probetraining",
                message2,
                to=[test.email],
            ).send()
            messages.add_message(request, messages.SUCCESS, "Anmeldung verschickt")
            return HttpResponseRedirect(reverse("interested_index"))
        else:
            return render(
                request,
                "interested/interested_index.html",
                {"form": form, "chairmen": chairmen, "public_events": public_events},
            )
    form = ProbetrainingForm()
    return render(
        request,
        "interested/interested_index.html",
        {"form": form, "chairmen": chairmen, "public_events": public_events},
    )


def interested_offers(request):
    if request.method == "POST":
        form = ProbetrainingForm(request.POST)  # if no files
        if form.is_valid():
            messages.add_message(
                request, messages.SUCCESS, "Workshopanfrage verschickt"
            )
            first_name = form.cleaned_data.get("first_name")
            last_name = form.cleaned_data.get("last_name")
            birthdate = form.cleaned_data.get("birth_date")
            int_email = form.cleaned_data.get("email")
            telnr = form.cleaned_data.get("telephone")
            city = form.cleaned_data.get("city")
            notes = form.cleaned_data.get("notes")

            mail_subject = f"Anfrage Workshop von {first_name} {last_name}"
            message = render_to_string(
                "interested/workshop_email.html",
                {
                    "first_name": first_name,
                    "last_name": last_name,
                    "birthdate": birthdate,
                    "email": int_email,
                    "telnr": telnr,
                    "city": city,
                    "notes": notes,
                },
            )
            email = EmailMessage(mail_subject, message, to=[settings.TO_EMAIL])
            email.send()
            # And the message to the interested
            message2 = render_to_string(
                "interested/workshop_email_answer.html",
                {"first_name": first_name, "last_name": last_name},
            )
            EmailMessage(
                f"Twio X e.V. - Deine Workshopanfrage", message2, to=[int_email]
            ).send()
            return HttpResponseRedirect(reverse("offers"))

        else:
            return render(request, "interested/interested_offers.html", {"form": form})
    form = ProbetrainingForm()
    return render(request, "interested/interested_offers.html", {"form": form})


def interested_philosophy(request):
    return render(request, "interested/interested_philosophy.html", {})


class TesterListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Tester

    def test_func(self):
        return chairman_check(self.request)
