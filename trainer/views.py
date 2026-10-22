from .forms import TrainerForm, TrainerSelfForm
from .models import TrainingSessionEntry
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from members.models import Trainer, Session, Profile, AdditionalEmail
from members.roles import PrivilegedRequiredMixin, is_privileged, is_trainer
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.views.generic import DeleteView, UpdateView, ListView
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import user_passes_test
from datetime import date
from django.db.models import Count, Q
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

### JQUERY AJAX STUFF ###
@user_passes_test(is_privileged)
def get_session_emails(request, sessionid):
    """
    Get the emails of all regular members whose age fits the session, plus its trainers
    """
    session = get_object_or_404(Session, pk=sessionid)
    profiles = Profile.objects.filter(status="Ordentliches Mitglied", birthday__isnull=False).select_related("user")
    users = [p.user for p in profiles if session.allows_age(p.age)]
    emails = {u.email for u in users}
    emails |= set(AdditionalEmail.objects.filter(user__in=users).values_list("email", flat=True))
    emails |= set(session.trainer.values_list("trainer_email", flat=True))
    return JsonResponse({'emailstring': ','.join(sorted(e for e in emails if e))})


class TrainerListView(LoginRequiredMixin, PrivilegedRequiredMixin, ListView):
    queryset = Trainer.objects.filter(active=True).select_related("user").order_by("user__last_name")
    template_name = "user_handling/trainer_list.html"

class TrainerDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Trainer
    template_name = "user_handling/trainer_confirm_delete.html"
    permission_required = "members.delete_trainer"

    def get_success_url(self):
        return reverse("trainer_list")

    def form_valid(self, form):
        # deactivate instead of delete, see member_role in user_handling/views.py
        self.object.active = False
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

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
