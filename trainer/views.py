from .forms import TrainerForm, TrainerSelfForm
from .models import TrainingSessionEntry, TrainingSessionParticipant
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from members.models import Trainer, Session, Profile
from members.roles import PrivilegedRequiredMixin, is_privileged, is_trainer
from interested.models import TrialGroup
from interested.trials import ACTIVE_GROUP_ORDER, annotate_groups, upcoming_trial_dates
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.views.generic import DeleteView, UpdateView, ListView
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_POST
from datetime import date
from django.db.models import Count, Max, Q
from itertools import groupby


@user_passes_test(is_trainer)
def trainer_index(request):
    trainer = request.user.trainer
    entries = (
        TrainingSessionEntry.objects.filter(Q(trainer=trainer) | Q(cotrainer=trainer))
        .annotate(
            participant_count=Count("participant", distinct=True),
            invoice_count=Count("invoice", distinct=True),
        )
        .order_by("-date")
    )
    # grouped by month, newest first; entries without a date go last
    months = []
    for month, group in groupby(entries, key=lambda e: e.date.replace(day=1).date() if e.date else None):
        group = list(group)
        months.append({
            "month": month,
            "entries": group,
            "unsent": sum(not e.billed for e in group),
        })
    return render(request, "trainer/trainer_index.html", {"months": months})


@user_passes_test(is_trainer)
def trainer_groups(request):
    """The weekly training times the trainer is responsible for, as cards (the group page follows later),
    and below them the trial trainings at these times."""
    trainer = request.user.trainer
    sessions = (
        Session.objects.filter(trainer=trainer)
        .select_related("spot")
        .prefetch_related("trainer__user")
        .annotate(participant_count=Count("participants", distinct=True))
        .order_by("day_key", "start_time")
    )
    for session in sessions:
        session.co_trainers = [t.user.first_name for t in session.trainer.all() if t.pk != trainer.pk]
    # Probetraining: the next trial dates at the own training times (as on the trial dashboard), and the
    # groups in progress (not archived) with a date at one of them, e.g. to upload an application after
    # the last date. People and contacts are on the group page.
    own = TrialGroup.objects.filter(trial_dates__session__trainer=trainer).values("pk")
    # pk__in instead of filtering the dates directly, so the card numbers count all dates of the group
    trial_groups = annotate_groups(TrialGroup.objects.filter(pk__in=own, archived__isnull=True)).order_by(*ACTIVE_GROUP_ORDER)
    return render(request, "trainer/trainer_groups.html", {
        "sessions": sessions,
        "upcoming": upcoming_trial_dates(request.user, board=False),
        "groups": trial_groups,
    })


@user_passes_test(is_privileged)
def trainer_group_detail(request, pk):
    """A weekly training time as a group: who ticked "Teilnahme" for it, with their contacts.
    Built like the trial group page, without dates, attendance and outcomes. Open to every trainer
    (e.g. a substitute) and the board, like the trial groups."""
    session = get_object_or_404(Session.objects.select_related("spot").prefetch_related("trainer__user"), pk=pk)
    participants = list(session.participants.select_related("user").order_by("user__last_name", "user__first_name"))
    # contact person and emergency number are columns only if a minor here has one of them
    show_parent = any(p.age is not None and p.age < 18 and (p.parent or p.parent_telnr) for p in participants)
    return render(request, "trainer/training_group_detail.html", {
        "object": session,
        "participants": participants,
        "show_parent": show_parent,
        "candidates": group_candidates(session),
    })


def group_candidates(session):
    """Members who were at a training of this training time at least once (recorded in the trainers'
    session entries) but are not on its list, with how often and when they were there last."""
    visits = {
        row["user"]: row
        for row in TrainingSessionParticipant.objects.filter(session__session=session, user__isnull=False)
        .values("user").annotate(count=Count("session", distinct=True), last=Max("session__date"))
    }
    candidates = (
        Profile.objects.filter(user__in=visits, user__is_active=True)
        .exclude(pk__in=session.participants.values("pk"))
        .select_related("user").order_by("user__last_name", "user__first_name")
    )
    for profile in candidates:
        profile.visits = visits[profile.user_id]["count"]
        profile.last_visit = visits[profile.user_id]["last"]
    return candidates


