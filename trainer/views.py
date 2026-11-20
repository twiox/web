from .forms import GroupEmailForm, TrainerForm, TrainerSelfForm
from .models import TrainingSessionEntry, TrainingSessionParticipant
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from members.models import AdditionalEmail, Message, Trainer, Session, Profile
from members.roles import BoardRequiredMixin, PrivilegedRequiredMixin, is_privileged, is_trainer
from public.models import TrialGroup
from public.trials import ACTIVE_GROUP_ORDER, annotate_groups, upcoming_trial_dates
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import DeleteView, UpdateView, ListView
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_POST
from datetime import date, datetime, timedelta
from django.conf import settings
import html as html_lib
import re
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.db.models import Count, Max, Q
from itertools import groupby
import logging

logger = logging.getLogger(__name__)


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
        **group_dashboard(session, participants),
    })


def group_dashboard(session, participants):
    """Data for the dashboard below the list, from the trainers' session entries (Trainingsstunden):
    - timeline: participants per entry of this training time (members, guests and trial participants)
    - heatmap: per person on the list and entry: 2 = there, 1 = at another training the same week, 0 = not there
    """
    entries = list(
        TrainingSessionEntry.objects.filter(session=session, date__isnull=False)
        .annotate(count=Count("participant", distinct=True)).prefetch_related("trainer__user", "cotrainer__user").order_by("date")
    )
    # trainers and co-trainers are not participants of an entry but count as people at the training
    for entry in entries:
        entry.trainer_roles = {t.pk: "Co-Trainer*in" for t in entry.cotrainer.all()}
        entry.trainer_roles.update({t.pk: "Trainer*in" for t in entry.trainer.all()})  # trainer wins over co-trainer
        entry.trainer_count = len(entry.trainer_roles)
        entry.total = entry.count + entry.trainer_count
    timeline = [{"date": e.date.strftime("%Y-%m-%d"), "label": e.date.strftime("%d.%m.%Y"),
                 "count": e.total, "trainers": e.trainer_count} for e in entries]
    trainer_rows = trainer_heatmap(session, entries)

    # every recorded attendance of the people on the list, any training time (for the "same week" cells)
    attended = {}  # user id -> {entry id: iso week}
    rows = TrainingSessionParticipant.objects.filter(
        user__in=[p.user_id for p in participants], session__date__isnull=False
    ).values_list("user", "session_id", "session__date")
    for user_id, entry_id, day in rows:
        attended.setdefault(user_id, {})[entry_id] = day.isocalendar()[:2]

    heatmap = []
    for profile in participants:
        visits = attended.get(profile.user_id, {})
        weeks = {}
        for entry_id, week in visits.items():
            weeks.setdefault(week, set()).add(entry_id)
        cells, last_seen = [], None
        for entry in entries:
            if entry.pk in visits:
                cells.append(2)
                last_seen = entry.date
            elif weeks.get(entry.date.isocalendar()[:2], set()) - {entry.pk}:
                cells.append(1)
            else:
                cells.append(0)
        heatmap.append({"profile": profile, "cells": list(zip(entries, cells)), "last_seen": last_seen})

    # "Andere": who was there but is not on the list (members to add, guests, trial participants)
    on_list = {p.user_id for p in participants}
    others = {entry.pk: [] for entry in entries}
    for row in TrainingSessionParticipant.objects.filter(session__in=entries).select_related("user").order_by("pk"):
        if row.user_id and row.user_id in on_list:
            continue
        if row.user_id:
            label = f"{row.user.get_full_name()} (Mitglied)"
        elif row.tester_id:
            label = f"{row.name or 'Probetraining'} (Probetraining)"
        elif row.name:
            label = f"{row.name} (Gast)"
        else:
            label = row.display_name  # the member account was deleted
        others[row.session_id].append(label)
    other_cells = [(entry, others[entry.pk]) for entry in entries]
    has_others = any(names for _, names in other_cells)
    return {"entries": entries, "timeline": timeline, "heatmap": heatmap, "other_cells": other_cells, "has_others": has_others,
            "trainer_rows": trainer_rows}


