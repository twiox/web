from datetime import date

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from django.views.generic import (
    CreateView,
    UpdateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
)
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Count, F, Max, Min, Q
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from .forms import ProbetrainingForm, PublicEventForm, TesterForm, TrialDateFormSet, TrialGroupForm
from members.models import Chairman
from .models import (
    Teamer,
    PublicEvent,
    EventParticipant,
    EventMerch,
    Tester,
    TrialGroup,
)
from .trials import (
    archive_group, attended_trainings, can_archive, current_testers, delete_stale_requests, finished_testers, group_attendance,
    upcoming_trial_dates, weekday_matches,
)
from members.roles import PrivilegedRequiredMixin, is_board, is_privileged


def interested_index(request):
    chairmen = Chairman.objects.filter(active=True, show__contains="interested_site")
    public_events = [x for x in PublicEvent.objects.all() if not x.is_past_due]

    if request.method == "POST":
        form = ProbetrainingForm(request.POST)  # if no files
        if form.is_valid():
            # get Form data
            test = form.save()

            mail_subject = (
                f"Twio X e.V. - Anfrage Probetraining {test.first_name} {test.last_name}"
            )
            message = render_to_string(
                "interested/emails/probe_email_answer.html",
                {
                    "object": test,
                },
            )
            email = EmailMessage(mail_subject, message, to=[settings.TO_EMAIL, test.email])
            email.content_subtype = 'html'
            email.send()
            messages.add_message(request, messages.SUCCESS, "Anmeldung verschickt")
            return HttpResponseRedirect(reverse("interested_index"))
        else:
            return render(
                request,
                "interested/interested_index.html",
                {"form": form, "chairmen": chairmen, "public_events": public_events},
            )
    form = ProbetrainingForm()
    return render(
        request,
        "interested/interested_index.html",
        {"form": form, "chairmen": chairmen, "public_events": public_events},
    )


def interested_offers(request):
    if request.method == "POST":
        form = ProbetrainingForm(request.POST)  # if no files
        if form.is_valid():
            messages.add_message(
                request, messages.SUCCESS, "Workshopanfrage verschickt"
            )
            first_name = form.cleaned_data.get("first_name")
            last_name = form.cleaned_data.get("last_name")
            birthdate = form.cleaned_data.get("birth_date")
            int_email = form.cleaned_data.get("email")
            telnr = form.cleaned_data.get("telephone")
            city = form.cleaned_data.get("city")
            notes = form.cleaned_data.get("notes")

            mail_subject = f"Anfrage Workshop von {first_name} {last_name}"
            message = render_to_string(
                "interested/emails/workshop_email.html",
                {
                    "first_name": first_name,
                    "last_name": last_name,
                    "birthdate": birthdate,
                    "email": int_email,
                    "telnr": telnr,
                    "city": city,
                    "notes": notes,
                },
            )
            email = EmailMessage(mail_subject, message, to=[settings.TO_EMAIL])
            email.send()
            # And the message to the interested
            message2 = render_to_string(
                "interested/emails/workshop_email_answer.html",
                {"first_name": first_name, "last_name": last_name},
            )
            EmailMessage(
                f"Twio X e.V. - Deine Workshopanfrage", message2, to=[int_email]
            ).send()
            return HttpResponseRedirect(reverse("offers"))

        else:
            return render(request, "interested/interested_offers.html", {"form": form})
    form = ProbetrainingForm()
    return render(request, "interested/interested_offers.html", {"form": form})


def interested_philosophy(request):
    return render(request, "interested/interested_philosophy.html", {})


def interested_team(request):
    leipzig_people = Teamer.objects.all()
    return render(
        request,
        "interested/interested_team.html",
        {"leipzig_people": leipzig_people},
    )


def tester_age_groups(testers):
    """Children / teenagers / adults / without birthday, for the dashboard."""
    groups = {"Kinder (bis 13)": 0, "Jugendliche (14–17)": 0, "Erwachsene (ab 18)": 0}
    for tester in testers:
        age = tester.age
        if age is None:
            continue
        key = "Kinder (bis 13)" if age < 14 else "Jugendliche (14–17)" if age < 18 else "Erwachsene (ab 18)"
        groups[key] += 1
    return groups


