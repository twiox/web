from collections import Counter

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
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
from django.db.models import Count, F
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from .forms import OrganizerForm, ProbetrainingForm, PublicEventForm, TeamerForm, TesterForm, TrialDateFormSet, TrialGroupForm
from members.models import Chairman
from accounts.profile import html_email
from .models import (
    Teamer,
    PublicEvent,
    EventParticipant,
    EventMerch,
    Tester,
    TrialGroup,
)
from .trials import (
    ACTIVE_GROUP_ORDER, FINAL_OUTCOMES, annotate_groups, archive_group, attended_trainings, can_archive, current_testers, delete_stale_requests, email_board,
    finished_testers, group_attendance, is_photo, upcoming_trial_dates, weekday_matches,
)
from members.roles import BoardRequiredMixin, PrivilegedRequiredMixin, board_required, is_board, is_privileged


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
                "public/emails/probe_email_answer.html",
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
                "public/interested_index.html",
                {"form": form, "chairmen": chairmen, "public_events": public_events},
            )
    form = ProbetrainingForm()
    return render(
        request,
        "public/interested_index.html",
        {"form": form, "chairmen": chairmen, "public_events": public_events},
    )


def interested_offers(request):
    return render(request, "public/interested_offers.html")


def interested_philosophy(request):
    return render(request, "public/interested_philosophy.html", {})


