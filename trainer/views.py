from .models import TrainingSessionEntry
from django.shortcuts import render, get_object_or_404
from members.models import Trainer, Session, Profile, AdditionalEmail, is_trainer, is_chairman
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.views.generic import DeleteView, UpdateView, ListView
from django.urls import reverse
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count, Q
from itertools import groupby


def trainer_check(user):
    return is_trainer(user)

@user_passes_test(trainer_check)
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


@user_passes_test(trainer_check)
def trainer_data(request):
    """ I just assume for the moment, that the user is a trainer """
    return render(
        request,"trainer/trainer_data.html",
    )

### JQUERY AJAX STUFF ###
def is_privileged(user):
    return user.profile.privileged

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


class TrainerListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    queryset = Trainer.objects.filter(active=True).select_related("user").order_by("user__last_name")
    template_name = "user_handling/trainer_list.html"

    def test_func(self):
        user = self.request.user
        return trainer_check(user) or is_chairman(user) or user.is_superuser

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
    #template: event_form.html
    model = Trainer
    fields = [
        "trainer_telnr",
        "trainer_email",
        "license_number",
        "license_valid",
        "license_level",
        "contract",
        "license",
        "codex",
        "salary",
        "image"
        ]
    template_name="trainer/trainer_form.html"
    permission_required = 'members.change_trainer'



class TrainerSelfUpdateView(UpdateView, LoginRequiredMixin,UserPassesTestMixin):
    model = Trainer
    fields = [
        "trainer_telnr",
        "trainer_email",
        "license_number",
        "license_valid",
        "license_level",
        "contract",
        "license",
        "codex",
        "image"
    ]
    template_name = "trainer/trainer_form.html"

    def get_object(self):
        return Trainer.objects.get(pk=self.request.user.trainer.pk)

    def test_func(self):
        return is_trainer(self.request.user)