class TesterIndexView(LoginRequiredMixin, PrivilegedRequiredMixin, TemplateView):
    """Probetraining dashboard: who is waiting, the groups, and the next trial dates (archived groups only in their overview)."""

    template_name = "interested/tester_index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # no cron here (see members.views.index): old requests are cleaned up whenever the dashboard is opened
        delete_stale_requests()
        waiting = list(Tester.objects.filter(trial_group__isnull=True))
        board = is_board(self.request.user)
        groups = TrialGroup.objects.annotate(
            size=Count("testers", distinct=True),
            decided_count=Count("testers", filter=~Q(testers__outcome=""), distinct=True),
            applied_count=Count("testers", filter=Q(testers__outcome="applied"), distinct=True),
            member_count=Count("testers", filter=Q(testers__outcome="member"), distinct=True),
            declined_count=Count("testers", filter=Q(testers__outcome="declined"), distinct=True),
            date_count=Count("trial_dates", distinct=True),
            past_count=Count("trial_dates", filter=Q(trial_dates__date__lt=date.today()), distinct=True),
            first_date=Min("trial_dates__date"),
            last_date=Max("trial_dates__date"),
        )
        archived = list(groups.filter(archived__isnull=False).order_by("-archived", "-pk"))
        context.update(
            waiting=len(waiting),
            in_groups=current_testers().filter(trial_group__isnull=False).count(),
            age_groups=tester_age_groups(waiting),
            groups=groups.filter(archived__isnull=True),
            archived_groups=archived,
            archived_members=sum(g.member_count for g in archived),
            archived_declined=sum(g.declined_count for g in archived),
            # the board sees all dates, trainers the ones at their own training times
            upcoming=upcoming_trial_dates(self.request.user, board),
            upcoming_all=board,
            finished=finished_testers(),
            outcomes=Tester.OUTCOMES,
        )
        return context


class TesterListView(LoginRequiredMixin, PrivilegedRequiredMixin, ListView):
    """All trial requests outside archived groups, newest first; requests from before the date was stored come last."""

    model = Tester
    queryset = (
        current_testers().select_related("trial_group")
        .annotate(visits=Count("attendances"))  # trial trainings attended, in any group
        .order_by(F("created").desc(nulls_last=True), "-pk")
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["groups"] = TrialGroup.objects.filter(archived__isnull=True).order_by("name")  # for the group dropdown in each row
        return context


@login_required
@require_POST
def tester_note(request, pk):
    """List: edit the notes in place; the Vorstandsnotizen only by the board."""
    field = request.POST.get("field")
    allowed = {"notes": is_privileged, "board_notes": is_board}
    if field not in allowed or not allowed[field](request.user):
        return JsonResponse({"success": False}, status=403)
    tester = get_object_or_404(current_testers(), pk=pk)
    setattr(tester, field, request.POST.get("value", "").strip())
    tester.save(update_fields=[field])
    return JsonResponse({"success": True})


@login_required
@require_POST
def tester_set_group(request, pk):
    """Puts a trial participant into a group (from the list or the group page); empty: waiting again."""
    if not is_privileged(request.user):
        return JsonResponse({"success": False}, status=403)
    tester = get_object_or_404(current_testers(), pk=pk)
    group_pk = request.POST.get("group", "")
    tester.trial_group = get_object_or_404(TrialGroup, pk=group_pk, archived__isnull=True) if group_pk else None
    tester.save(update_fields=["trial_group"])
    return JsonResponse({"success": True, "group": str(tester.trial_group or "")})


@login_required
@require_POST
def tester_outcome(request, pk):
    """Dashboard dropdown: what came of the trial (membership application or not); empty: still open."""
    if not is_privileged(request.user):
        return JsonResponse({"success": False}, status=403)
    tester = get_object_or_404(current_testers(), pk=pk)
    outcome = request.POST.get("outcome", "")
    if outcome not in dict(Tester.OUTCOMES):
        return JsonResponse({"success": False}, status=400)
    tester.outcome = outcome
    tester.save(update_fields=["outcome"])
    return JsonResponse({"success": True})


@login_required
@require_POST
def tester_consent(request, pk):
    """List checkbox: the parents' consent for a minor is there (or not)."""
    if not is_privileged(request.user):
        return JsonResponse({"success": False}, status=403)
    tester = get_object_or_404(current_testers(), pk=pk)
    tester.has_consent = request.POST.get("value") == "true"
    tester.save(update_fields=["has_consent"])
    return JsonResponse({"success": True})


class TesterUpdateView(LoginRequiredMixin, PrivilegedRequiredMixin, UpdateView):
    model = Tester
    form_class = TesterForm

    def get_queryset(self):
        return current_testers()  # archived requests have nothing left to edit

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), "board": is_board(self.request.user)}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["attended"] = attended_trainings(self.object)
        return context

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, f"{self.object} gespeichert")
        return reverse("tester_list")