def interested_team(request):
    leipzig_people = Teamer.objects.all()
    return render(
        request,
        "public/interested_team.html",
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

    template_name = "public/tester_index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # no cron here (see members.views.index): old requests are cleaned up whenever the dashboard is opened
        delete_stale_requests()
        waiting = list(Tester.objects.filter(trial_group__isnull=True))
        board = is_board(self.request.user)
        groups = annotate_groups(TrialGroup.objects.all())
        archived = list(groups.filter(archived__isnull=False).order_by("-archived", "-pk"))
        active = list(groups.filter(archived__isnull=True).order_by(*ACTIVE_GROUP_ORDER))
        # finished trials, one collapsible table per group (same order as the cards)
        finished = {}
        for tester in finished_testers():
            finished.setdefault(tester.trial_group_id, []).append(tester)
        finished_groups = []
        for group in active:
            if group.pk in finished:
                group.finished = finished[group.pk]
                group.open = any(not tester.outcome for tester in group.finished)  # someone still without outcome
                finished_groups.append(group)
        context.update(
            waiting=len(waiting),
            in_groups=current_testers().filter(trial_group__isnull=False).count(),
            age_groups=tester_age_groups(waiting),
            groups=active,
            archived_groups=archived,
            archived_members=sum(g.member_count for g in archived),
            archived_declined=sum(g.declined_count for g in archived),
            # the board sees all dates, trainers the ones at their own training times
            upcoming=upcoming_trial_dates(self.request.user, board),
            upcoming_all=board,
            finished_groups=finished_groups,
            outcomes=Tester.OUTCOMES,
        )
        return context


class TesterListView(LoginRequiredMixin, PrivilegedRequiredMixin, ListView):
    """All trial requests outside archived groups, newest first; requests from before the date was stored come last."""
    template_name = "public/tester_list.html"

    model = Tester
    queryset = (
        current_testers().select_related("trial_group")
        .annotate(visits=Count("attendances"))  # trial trainings attended, in any group
        .order_by(F("created").desc(nulls_last=True), "-pk")
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["groups"] = TrialGroup.objects.filter(archived__isnull=True).order_by("name")  # for the group dropdown in each row
        context["object_list"] = flag_duplicates(context["object_list"])
        return context


def flag_duplicates(testers):
    """Sets tester.duplicates: how many other listed requests have the same name (case and spaces ignored)."""
    testers = list(testers)
    key = lambda tester: (" ".join(tester.first_name.lower().split()), " ".join(tester.last_name.lower().split()))
    counts = Counter(key(tester) for tester in testers)
    for tester in testers:
        tester.duplicates = counts[key(tester)] - 1
    return testers


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


APPLICATION_MAX_PAGES = 10


@login_required
@require_POST
def tester_application(request, pk):
    """Group page: a trainer photographed the membership application (one photo per page).

    The pages go to the board by email (attached from memory, never stored) and the outcome becomes
    "Antrag abgegeben" – also if the email fails; the trainer then hands in the paper.
    Errors with the photos come back as {"error": ...}, nothing is changed then.
    """
    if not is_privileged(request.user):
        return JsonResponse({"success": False}, status=403)
    tester = get_object_or_404(current_testers().select_related("trial_group").exclude(outcome__in=FINAL_OUTCOMES), pk=pk)
    pages = request.FILES.getlist("pages")
    if not pages:
        return JsonResponse({"error": "Bitte mindestens eine Seite fotografieren."}, status=400)
    if len(pages) > APPLICATION_MAX_PAGES:
        return JsonResponse({"error": f"Höchstens {APPLICATION_MAX_PAGES} Seiten."}, status=400)
    if not all(is_photo(page) for page in pages):
        return JsonResponse({"error": "Mindestens eine Datei ist kein Foto – bitte die Seite neu fotografieren."}, status=400)

    tester.outcome = "applied"
    tester.save(update_fields=["outcome"])

    trainer = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
    # only name and group: everything else about the person is on the server
    body = (
        f"{trainer} hat den Mitgliedsantrag von {tester} (Probetrainingsgruppe {tester.trial_group or '–'}) hochgeladen.\n\n"
        f"Im Anhang: {len(pages)} Seite{'n' if len(pages) != 1 else ''}. "
    )
    sent = email_board(
        f"Mitgliedsantrag: {tester} ({tester.trial_group or 'ohne Gruppe'})", body,
        f"antrag-{tester.first_name}-{tester.last_name}", pages,
    )
    if sent:
        messages.success(request, f"Antrag von {tester} ist per E-Mail an den Vorstand gegangen – Ergebnis: Antrag abgegeben.")
    else:
        messages.warning(request, f"Antrag von {tester} eingetragen, aber die E-Mail ging nicht raus – bitte gib die Papiere so bald wie möglich beim Vorstand ab.")
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


@login_required
@require_POST
def tester_consent_upload(request, pk):
    """Group page, for trainers: the parents handed in the consent form – with a photo of it, or without.

    The board gets an email (the photo as PDF, built in memory, never stored). The box is ticked also if
    the email fails; the trainer then hands in the paper. Errors with the photo come back as {"error": ...}.
    """
    if not is_privileged(request.user):
        return JsonResponse({"success": False}, status=403)
    tester = get_object_or_404(current_testers().select_related("trial_group"), pk=pk)
    photo = request.FILES.get("photo")
    if photo and not is_photo(photo):
        return JsonResponse({"error": "Das ist kein Foto – bitte ein Foto der Erklärung aufnehmen oder ohne Foto bestätigen."}, status=400)
    tester.has_consent = True
    tester.save(update_fields=["has_consent"])

    trainer = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
    body = (
        f"{trainer} hat die Einverständniserklärung für {tester} (Probetrainingsgruppe {tester.trial_group or '–'}) als abgegeben markiert.\n\n"
        + ("Das Foto der Erklärung ist angehängt." if photo else "Es wurde kein Foto gemacht – das Papier soll so bald wie möglich beim Vorstand abgegeben werden.")
    )
    sent = email_board(
        f"Einverständniserklärung: {tester} ({tester.trial_group or 'ohne Gruppe'})", body,
        f"einverstaendnis-{tester.first_name}-{tester.last_name}", [photo] if photo else [],
    )
    if sent and photo:
        messages.success(request, f"Einverständniserklärung von {tester} gespeichert – das Foto ist per E-Mail an den Vorstand gegangen.")
    else:
        messages.info(request, f"Einverständniserklärung von {tester} gespeichert. Bitte gib sie so bald wie möglich beim Vorstand ab.")
    return JsonResponse({"success": True})


class TesterCreateView(LoginRequiredMixin, BoardRequiredMixin, CreateView):
    """The board enters someone by hand, e.g. after a phone call, without the public form."""
    template_name = "public/tester_form.html"

    model = Tester
    form_class = TesterForm

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), "board": True}

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, f"{self.object} eingetragen")
        return reverse("tester_list")


class TesterUpdateView(LoginRequiredMixin, PrivilegedRequiredMixin, UpdateView):
    template_name = "public/tester_form.html"
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
    template_name = "public/tester_confirm_delete.html"

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
    template_name = "public/trialgroup_form.html"

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
    template_name = "public/trialgroup_detail.html"

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
            outcomes=Tester.OUTCOMES,
            # for adding people who are still waiting
            waiting=Tester.objects.filter(trial_group__isnull=True).order_by("last_name", "first_name"),
        )
        return context


class TrialGroupDeleteView(LoginRequiredMixin, PrivilegedRequiredMixin, DeleteView):
    """POST only; the participants go back to waiting, the attendance in the session entries stays.

    An archived group (board only) takes its anonymised participants with it.
    """
    template_name = "public/trialgroup_confirm_delete.html"

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


class TeamerLeipzigCreateView(LoginRequiredMixin, BoardRequiredMixin, CreateView):
    template_name = "public/teamer_form.html"
    model = Teamer
    form_class = TeamerForm

    def form_valid(self, form):
        form.instance.city = "leipzig"  # before the one save (each save crops the photo again)
        messages.add_message(self.request, messages.SUCCESS, "Neues Teammitglied erstellt")
        return super().form_valid(form)


