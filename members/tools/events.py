from members.models import Event, Message, Participant
from members.forms import EventForm
from members.tools import emails
from django.shortcuts import render
from django.views.generic import DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.urls import path
from django.db.models import Q
import itertools
import locale
from datetime import datetime, timedelta
from collections import defaultdict
import json


def permission_check_2(user):
    try:
        return user.profile.permission_level > 2
    except AttributeError:  # anonymous user
        return False


def get_section(request):
    locale.setlocale(locale.LC_TIME, "de_DE")
    ddate = datetime.today() + timedelta(days=7)  # show older events for 1 more week

    # query for events that happen in the next year
    q = Event.objects.filter(Q(start_date__gte=ddate) & Q(deleted=False))

    nested_dict = lambda: defaultdict(nested_dict)
    events = nested_dict()

    for key, entries in itertools.groupby(q, lambda x: x.start_date.strftime("%B-%Y")):
        month, year = key.split("-")
        # add the entries for a year and a month to the dict
        events[year][month] = list(entries)

    messages = Message.objects.filter(display="events").distinct()

    context = {
        "events": events,
        "messages": messages,
    }

    return render(request, "sections/event_section.html", context)


#
#
# For the detail-view
#
#


def event_test_func(request, event):
    # members can see all events, otherwise if public event
    return any([request.user.is_authenticated, event.public_event])


class EventDetailView(UserPassesTestMixin, DetailView):
    template_name = "pages/event_detail.html"
    model = Event

    def test_func(self):
        event = self.get_object()
        return event_test_func(self.request, event)


#
#
# The Event Form
#
#


@user_passes_test(permission_check_2)
def toggle_delete(request):
    object = Event.objects.get(pk=int(request.GET.get("id")))
    object.deleted = object.deleted == False  # toggle the deletion
    object.save()
    return render(request, "snippets/events/event_header.html", {"event": object})


class EventCreateView(UserPassesTestMixin, CreateView):
    # template: event_detail.html
    model = Event
    form_class = EventForm
    template_name = "pages/event_form.html"

    def test_func(self):
        try:
            return self.request.user.profile.permission_level > 2
        except AttributeError:
            return False


class EventUpdateView(UserPassesTestMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = "pages/event_form.html"

    def test_func(self):
        try:
            return self.request.user.profile.permission_level > 2
        except AttributeError:
            return False


@user_passes_test(permission_check_2)
def add_question(request):
    object = Event.objects.get(pk=int(request.POST.get("id")))
    questions = (
        json.loads(object.questions) if object.questions else {}
    )  # get the (empty) questions json
    newkey = (
        max([int(x) for x in questions.keys()]) + 1 if len(questions.keys()) > 0 else 1
    )  # define a new key

    questions[newkey] = (
        request.POST.get("question"),
        request.POST.get("question_type"),
    )
    object.questions = json.dumps(questions)
    object.save()

    return render(
        request,
        "snippets/events/event_questions.html",
        {"event": object},
    )


@user_passes_test(permission_check_2)
def remove_question(request):
    object = Event.objects.get(pk=int(request.POST.get("id")))
    questions = json.loads(object.questions)

    del questions[request.POST.get("removekey")]

    object.questions = json.dumps(questions)
    object.save()

    return render(
        request,
        "snippets/events/event_questions.html",
        {"event": object},
    )


#
#
# Participant views
#
#


class ParticipantCreateView(CreateView):
    template_name = "pages/participant_form.html"
    model = Participant
    fields = "__all__"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["event"] = Event.objects.get(pk=int(self.kwargs["pk"]))
        return super().get_context_data(**context)

    def form_valid(self, form):
        self.object = form.save()
        answers = {
            x: self.request.POST.get(x)
            for x in self.request.POST
            if x[0] in "0123456789"
        }
        # translate the checkbox 'on' to 'Ja'
        answers = {k: "Ja" if v == "on" else v for k, v in answers.items()}
        self.object.answers = json.dumps(answers)
        self.object.save()

        # send the email
        emails.send_participant_email(self.object)

        # send message
        messages.add_message(
            self.request, messages.SUCCESS, "Du hast dich erfolgreich angemeldet"
        )

        return super().form_valid(form)


#
def participant_delete(request, pk):
    event = Event.objects.get(pk=int(pk))
    user = request.user
    part = Participant.objects.filter(user=user, event=event).first()
    part.delete()
    return render(request, "snippets/events/event_header.html", {"event": event})


urlpatterns = [
    path("get-section", get_section, name="get_event_section"),
    path("<int:pk>", EventDetailView.as_view(), name="get_event_detail"),
    path("delete_toggle", toggle_delete, name="event_delete_toggle"),
    path("neu/", EventCreateView.as_view(), name="event_create"),
    path("<int:pk>/update", EventUpdateView.as_view(), name="event_update"),
    path("add-question", add_question, name="event_add_question"),
    path("remove-question", remove_question, name="event_remove_question"),
    path("<int:pk>/anmelden", ParticipantCreateView.as_view(), name="event_register"),
    path("<int:pk>/abmelden", participant_delete, name="event_deregister"),
]
