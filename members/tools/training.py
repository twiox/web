from members.models import Session, Message, Tester
from members.forms import TrialForm
from members.tools import emails
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, UpdateView, CreateView, ListView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime


# Helper function
def get_session_age_hist(session):
    """
    Calculate a histogram of the ages of session participants on the fly
    """
    import matplotlib
    import matplotlib.pyplot as plt
    from members.models import calculate_age
    import base64
    from io import BytesIO

    matplotlib.use("Agg")

    x = [
        calculate_age(x)
        for x in session.participants.all().values_list("profile__birthday", flat=True)
    ]
    fig = plt.figure(figsize=(4, 3))
    ax = fig.add_subplot(111)

    plt.hist(x, color="#088eaa", bins=5)
    ax.set_title("Altersverteilung")
    ax.set_ylabel("Anzahl")
    ax.set_xlabel("Alter")

    # Be sure to only pick integer tick locations.
    plt.locator_params(axis="both", integer=True, tight=True)

    plt.tight_layout()

    stream = BytesIO()
    plt.savefig(stream, format="png", transparent=True)
    plt.close()

    return base64.b64encode(stream.getvalue()).decode()


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
    template_name = "pages/session_form.html"
    fields = [
        "title",
        "short",
        "hinweis",
        "trainer",
        "day",
        "min_age",
        "max_age",
        "start_time",
        "end_time",
        "spot",
    ]


class SessionCreateView(LoginRequiredMixin, CreateView):
    model = Session
    template_name = "pages/session_form.html"
    fields = [
        "title",
        "short",
        "hinweis",
        "trainer",
        "day",
        "min_age",
        "max_age",
        "start_time",
        "end_time",
        "spot",
    ]


def session_delete(request, pk):
    if request.user.profile.permission_level > 1:
        session = Session.objects.get(pk=pk)
        session.delete()
    return redirect("landing")


class TesterCreateView(CreateView):
    model = Tester
    form_class = TrialForm
    template_name = "pages/trial_form.html"

    def form_valid(self, form):
        self.object = form.save()
        self.object.date = datetime.now()
        self.object.save()

        # send the email
        emails.send_trial_email(self.object)
        # send message
        messages.add_message(
            self.request, messages.SUCCESS, "Du hast dich erfolgreich angemeldet"
        )
        return super().form_valid(form)


class TesterListView(ListView):
    model = Tester
    template_name = "pages/trial_list.html"


urlpatterns = [
    path("get-section", get_section, name="get_training_section"),
    path("<int:pk>", SessionDetailView.as_view(), name="session_detail"),
    path("<int:pk>/edit", SessionUpdateView.as_view(), name="session_update"),
    path("neu", SessionCreateView.as_view(), name="session_create"),
    path("<int:pk>/delete", session_delete, name="session_delete"),
    path("<int:pk>/toggle", toggle_participation, name="session_participation_toggle"),
    path("probetraining", TesterCreateView.as_view(), name="trial_form"),
    path("probetrainingsverwaltung", TesterListView.as_view(), name="tester_list"),
]
