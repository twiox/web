from members.models import Session, Message
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, UpdateView
from django.contrib.auth.decorators import login_required
from django.contrib import messages


def get_section(request):
    sessions = Session.objects.all()
    training_messages = Message.objects.filter(display="sessions").distinct()

    session_days = sorted(
        list(set([(x.day, x.weekday) for x in sessions])),
        key=lambda x: ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"].index(x[0]),
    )
    # group sessions by day and pack into dict
    grouped_sessions = {}
    for short, day in session_days:
        grouped_sessions[short] = sessions.filter(day=short).order_by("start_time")

    context = {
        "sessions": grouped_sessions,
        "session_days": session_days,
        "messages": training_messages,
    }

    return render(request, "sections/training_section.html", context)


@login_required
def toggle_participation(request, pk):
    session = Session.objects.get(pk=pk)
    user = request.user
    if user in session.participants.all():
        session.participants.remove(user)
        messages.add_message(
            request, messages.SUCCESS, "Du hast dich erfolgreich abgemeldet"
        )
    else:
        session.participants.add(user)
        messages.add_message(
            request, messages.SUCCESS, "Du hast dich erfolgreich angemeldet"
        )
    return redirect(session)


class SessionDetailView(LoginRequiredMixin, DetailView):
    model = Session
    template_name = "pages/session_detail.html"


class SessionUpdateView(LoginRequiredMixin, UpdateView):
    model = Session
    template_name = "pages/session_detail.html"
    fields = "__all__"


urlpatterns = [
    path("get-section", get_section, name="get_training_section"),
    path("<int:pk>", SessionDetailView.as_view(), name="session_detail"),
    path("<int:pk>/edit", SessionUpdateView.as_view(), name="session_update"),
    path("<int:pk>/toggle", toggle_participation, name="session_participation_toggle"),
]
