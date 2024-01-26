from members.models import Event, Message
from django.shortcuts import render
from django.urls import path


def get_section(request):
    events = Event.objects.all()
    event_messags = Message.objects.filter(display="events").distinct()

    context = {
        "events": events.distinct(),
        "event_messags": event_messags,
    }

    return render(request, "events/event_section.html", context)


urlpatterns = [
    path("get-section", get_section, name="get_event_section"),
]
