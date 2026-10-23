"""Trial groups: who is expected when, and who actually came.

Attendance is not stored separately: it comes from the training session entries the
trainers fill in. A trial participant counts as present on a trial date when they are
a participant (linked via TrainingSessionParticipant.tester) of an entry for that
training time on that day.
"""
from datetime import date, datetime

from django.db.models import Count

from trainer.models import TrainingSessionEntry, TrainingSessionParticipant

from .models import Tester, TrialDate, TrialGroup



def weekday_matches(trial_date):
    """The date falls on the weekday of its training time (Session.day_key: Mo = 1)."""
    return trial_date.session.day_key - 1 == trial_date.date.weekday()


def expected_testers(entry):
    """Trial participants whose group has a trial date for this training session entry."""
    if not entry.session_id or not entry.date:
        return Tester.objects.none()
    return Tester.objects.filter(
        trial_group__trial_dates__session=entry.session_id,
        trial_group__trial_dates__date=entry.date.date(),
    ).distinct().order_by("first_name", "last_name")


def group_attendance(group):
    """Rows for the attendance table of a group.

    Returns (dates, rows): rows are (tester, [status per date]) with status True (came),
    False (an entry exists for that date, but without them) or None (no entry yet).
    """
    dates = list(group.trial_dates.select_related("session"))
    testers = list(group.testers.order_by("last_name", "first_name"))
    entries = {
        d.pk: [e.pk for e in TrainingSessionEntry.objects.filter(session=d.session_id, date__date=d.date).order_by("pk")]
        for d in dates
    }
    for d in dates:
        d.entry_pk = entries[d.pk][0] if entries[d.pk] else None  # the training session entered for this date
    present = set(
        TrainingSessionParticipant.objects.filter(tester__in=testers, session__in=[pk for pks in entries.values() for pk in pks])
        .values_list("tester_id", "session_id")
    )
    rows = []
    for tester in testers:
        statuses = []
        for d in dates:
            if not entries[d.pk]:
                statuses.append(None)
            else:
                statuses.append(any((tester.pk, entry) in present for entry in entries[d.pk]))
        rows.append((tester, statuses))
    return dates, rows


def attended_trainings(tester):
    """Every training the person was entered in as trial participant, independent of their (current) group."""
    return (
        TrainingSessionParticipant.objects.filter(tester=tester)
        .select_related("session__session")
        .order_by("session__date")
    )


def upcoming_trial_dates(user, board):
    """Trial dates from today on: all of them for the board, a trainer only sees their own training times."""
    dates = TrialDate.objects.filter(date__gte=date.today()).select_related("group", "session").prefetch_related("group__testers")
    if not board:
        trainer = getattr(user, "trainer", None)
        dates = dates.filter(session__trainer=trainer) if trainer else dates.none()
    return dates.distinct()


def trainer_trial_groups(trainer):
    """Groups with at least one date at one of the trainer's training times, latest first.

    Every date gets .own (at one of the trainer's training times), the group .next_date (next date from today on).
    """
    groups = list(
        TrialGroup.objects.filter(trial_dates__session__trainer=trainer).distinct()
        .prefetch_related("trial_dates__session__trainer", "testers")
    )
    today = date.today()
    for group in groups:
        group.dates = list(group.trial_dates.all())
        for d in group.dates:
            d.own = trainer in d.session.trainer.all()
        upcoming = [d.date for d in group.dates if d.date >= today]
        group.next_date = min(upcoming) if upcoming else None
        group.last_date = max(d.date for d in group.dates)
    # groups that still come first (by their next date), then finished ones (latest first)
    return sorted(groups, key=lambda g: (g.next_date is None, g.next_date or date.min, -g.last_date.toordinal()))


def finished_testers():
    """Everyone in a group whose trial dates are all over, with .visits; the ones without outcome first."""
    finished = TrialGroup.objects.filter(trial_dates__isnull=False).exclude(trial_dates__date__gte=date.today())
    return (
        Tester.objects.filter(trial_group__in=finished)
        .annotate(visits=Count("attendances"))
        .select_related("trial_group")
        .order_by("outcome", "last_name", "first_name")  # empty (open) sorts first
    )


def mark_member(first_name, last_name, birthday):
    """Trial requests of someone who is a member now (same name and birthday) get the outcome "Mitglied"."""
    if not (first_name and last_name and birthday):
        return
    if isinstance(birthday, datetime):  # Profile.birthday is a datetime, but forms set a plain date
        birthday = birthday.date()
    Tester.objects.filter(
        first_name__iexact=first_name.strip(), last_name__iexact=last_name.strip(), birthday__date=birthday
    ).exclude(outcome="member").update(outcome="member")
