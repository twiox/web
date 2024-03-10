from members.models import Event, Message
from django.shortcuts import render
from django.views.generic import DetailView
from django.contrib.auth.mixins import UserPassesTestMixin
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


urlpatterns = [
    path("get-section", get_section, name="get_event_section"),
    path("<int:pk>", EventDetailView.as_view(), name="get_event_detail"),
]