def trainer_heatmap(session, entries):
    """The trainer rows on top of the heatmap: the group's trainers and everyone who trained one of its
    entries (as trainer or co-trainer). Per entry: 2 = trained it, 1 = trained another one that week, 0 = not."""
    people = {t.pk: t for t in session.trainer.select_related("user")}
    for entry in entries:
        for t in list(entry.trainer.all()) + list(entry.cotrainer.all()):
            people.setdefault(t.pk, t)
    if not people:
        return []
    # every entry anywhere they trained, for the "same week" cells
    weeks = {}  # trainer id -> {iso week: {entry id}}
    for through in (TrainingSessionEntry.trainer.through, TrainingSessionEntry.cotrainer.through):
        for trainer_id, entry_id, day in through.objects.filter(
            trainer_id__in=people, trainingsessionentry__date__isnull=False
        ).values_list("trainer_id", "trainingsessionentry_id", "trainingsessionentry__date"):
            weeks.setdefault(trainer_id, {}).setdefault(day.isocalendar()[:2], set()).add(entry_id)
    in_group = set(session.trainer.values_list("pk", flat=True))
    rows = []
    for trainer in sorted(people.values(), key=lambda t: (t.pk not in in_group, t.user.last_name, t.user.first_name)):
        cells, last_seen = [], None
        for entry in entries:
            role = entry.trainer_roles.get(trainer.pk)
            if role:
                cells.append((entry, 2, role))
                last_seen = entry.date
            elif weeks.get(trainer.pk, {}).get(entry.date.isocalendar()[:2], set()) - {entry.pk}:
                cells.append((entry, 1, ""))
            else:
                cells.append((entry, 0, ""))
        rows.append({"trainer": trainer, "cells": cells, "last_seen": last_seen, "in_group": trainer.pk in in_group})
    return rows


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


# shown before the subject in the form too, so members see in their inbox where the e-mail comes from
GROUP_EMAIL_PREFIX = "Twio X e.V. | "
# the e-mail goes to the whole group, so it opens with this; shown above the message field as well
GROUP_EMAIL_GREETING = "Liebe Trainingsgruppe,"


def group_email_addresses(user, session):
    """Besides the participants, the e-mail goes to the board (TO_EMAIL) and to every trainer of the
    training time, with their public trainer address; replies go to the board and the sender's public
    trainer address. Trainers without one are skipped, with a hint in the form. An address with special
    characters before the @ stays out of Reply-To: it would empty the whole header."""
    info_to, hints = [("Vorstand", settings.TO_EMAIL)], []
    for trainer in session.trainer.select_related("user").order_by("user__first_name"):
        address = (trainer.trainer_email or "").strip()
        if address:
            info_to.append((trainer.user.get_full_name(), address))
        else:
            hints.append(f"{trainer.user.get_full_name()} hat keine öffentliche Trainer-E-Mail-Adresse und bekommt die E-Mail nicht.")
    own = getattr(user, "trainer", None)
    own_address = (own.trainer_email or "").strip() if own else ""
    reply_to = [settings.TO_EMAIL]
    if not own_address:
        # the board gets the replies through TO_EMAIL anyway, so only trainers need the hint
        if own:
            hints.append("Du hast keine öffentliche Trainer-E-Mail-Adresse, Antworten gehen deshalb nur an den Vorstand."
                         " Du kannst sie unter „Meine Daten“ eintragen.")
    elif not own_address.isascii():
        hints.append(f"Deine Adresse {own_address} enthält Sonderzeichen und kann nicht als Antwortadresse eingetragen werden.")
    else:
        reply_to.append(own_address)
    unique = {}
    for name, address in info_to:
        unique.setdefault(address, name)  # e.g. a trainer whose public address is the club address
    return [(name, address) for address, name in unique.items()], list(dict.fromkeys(reply_to)), hints


def group_email_context(addresses, recipients, form):
    """The chips of the form: participants and the board/trainers, after a failed post in the state they were sent."""
    info_to, reply_to, hints = addresses
    posted = form.is_bound
    kept_info = set(form.data.getlist("info_to")) if posted else {a for _, a in info_to}
    kept_recipients = set(form.data.getlist("recipients")) if posted else {str(p.pk) for p, a in recipients if a}
    return {
        "info_to": [(name, address, address in kept_info) for name, address in info_to],
        "recipients": [(profile, addresses, str(profile.pk) in kept_recipients) for profile, addresses in recipients],
        "reply_to": reply_to,
        "address_hints": hints,
    }


def group_recipients(session):
    """Everyone on the list with their addresses: the own one and the additional ones (e.g. a parent's)."""
    participants = list(session.participants.select_related("user").order_by("user__last_name", "user__first_name"))
    extra = {}
    for user_id, email in AdditionalEmail.objects.filter(user__in=[p.user_id for p in participants]).values_list("user", "email"):
        extra.setdefault(user_id, []).append(email)
    recipients = []
    for profile in participants:
        addresses = list(dict.fromkeys(e.strip() for e in [profile.user.email, *extra.get(profile.user_id, [])] if e and e.strip()))
        recipients.append((profile, addresses))
    return recipients


def send_each(connection, mails):
    """Sends the e-mails one at a time, so a refused address (e.g. with an umlaut) only misses that one.
    mails: (label, build) pairs; returns the labels whose e-mail could not be sent."""
    failed = []
    for label, build in mails:
        try:
            connection.send_messages([build()])
        except Exception:
            logger.exception("group e-mail to %s failed", label)
            failed.append(label)
            connection.close()  # opened again for the next one, in case the error broke the connection
    return failed