class TesterDeleteView(LoginRequiredMixin, PrivilegedRequiredMixin, DeleteView):
    """POST only (the list and the group page ask first)."""

    model = Tester
    http_method_names = ["post"]

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, f"{self.object} gelöscht")
        return super().form_valid(form)

    def get_success_url(self):
        # deleted from the group page: back to the group
        if "from_group" in self.request.POST and self.object.trial_group_id:
            return reverse("trial_group_detail", args=[self.object.trial_group_id])
        return reverse("tester_list")


class TrialGroupFormMixin:
    """Create and edit a group together with its dates."""

    model = TrialGroup
    form_class = TrialGroupForm
    template_name = "interested/trialgroup_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dates"] = kwargs.get("dates") or TrialDateFormSet(instance=self.object)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object() if "pk" in kwargs else None
        form = self.get_form()
        dates = TrialDateFormSet(request.POST, instance=self.object or TrialGroup())
        if form.is_valid() and dates.is_valid():
            self.object = form.save()
            dates.instance = self.object
            dates.save()
            messages.add_message(request, messages.SUCCESS, f"Gruppe {self.object} gespeichert")
            return redirect("trial_group_detail", pk=self.object.pk)
        return self.render_to_response(self.get_context_data(form=form, dates=dates))


class TrialGroupCreateView(LoginRequiredMixin, PrivilegedRequiredMixin, TrialGroupFormMixin, CreateView):
    pass


class TrialGroupUpdateView(LoginRequiredMixin, PrivilegedRequiredMixin, TrialGroupFormMixin, UpdateView):
    def get_queryset(self):
        return TrialGroup.objects.filter(archived__isnull=True)


class TrialGroupDetailView(LoginRequiredMixin, PrivilegedRequiredMixin, DetailView):
    """Dates, participants and their attendance (from the trainers' session entries)."""

    model = TrialGroup
    template_name = "interested/trialgroup_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dates, rows = group_attendance(self.object)
        for trial_date in dates:
            trial_date.weekday_ok = weekday_matches(trial_date)
        context.update(
            dates=dates,
            rows=rows,
            can_archive=can_archive(self.object),
            archive_members=sum(1 for tester, _ in rows if tester.outcome == "member"),
            # for adding people who are still waiting
            waiting=Tester.objects.filter(trial_group__isnull=True).order_by("last_name", "first_name"),
        )
        return context


class TrialGroupDeleteView(LoginRequiredMixin, PrivilegedRequiredMixin, DeleteView):
    """POST only; the participants go back to waiting, the attendance in the session entries stays.

    An archived group (board only) takes its anonymised participants with it.
    """

    model = TrialGroup
    http_method_names = ["post"]

    def form_valid(self, form):
        if self.object.archived:
            if not is_board(self.request.user):
                raise PermissionDenied
            self.object.testers.all().delete()
        messages.add_message(self.request, messages.SUCCESS, f"Gruppe {self.object} gelöscht")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("tester_index")


@login_required
@require_POST
def trial_group_archive(request, pk):
    """Board only: archives a group whose participants all have a final outcome (see trials.archive_group)."""
    if not is_board(request.user):
        raise PermissionDenied
    group = get_object_or_404(TrialGroup, pk=pk)
    if not can_archive(group):
        messages.add_message(request, messages.ERROR, "Archivieren geht erst, wenn alle Mitglied oder nicht Mitglied geworden sind.")
        return redirect("trial_group_detail", pk=group.pk)
    archive_group(group)
    messages.add_message(request, messages.SUCCESS, f"Gruppe {group} archiviert")
    return redirect("tester_index")


class TeamerLeipzigCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Teamer
    fields = [
        "priority",
        "picture",
        "name",
        "position",
        "notes",
        "public_telnr",
        "public_email",
    ]
    permission_required = "interested.add_teamer"

    def form_valid(self, form):
        teamer = form.save()
        teamer.city = "leipzig"
        teamer.save()
        messages.add_message(
            self.request, messages.SUCCESS, "Neues Teammitglied erstellt"
        )
        return super(TeamerLeipzigCreateView, self).form_valid(form)


class TeamerUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Teamer
    fields = [
        "priority",
        "picture",
        "name",
        "position",
        "notes",
        "public_telnr",
        "public_email",
    ]
    permission_required = "interested.change_teamer"

    def form_valid(self, form):
        messages.add_message(
            self.request, messages.SUCCESS, "Teammitglied erfolgreich aktualisiert"
        )
        return super(TeamerUpdateView, self).form_valid(form)


class TeamerDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Teamer
    permission_required = "interested.delete_teamer"

    def post(self, request, *args, **kwargs):
        messages.add_message(request, messages.SUCCESS, "Teammitglied gelöscht")
        return self.delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("team")


class PublicEventCreateView(PermissionRequiredMixin, CreateView):
    model = PublicEvent
    permission_required = "interested_add_publicevent"
    fields = "__all__"
    template_name = "interested/publicevent_form.html"


class PublicEventView(DetailView):
    model = PublicEvent
    slug_url_kwarg = "event_slug"
    slug_field = "slug"  # DetailView's default value: optional
    form_class = PublicEventForm

    def get_context_data(self, **kwargs):
        context = super(PublicEventView, self).get_context_data(**kwargs)
        context["event"] = self.get_object()
        merch = EventMerch.objects.filter(event=self.get_object())
        if merch:
            merch = merch.all()[0]
            context["sizes"] = [x for x in merch.sizes.split("\t")]
        else:
            context["sizes"] = []
        context["merch"] = merch
        context["chairmen"] = Chairman.objects.filter(
            active=True, show__contains="interested_xdream"
        )

        return context

    def post(self, request, *args, **kwargs):
        form = PublicEventForm(request.POST)
        event = self.get_object()
        self.object = event
        context = super(PublicEventView, self).get_context_data(**kwargs)

        if form.is_valid():

            participant = EventParticipant(
                event=event,
                first_name=form.cleaned_data.get("first_name"),
                last_name=form.cleaned_data.get("last_name"),
                birthday=form.cleaned_data.get("birthday"),
                email=form.cleaned_data.get("email"),
                phone=form.cleaned_data.get("phone", ""),
                contact=form.cleaned_data.get("contact", ""),
                invoice=float(event.base_costs),
                merch_wanted=form.cleaned_data.get("merch_wanted", False),
                merch_size=form.cleaned_data.get("merch_size", ""),
                inform_ok = form.cleaned_data.get("inform_ok", False),
                notes="",
            )

            participant.save()
            mail_subject = f"Twio X e.V. | {event.title}: Anmeldebestätigung {participant.first_name} {participant.last_name}"
            message = render_to_string(
                "interested/public_event_confirmation_email.html",
                {
                    "first_name": participant.first_name,
                    "last_name": participant.last_name,
                    "birthdate": participant.birthday,
                    "email": participant.email,
                    "telnr": participant.phone,
                    "title": event.title,
                    "start_date": event.start_date,
                    "end_date": event.end_date,
                    "contact": participant.contact,
                    "merch_wanted": True if participant.merch_wanted else False,
                    "merch_title": None,
                    "merch_size": participant.merch_size,
                    "costs": participant.invoice,
                    "id": participant.id,
                    "event": event.title.replace(" ", "-"),
                },
            )
            email = EmailMessage(mail_subject, message, to=[settings.TO_EMAIL, participant.email])
            email.send()

            messages.add_message(
                request, messages.SUCCESS, "Du hast dich erfolgreich angemeldet"
            )
            context["form"] = PublicEventForm
            return self.render_to_response(context=context)

        else:
            context["form"] = form
            return self.render_to_response(context=context)


