from members.models import Session, Message
from django.shortcuts import render
from django.urls import path


def get_section(request):
    sessions = Session.objects.all()
    training_messages = Message.objects.filter(display="sessions").distinct()

    session_days = sorted(
        list(set([(x.day, x.weekday, x.order) for x in sessions])), key=lambda x: x[2]
    )
    # group sessions by day and pack into dict
    grouped_sessions = {}
    for short, day, order in session_days:
        grouped_sessions[short] = sessions.filter(day=short).order_by("start_time")

    context = {
        "sessions": grouped_sessions,
        "session_days": session_days,
        "messages": training_messages,
    }

    return render(request, "sections/training_section.html", context)


urlpatterns = [
    path("get-section", get_section, name="get_training_section"),
]