@user_passes_test(is_privileged)
def trainer_group_email(request, pk):
    """Writes to everyone on a training time's list, one e-mail each; the board and the training time's
    trainers get the same e-mail (see group_email_addresses). Participants, board and trainers can be
    left out in the form. Optionally also a notice at the training time."""
    session = get_object_or_404(Session, pk=pk)
    recipients = group_recipients(session)
    reachable = [(p, a) for p, a in recipients if a]
    can_notice = is_privileged(request.user)
    addresses = group_email_addresses(request.user, session)
    info_choices, reply_to, _ = addresses
    form = GroupEmailForm(
        request.POST or None, can_notice=can_notice, info_choices=info_choices,
        recipient_choices=[(str(p.pk), p.user.get_full_name()) for p, _ in reachable],
    )
    if request.method == "POST" and form.is_valid():
        subject, body = form.cleaned_data["subject"], form.cleaned_data["body"]
        context = {"body": body, "sender": request.user.get_full_name(), "session": session, "greeting": GROUP_EMAIL_GREETING}

        def mail(to):
            html = render_to_string("trainer/emails/group_email.html", context)
            # for mail apps without HTML: keep line and paragraph breaks, then drop the tags
            text = re.sub(r"<br\s*/?>\s*", "\n", html)
            text = re.sub(r"<hr\s*/?>", "\n\n___\n\n", text)  # the line above the club footer
            text = re.sub(r"</(p|li|ul|h\d)>", "\n\n", text)
            text = re.sub(r"[ \t]+\n", "\n", html_lib.unescape(strip_tags(text)))
            text = re.sub(r"\n{3,}", "\n\n", text).strip()
            message = EmailMultiAlternatives(GROUP_EMAIL_PREFIX + subject, text, settings.DEFAULT_FROM_EMAIL, to, reply_to=reply_to)
            message.attach_alternative(html, "text/html")
            return message

        chosen = set(form.cleaned_data["recipients"])
        selected = [(p, a) for p, a in reachable if str(p.pk) in chosen]
        connection = get_connection()
        failed = send_each(connection, [(p.user.get_full_name(), lambda a=a: mail(a)) for p, a in selected])
        if selected and len(failed) == len(selected):
            # nobody got it (e.g. the mail server is down): nothing else is sent, so trying again sends no duplicates
            connection.close()
            messages.add_message(request, messages.ERROR, "Die E-Mails konnten nicht gesendet werden – bitte später nochmal versuchen.")
        else:
            info_to = form.cleaned_data["info_to"]  # the chips left in the form, only from the offered addresses
            failed_info = send_each(connection, [(address, lambda address=address: mail([address])) for address in info_to])
            connection.close()
            missing = len(recipients) - len(reachable)
            text = f"E-Mail an {len(selected) - len(failed)} Teilnehmende gesendet"
            if missing:
                text += f" ({missing} ohne E-Mail-Adresse)"
            if failed or failed_info:
                text += f"; nicht an {', '.join(failed + failed_info)}"
            if can_notice and form.cleaned_data.get("notice"):
                notice = Message.objects.create(title=subject, message=body, author=request.user, display="sessions",
                                                autodelete=datetime.now() + timedelta(days=3))
                notice.sessions.add(session)
                text += ", Hinweis bei der Trainingszeit angelegt"
            messages.add_message(request, messages.WARNING if failed or failed_info else messages.SUCCESS, text)
            return HttpResponseRedirect(reverse("trainer_group_detail", args=[session.pk]))
    return render(request, "trainer/training_group_email.html", {
        "object": session, "form": form,
        "prefix": GROUP_EMAIL_PREFIX, "greeting": GROUP_EMAIL_GREETING, "sender": request.user.get_full_name(), "session": session,
        **group_email_context(addresses, recipients, form),
    })


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
    template_name = "accounts/trainer_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # deactivated trainers keep their data (see TrainerDeleteView), listed collapsed below
        context["inactive_trainers"] = Trainer.objects.filter(active=False).select_related("user").order_by("user__last_name")
        return context

class TrainerDeleteView(LoginRequiredMixin, BoardRequiredMixin, DeleteView):
    """Deactivates straight from the list, without a confirmation page: it can be undone
    in the "Inaktive Trainer*innen" section below the list."""

    model = Trainer
    http_method_names = ["post"]

    def form_valid(self, form):
        # deactivate instead of delete, see member_role in accounts/views.py
        if conflict := self.object.schedule_conflict():
            messages.add_message(self.request, messages.ERROR, conflict)
            return HttpResponseRedirect(reverse("trainer_list"))
        self.object.active = False
        self.object.save()
        messages.add_message(self.request, messages.SUCCESS, f"{self.object.user.get_full_name()} deaktiviert")
        return HttpResponseRedirect(reverse("trainer_list"))

class TrainerUpdateView(LoginRequiredMixin, BoardRequiredMixin, UpdateView):
    model = Trainer
    form_class = TrainerForm
    template_name = "trainer/trainer_form.html"

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