@user_passes_test(is_privileged)
@require_POST
def trainer_group_add(request, pk):
    """Puts someone on a training time's list who was there at least once (see group_candidates)."""
    session = get_object_or_404(Session, pk=pk)
    profile = get_object_or_404(group_candidates(session), pk=request.POST.get("profile") or 0)
    session.participants.add(profile)
    messages.add_message(request, messages.SUCCESS, f"{profile.user.get_full_name()} zu {session.title} hinzugefügt")
    return HttpResponseRedirect(reverse("trainer_group_detail", args=[session.pk]))


@user_passes_test(is_privileged)
@require_POST
def trainer_group_remove(request, pk, profile_pk):
    """Takes someone off a training time's list, e.g. after ticking "Teilnahme" by accident.
    They can tick it again on the dashboard at any time."""
    session = get_object_or_404(Session, pk=pk)
    profile = get_object_or_404(session.participants.select_related("user"), pk=profile_pk)
    session.participants.remove(profile)
    messages.add_message(request, messages.SUCCESS, f"{profile.user.get_full_name()} aus {session.title} entfernt")
    return HttpResponseRedirect(reverse("trainer_group_detail", args=[session.pk]))


@user_passes_test(is_privileged)
@require_POST
def trainer_group_note(request, pk, profile_pk):
    """The trainer notes of someone on the list, edited in place on the group page (saved on leaving the box)."""
    session = get_object_or_404(Session, pk=pk)
    profile = get_object_or_404(session.participants, pk=profile_pk)
    profile.notes_trainer = request.POST.get("value", "").strip()
    profile.save(update_fields=["notes_trainer"])
    return JsonResponse({"success": True})


@user_passes_test(is_trainer)
def trainer_data(request):
    trainer = request.user.trainer
    license_days_left = (trainer.license_valid.date() - date.today()).days if trainer.license_valid else None
    documents = [
        ("Vertrag", trainer.contract),
        ("Lizenz", trainer.license),
        ("Ehrenkodex", trainer.codex),
    ]
    return render(request, "trainer/trainer_data.html", {
        "trainer": trainer,
        "license_expired": license_days_left is not None and license_days_left < 0,
        "license_expires_soon": license_days_left is not None and 0 <= license_days_left <= 60,
        "documents": documents,
    })

class TrainerListView(LoginRequiredMixin, PrivilegedRequiredMixin, ListView):
    queryset = Trainer.objects.filter(active=True).select_related("user").order_by("user__last_name")
    template_name = "user_handling/trainer_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # deactivated trainers keep their data (see TrainerDeleteView), listed collapsed below
        context["inactive_trainers"] = Trainer.objects.filter(active=False).select_related("user").order_by("user__last_name")
        return context

class TrainerDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Deactivates straight from the list, without a confirmation page: it can be undone
    in the "Inaktive Trainer*innen" section below the list."""

    model = Trainer
    permission_required = "members.delete_trainer"
    http_method_names = ["post"]

    def form_valid(self, form):
        # deactivate instead of delete, see member_role in user_handling/views.py
        self.object.active = False
        self.object.save()
        messages.add_message(self.request, messages.SUCCESS, f"{self.object.user.get_full_name()} deaktiviert")
        return HttpResponseRedirect(reverse("trainer_list"))

class TrainerUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Trainer
    form_class = TrainerForm
    template_name = "trainer/trainer_form.html"
    permission_required = "members.change_trainer"

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, "Gespeichert")
        return super().form_valid(form)


class TrainerSelfUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    form_class = TrainerSelfForm
    template_name = "trainer/trainer_form.html"
    success_url = reverse_lazy("trainer_data")
    extra_context = {"is_self": True}

    def get_object(self):
        return self.request.user.trainer

    def test_func(self):
        return is_trainer(self.request.user)

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, "Gespeichert")
        return super().form_valid(form)
