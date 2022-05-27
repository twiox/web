from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import permission_required
from django.views.generic import (CreateView, UpdateView, DeleteView, DetailView, ListView)
from django.contrib import messages
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from .forms import ProbetrainingForm, PublicEventForm
from members.models import Chairman
from .models import Teamer, PublicEvent, EventParticipant, EventMerch

def interested_index(request):
    chairmen = Chairman.objects.filter(show__contains="interested_site")
    public_events = [x for x in PublicEvent.objects.all() if not x.is_past_due]
    
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
            return HttpResponseRedirect(reverse("interested_index"))
        else:
            return render(request, "interested/interested_index.html", {"form": form, "chairmen": chairmen, 'public_events':public_events})
    form = ProbetrainingForm()
    return render(request, "interested/interested_index.html", {"form": form, "chairmen": chairmen,'public_events':public_events})


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
            return HttpResponseRedirect(reverse("offers"))

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
    permission_required = 'interested.delete_teamer'

    def post(self, request, *args, **kwargs):
        messages.add_message(request, messages.SUCCESS, 'Teammitglied gelöscht')
        return self.delete(request, *args, **kwargs)
        
    def get_success_url(self):
        return reverse("team")+"#nav" 


class PublicEventCreateView(PermissionRequiredMixin, CreateView):
    model = PublicEvent
    permission_required = "interested_add_publicevent"
    fields = "__all__"
    template_name = "interested/publicevent_form.html"


class PublicEventView(DetailView):
    model = PublicEvent
    slug_url_kwarg = 'event_slug'
    slug_field = 'slug' # DetailView's default value: optional
    form_class = PublicEventForm

    def get_context_data(self, **kwargs):
        context = super(PublicEventView, self).get_context_data(**kwargs)
        context['event'] = self.get_object()
        merch = EventMerch.objects.filter(event=self.get_object())
        if merch:
            merch = merch.all()[0]
            context['sizes'] = [x for x in merch.sizes.split("\t")]
        else:
            context['sizes'] = []
        context['merch'] = merch
        return context

    def post(self, request, *args, **kwargs):
        form = PublicEventForm(request.POST)
        event = self.get_object()
        self.object = event
        context = super(PublicEventView, self).get_context_data(**kwargs)
        merch = merch = EventMerch.objects.filter(event=event).first()

        if form.is_valid():
            participant = EventParticipant(
                event=event,
                first_name=form.cleaned_data.get('first_name'),
                last_name = form.cleaned_data.get('last_name'),
                birthday = form.cleaned_data.get('birthday'),
                email = form.cleaned_data.get('email'),
                phone = form.cleaned_data.get('phone'),
                contact  = form.cleaned_data.get('contact'),
                invoice = float(form.cleaned_data.get('costs')),
                merch_wanted = form.cleaned_data.get('merch_wanted'),
                merch_size = form.cleaned_data.get('merch_size'),
                notes=""
            )
            participant.save()
            mail_subject = f"Twio X e.V. | {event.title}: Anmeldebestätigung"
            mail_subject2 = f"Anmeldung: {event.title}: {participant.first_name} {participant.last_name}"
            message = render_to_string("interested/public_event_confirmation_email.html", {
                "first_name": participant.first_name,
                "last_name": participant.last_name,
                "birthdate": participant.birthday,
                "email": participant.email,
                "telnr": participant.phone,
                "title": event.title,
                "start_date": event.start_date,
                "end_date": event.end_date,
                "contact": participant.contact,
                "merch": True if participant.merch_wanted else False,
                "merch_title": merch.title if merch else None,
                "merch_size": participant.merch_size,
                "costs": participant.invoice,
                }
            )
            email = EmailMessage(mail_subject2, message, to=[settings.TO_EMAIL])
            email2 = EmailMessage(mail_subject, message, to=[participant.email])
            #email.send()
            #email2.send()
            
            messages.add_message(request, messages.SUCCESS, 'Du hast dich erfolgreich angemeldet')
            context['form'] = PublicEventForm
            return self.render_to_response(context=context)

        else:
            context['form'] = form
            return self.render_to_response( context=context)


@permission_required("interested_change_eventparticipant")
def event_participant_list_view(request, event_slug):
    event = PublicEvent.objects.get(slug=event_slug)
    object_list = EventParticipant.objects.filter(event=event)
    return render(request, "interested/eventparticipant_list.html", {"object_list":object_list, "event": event})


class EventParticipantDeleteView(PermissionRequiredMixin, DeleteView):
    model=EventParticipant
    permission_required="interested_remove_eventparticipant"
    
    def get_success_url(self, **kwargs):
        slug = self.get_object().event.slug
        messages.add_message(self.request, messages.SUCCESS, 'Teilnehmer*in erfolgreich gelöscht')
        return reverse("event_participant_list", kwargs={'event_slug':slug})

class EventParticipantUpdateView(PermissionRequiredMixin, UpdateView):
    model=EventParticipant
    permission_required="interested_change_eventparticipant"
    template_name = "interested/eventparticipant_form_update.html"
    fields = ["first_name", "last_name", "birthday", "email", "phone", "contact", "invoice", "payed", "merch_wanted", "merch_size", "notes"]
    
    def get_success_url(self, **kwargs):
        slug = self.get_object().event.slug
        messages.add_message(self.request, messages.SUCCESS, 'Teilnehmer*in erfolgreich geändert')
        return reverse("event_participant_list", kwargs={'event_slug':slug})


class PublicEventDeleteView(PermissionRequiredMixin, DeleteView):
    model = PublicEvent
    permission_required = "interested_publicevent_delete"
    
    def get_success_url(self, **kwargs):
        slug = self.get_object().slug
        messages.add_message(self.request, messages.SUCCESS, 'Veranstaltung erfolgreich gelöscht')
        return reverse("interested_index")
    

class PublicEventUpdateView(PermissionRequiredMixin, UpdateView):
    model = PublicEvent
    permission_required="interested_change_eventparticipant"
    fields = "__all__"
    
    def get_success_url(self, **kwargs):
        slug = self.get_object().slug
        messages.add_message(self.request, messages.SUCCESS, 'Veranstaltung erfolgreich geändert')
        return reverse("public_event", kwargs={'event_slug':slug})
    

class EventMerchCreateView(PermissionRequiredMixin, CreateView):
    model = EventMerch
    permission_required = "interested_change_eventmerch"
    fields = "__all__"
    
    def form_valid(self, form):
        self.object = form.save()
        return super().form_valid(form)
    
    def get_success_url(self, **kwargs):
        messages.add_message(self.request, messages.SUCCESS, 'Merch erfolgreich hinzugefügt')
        return reverse("public_event_change", kwargs={'pk':self.object.event.pk})

class EventMerchUpdateView(PermissionRequiredMixin, UpdateView):
    model = EventMerch
    permission_required = "interested_change_eventmerch"
    fields = "__all__"

    def get_success_url(self, **kwargs):
        event_pk = self.get_object().event.pk
        messages.add_message(self.request, messages.SUCCESS, 'Merch erfolgreich geändert')
        return reverse("public_event_change", kwargs={'pk':event_pk})

class EventMerchDeleteView(PermissionRequiredMixin, DeleteView):
    model = EventMerch
    permission_required = "interested_change_eventmerch"
    
    def get_success_url(self, **kwargs):
        event_pk = self.get_object().event.pk
        messages.add_message(self.request, messages.SUCCESS, 'Merch erfolgreich gelöscht')
        return reverse("public_event_change", kwargs={'pk':event_pk})
    