class TeamerUpdateView(LoginRequiredMixin, BoardRequiredMixin, UpdateView):
    template_name = "public/teamer_form.html"
    model = Teamer
    form_class = TeamerForm

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, "Teammitglied erfolgreich aktualisiert")
        return super().form_valid(form)


class TeamerDeleteView(LoginRequiredMixin, BoardRequiredMixin, DeleteView):
    template_name = "public/teamer_confirm_delete.html"
    model = Teamer

    def post(self, request, *args, **kwargs):
        messages.add_message(request, messages.SUCCESS, "Teammitglied gelöscht")
        return self.delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("team")


class PublicEventCreateView(LoginRequiredMixin, BoardRequiredMixin, CreateView):
    model = PublicEvent
    fields = "__all__"
    template_name = "public/publicevent_form.html"


class PublicEventView(DetailView):
    template_name = "public/publicevent_detail.html"
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
                "public/public_event_confirmation_email.html",
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


@login_required
@board_required
def event_participant_list_view(request, event_slug):
    event = get_object_or_404(PublicEvent, slug=event_slug)
    object_list = EventParticipant.objects.filter(event=event)
    return render(
        request,
        "public/eventparticipant_list.html",
        {"object_list": object_list, "event": event},
    )


class EventParticipantDeleteView(UserPassesTestMixin, DeleteView):
    template_name = "public/eventparticipant_confirm_delete.html"
    model = EventParticipant

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
    template_name = "public/eventparticipant_form_update.html"
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
    template_name = "public/publicevent_confirm_delete.html"
    model = PublicEvent

    def test_func(self):
        return is_board(self.request.user)

    def get_success_url(self, **kwargs):
        slug = self.get_object().slug
        messages.add_message(
            self.request, messages.SUCCESS, "Veranstaltung erfolgreich gelöscht"
        )
        return reverse("interested_index")


class PublicEventUpdateView(UserPassesTestMixin, UpdateView):
    template_name = "public/publicevent_form.html"
    model = PublicEvent
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
    template_name = "public/eventmerch_form.html"
    model = EventMerch
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
    template_name = "public/eventmerch_form.html"
    model = EventMerch
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
    template_name = "public/eventmerch_confirm_delete.html"
    model = EventMerch

    def test_func(self):
        return is_board(self.request.user)

    def get_success_url(self, **kwargs):
        event_pk = self.get_object().event.pk
        messages.add_message(
            self.request, messages.SUCCESS, "Merch erfolgreich gelöscht"
        )
        return reverse("public_event_change", kwargs={"pk": event_pk})


def fsj_view(request):
    return render(request,'public/fsj.html')

def nebenjob_view(request):
    return render(request,'public/nebenjob.html')


def organizers_index(request):
    """The page for event organizers (/veranstalter/, its own section in the navigation): a request form
    that goes to the board, with a confirmation to the organizer."""
    chairmen = Chairman.objects.filter(active=True, show__contains="event_site")
    if (request.method == "POST"):
        form = OrganizerForm(request.POST) #if no files
        if form.is_valid():
            #get Form data
            captcha = form.cleaned_data.get('captcha')

            if captcha != 'parkour':
                form = OrganizerForm() 
                return render(request, "public/organizers.html", {"form":form,"chairmen":chairmen})

            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            int_email = form.cleaned_data.get('email')
            telnr = form.cleaned_data.get('telephone')
            notes = form.cleaned_data.get('notes')
            
            context = {"first_name": first_name, "last_name": last_name, "email": int_email, "telnr": telnr, "notes": notes}
            # to the board (a reply goes to the organizer), and a confirmation to the organizer
            html_email(f"Twio X e.V. | Anfrage Veranstalter {first_name} {last_name}", "public/emails/organizer_request_board.html",
                       context, [settings.TO_EMAIL], reply_to=[int_email] if int_email.isascii() else None).send()  # a non-ASCII Reply-To ends up empty
            html_email("Twio X e.V. | Deine Anfrage", "public/emails/organizer_request_answer.html",
                       context, [int_email], reply_to=[settings.TO_EMAIL]).send()
            messages.add_message(request, messages.SUCCESS, 'Anfrage erfolgreich verschickt')
            return HttpResponseRedirect("")
        else:
            return render(request,"public/organizers.html",{"form":form, "chairmen":chairmen})
    form = OrganizerForm() 
    return render(request, "public/organizers.html", {"form":form,"chairmen":chairmen})


def landing_page(request):
    public_events = [x for x in PublicEvent.objects.all() if not x.is_past_due]
    return render(request, "public/landing.html", {"public_events": public_events})


def impressum_page(request):
    return render(request, "public/impressum.html")


def data_protection_page(request):
    return render(request, "public/dataprotection.html")