def event_participant_list_view(request, event_slug):
    if not is_board(request.user):
        return render(request, "login")
    event = PublicEvent.objects.get(slug=event_slug)
    object_list = EventParticipant.objects.filter(event=event)
    return render(
        request,
        "interested/eventparticipant_list.html",
        {"object_list": object_list, "event": event},
    )


class EventParticipantDeleteView(UserPassesTestMixin, DeleteView):
    model = EventParticipant
    permission_required = "interested_remove_eventparticipant"

    def test_func(self):
        return is_board(self.request.user)

    def get_success_url(self, **kwargs):
        slug = self.get_object().event.slug
        messages.add_message(
            self.request, messages.SUCCESS, "Teilnehmer*in erfolgreich gelöscht"
        )
        return reverse("event_participant_list", kwargs={"event_slug": slug})


class EventParticipantUpdateView(UserPassesTestMixin, UpdateView):
    model = EventParticipant
    permission_required = "interested_change_eventparticipant"
    template_name = "interested/eventparticipant_form_update.html"
    fields = [
        "first_name",
        "last_name",
        "birthday",
        "email",
        "phone",
        "contact",
        "invoice",
        "payed",
        "merch_wanted",
        "merch_size",
        "notes",
    ]

    def test_func(self):
        return is_board(self.request.user)

    def get_success_url(self, **kwargs):
        slug = self.get_object().event.slug
        messages.add_message(
            self.request, messages.SUCCESS, "Teilnehmer*in erfolgreich geändert"
        )
        return reverse("event_participant_list", kwargs={"event_slug": slug})


class PublicEventDeleteView(UserPassesTestMixin, DeleteView):
    model = PublicEvent
    permission_required = "interested_publicevent_delete"

    def test_func(self):
        return is_board(self.request.user)

    def get_success_url(self, **kwargs):
        slug = self.get_object().slug
        messages.add_message(
            self.request, messages.SUCCESS, "Veranstaltung erfolgreich gelöscht"
        )
        return reverse("interested_index")


class PublicEventUpdateView(UserPassesTestMixin, UpdateView):
    model = PublicEvent
    permission_required = "interested_change_eventparticipant"
    fields = "__all__"

    def test_func(self):
        return is_board(self.request.user)

    def get_success_url(self, **kwargs):
        slug = self.get_object().slug
        messages.add_message(
            self.request, messages.SUCCESS, "Veranstaltung erfolgreich geändert"
        )
        return reverse("public_event", kwargs={"event_slug": slug})


class EventMerchCreateView(UserPassesTestMixin, CreateView):
    model = EventMerch
    permission_required = "interested_change_eventmerch"
    fields = "__all__"

    def test_func(self):
        return is_board(self.request.user)

    def form_valid(self, form):
        self.object = form.save()
        return super().form_valid(form)

    def get_success_url(self, **kwargs):
        messages.add_message(
            self.request, messages.SUCCESS, "Merch erfolgreich hinzugefügt"
        )
        return reverse("public_event_change", kwargs={"pk": self.object.event.pk})


class EventMerchUpdateView(UserPassesTestMixin, UpdateView):
    model = EventMerch
    permission_required = "interested_change_eventmerch"
    fields = "__all__"

    def test_func(self):
        return is_board(self.request.user)

    def get_success_url(self, **kwargs):
        event_pk = self.get_object().event.pk
        messages.add_message(
            self.request, messages.SUCCESS, "Merch erfolgreich geändert"
        )
        return reverse("public_event_change", kwargs={"pk": event_pk})


class EventMerchDeleteView(UserPassesTestMixin, DeleteView):
    model = EventMerch
    permission_required = "interested_change_eventmerch"

    def test_func(self):
        return is_board(self.request.user)

    def get_success_url(self, **kwargs):
        event_pk = self.get_object().event.pk
        messages.add_message(
            self.request, messages.SUCCESS, "Merch erfolgreich gelöscht"
        )
        return reverse("public_event_change", kwargs={"pk": event_pk})


def fsj_view(request):
    return render(request,'interested/fsj.html')

def nebenjob_view(request):
    return render(request,'interested/nebenjob.html')
