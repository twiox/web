from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import (CreateView, UpdateView, DeleteView)
from django.contrib import messages
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from .forms import ProbetrainingForm
from members.models import Chairman
from .models import Teamer


def interested_index(request):
    chairmen = Chairman.objects.filter(show__contains="interested_site")

    if (request.method == "POST"):
        form = ProbetrainingForm(request.POST)  # if no files
        if form.is_valid():
            # get Form data
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            birthdate = form.cleaned_data.get('birth_date')
            int_email = form.cleaned_data.get('email')
            telnr = form.cleaned_data.get('telephone')
            city = form.cleaned_data.get('city')
            notes = form.cleaned_data.get('notes')

            mail_subject = f'Anfrage Probetraining von {first_name} {last_name}'
            message = render_to_string('interested/probe_email.html', {
                "first_name": first_name,
                "last_name": last_name,
                "birthdate": birthdate,
                "email": int_email,
                "telnr": telnr,
                "city": city,
                "notes": notes,
                }
                                       )
            email = EmailMessage(mail_subject, message, to=[settings.TO_EMAIL])
            email.send()
            # And the message to the interested
            message2 = render_to_string("interested/probe_email_answer.html", {
                "first_name": first_name,
                "last_name": last_name
                }
            )
            EmailMessage(f"Twio X e.V. - Deine Anfrage auf Probetraining", message2, to=[int_email]).send()
            messages.add_message(request, messages.SUCCESS, 'Anmeldung verschickt')
            return HttpResponseRedirect("")
        else:
            return render(request, "interested/interested_index.html", {"form": form, "chairmen": chairmen})
    form = ProbetrainingForm()
    return render(request, "interested/interested_index.html", {"form": form, "chairmen": chairmen})


def interested_offers(request):
    if (request.method == "POST"):
        form = ProbetrainingForm(request.POST)  # if no files
        if form.is_valid():
            messages.add_message(request, messages.SUCCESS, 'Workshopanfrage verschickt')
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            birthdate = form.cleaned_data.get('birth_date')
            int_email = form.cleaned_data.get('email')
            telnr = form.cleaned_data.get('telephone')
            city = form.cleaned_data.get('city')
            notes = form.cleaned_data.get('notes')

            mail_subject = f"Anfrage Workshop von {first_name} {last_name}"
            message = render_to_string("interested/workshop_email.html", {
                "first_name": first_name,
                "last_name": last_name,
                "birthdate": birthdate,
                "email": int_email,
                "telnr": telnr,
                "city": city,
                "notes": notes,
                }
            )
            email = EmailMessage(mail_subject, message, to=[settings.TO_EMAIL])
            email.send()
            # And the message to the interested
            message2 = render_to_string("interested/workshop_email_answer.html", {
                "first_name": first_name,
                "last_name": last_name
                }
            )
            EmailMessage(f"Twio X e.V. - Deine Workshopanfrage", message2, to=[int_email]).send()
            return HttpResponseRedirect("")

        else:
            return render(request, "interested/interested_offers.html", {"form": form})
    form = ProbetrainingForm()
    return render(request, "interested/interested_offers.html", {"form": form})


def interested_philosophy(request):
    return render(request, "interested/interested_philosophy.html", {})


def interested_team(request):
    jena_people = Teamer.objects.filter(city__contains="jena")
    leipzig_people = Teamer.objects.filter(city__contains="leipzig")
    return render(request, "interested/interested_team.html",
                  {"leipzig_people": leipzig_people, "jena_people": jena_people})


class TeamerLeipzigCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Teamer
    fields = ["priority", "picture", "name", "position", "notes", "public_telnr", "public_email"]
    permission_required = 'interested.add_teamer'

    def form_valid(self, form):
        teamer = form.save()
        teamer.city = "leipzig"
        teamer.save()
        messages.add_message(self.request, messages.SUCCESS, 'Neues Teammitglied erstellt')
        return super(TeamerLeipzigCreateView, self).form_valid(form)


class TeamerJenaCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Teamer
    fields = ["priority", "picture", "name", "position", "notes", "public_telnr", "public_email"]
    permission_required = 'interested.add_teamer'

    def form_valid(self, form):
        teamer = form.save()
        teamer.city = "jena"
        teamer.save()
        messages.add_message(self.request, messages.SUCCESS, 'Neues Teammitglied erstellt')
        return super(TeamerJenaCreateView, self).form_valid(form)


class TeamerUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Teamer
    fields = ["priority", "picture", "name", "position", "notes", "public_telnr", "public_email"]
    permission_required = 'interested.change_teamer'

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, 'Teammitglied erfolgreich aktualisiert')
        return super(TeamerUpdateView, self).form_valid(form)


class TeamerDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Teamer
    success_url = "/interested/team"
    permission_required = 'interested.delete_teamer'

    def post(self, request, *args, **kwargs):
        messages.add_message(request, messages.SUCCESS, 'Teammitglied gelöscht')
        return self.delete(request, *args, **kwargs)
