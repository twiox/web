from members.models import Event, Message
from django.shortcuts import render
from django.urls import path
import itertools
import locale
from datetime import datetime, timedelta
from collections import defaultdict


def get_section(request):
    locale.setlocale(locale.LC_TIME, "de_DE")
    ddate = datetime.today() + timedelta(days=7)  # show older events for 1 more week

    # query for events that happen in the next year
    q = Event.objects.filter(start_date__gte=ddate)

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


urlpatterns = [
    path("get-section", get_section, name="get_event_section"),
]
