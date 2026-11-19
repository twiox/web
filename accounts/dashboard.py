"""The board's dashboard below the member list: members by status, the expected contributions,
sex and age, and who trains in which group.

Members are the profiles of active accounts. Contributions are monthly amounts (Profile.beitrag);
a cancelled member pays up to the month of the "Kündigung zum" date (membership_end), paused and
supporting members pay their amount like everyone else.
"""
from collections import Counter
from datetime import date, timedelta

from django.db.models import Count, Max

from members.models import Profile, Session, Trainer
from trainer.models import TrainingSessionEntry, TrainingSessionParticipant

STATUS_ORDER = ["Ordentliches Mitglied", "Förderndes Mitglied", "Pausiertes Mitglied", "Kündigung"]
AGE_BANDS = [("unter 9", 0, 8), ("9–13", 9, 13), ("14–17", 14, 17), ("18–29", 18, 29), ("30–49", 30, 49), ("50+", 50, 200)]
SEXES = [("w", "weiblich"), ("m", "männlich"), ("d", "divers")]
ACTIVE_DAYS = 90  # "active": at a training in the last 3 months


def month_start(day, months_ahead=0):
    month = day.month - 1 + months_ahead
    return date(day.year + month // 12, month % 12 + 1, 1)


def pays_in(profile, month):
    """Pays for this month: an amount above 0, and not cancelled before the month starts."""
    end = profile.membership_end.date() if profile.membership_end else None
    return profile.beitrag > 0 and (end is None or end >= month)


def board_dashboard(today=None):
    today = today or date.today()
    members = list(Profile.objects.filter(user__is_active=True).select_related("user"))

    # 1. members by status, and the next cancellation coming into effect
    by_status = Counter(p.status for p in members)
    statuses = [(s, by_status.get(s, 0)) for s in STATUS_ORDER] + [(s, n) for s, n in by_status.items() if s not in STATUS_ORDER]
    leaving = sorted(p.membership_end.date() for p in members if p.membership_end and p.membership_end.date() >= today)

    # 2. contributions this month, by amount and payment method, and the next six months
    this_month = month_start(today)
    paying = [p for p in members if pays_in(p, this_month)]
    by_amount = Counter(p.beitrag for p in paying)
    by_method = Counter(p.zahlungsart for p in paying)
    forecast = []
    for ahead in range(6):
        month = month_start(today, ahead)
        forecast.append({"month": month, "total": sum(p.beitrag for p in members if pays_in(p, month))})

    # 3. sex and age (age groups; without a birthday counted apart)
    pyramid = []
    for label, low, high in AGE_BANDS:
        band = [p for p in members if p.age is not None and low <= p.age <= high]
        counts = {sex: sum(1 for p in band if p.sex == sex) for sex, _ in SEXES}
        if band or low >= 9:  # "unter 9" only when there is someone
            pyramid.append({"label": label, **counts, "total": len(band)})
    widest = max([max(row["w"], row["m"]) for row in pyramid] + [1])
    for row in pyramid:
        # the longest bar takes 85 % of its side, so the number at its tip always fits
        row["w_pct"], row["m_pct"] = round(row["w"] / widest * 85), round(row["m"] / widest * 85)

    # 4. training: on a training time's list ("Teilnahme"), and at a training in the last 3 months
    on_list = set(Session.participants.through.objects.values_list("profile_id", flat=True))
    # each member's last recorded training: date and entry (for the "Ohne Trainingsgruppe" table)
    last_visit = {}
    for row in (TrainingSessionParticipant.objects.filter(user__isnull=False, session__date__isnull=False)
                .select_related("session__session").order_by("user_id", "-session__date")):
        last_visit.setdefault(row.user_id, row.session)
    last_seen = {user_id: entry.date for user_id, entry in last_visit.items()}
    since = today - timedelta(days=ACTIVE_DAYS)
    active = {p.pk for p in members if last_seen.get(p.user_id) and last_seen[p.user_id].date() >= since}
    groups = [{"session": s, "count": s.size} for s in
              Session.objects.annotate(size=Count("participants", distinct=True)).order_by("day_key", "start_time")]
    biggest = max([g["count"] for g in groups] + [1])
    for group in groups:
        group["pct"] = round(group["count"] / biggest * 85)
    # active trainers are at the trainings as trainers, not missing from a group
    trainers = set(Trainer.objects.filter(active=True).values_list("user_id", flat=True))
    without_group = [p for p in members if p.pk not in on_list and p.user_id not in trainers]
    for p in without_group:
        p.last_seen = last_seen.get(p.user_id)
        p.last_entry = last_visit.get(p.user_id)
    # the ones who still come to trainings first (they probably never ticked "Teilnahme"), then by name
    without_group.sort(key=lambda p: p.user.last_name)
    without_group.sort(key=lambda p: p.last_seen.timestamp() if p.last_seen else 0, reverse=True)

    weekly = weekly_participation(today)

    return {
        **weekly,
        "members_total": len(members),
        "statuses": statuses,
        "next_leaving": leaving[0] if leaving else None,
        "leaving_count": len(leaving),
        "monthly_total": sum(p.beitrag for p in paying),
        "paying_count": len(paying),
        "by_amount": sorted(by_amount.items()),
        "by_method": by_method.most_common(),
        "forecast": forecast,
        "pyramid": pyramid,
        "sexes": SEXES,
        "sex_totals": {sex: sum(1 for p in members if p.sex == sex) for sex, _ in SEXES},
        "no_birthday": sum(1 for p in members if p.age is None),
        "on_list_count": sum(1 for p in members if p.pk in on_list),
        "active_count": len(active),
        "active_days": ACTIVE_DAYS,
        "groups": groups,
        "without_group": without_group,
    }


WEEKS = 26  # the participation chart: the last half year


def nice_step(top):
    """Clean gridline step for a maximum value: 1, 2, 5, 10, 20, ..."""
    raw, power = max(1, top) / 3, 1
    while power * 10 <= raw:
        power *= 10
    return next(step * power for step in (1, 2, 5, 10) if step * power >= raw)


def weekly_participation(today):
    """Per calendar week: how many distinct members were at a training, how many of them came once,
    twice or three times and more, and how many trainers trained (as trainer or co-trainer). Someone
    who trained in a week counts once, as trainer, even if they also took part somewhere that week.
    Members with an account only (guests and trial participants have none); each Trainingsstunde
    counts once per person, even if it was entered twice."""
    this_monday = today - timedelta(days=today.weekday())
    first_monday = this_monday - timedelta(weeks=WEEKS - 1)
    visits = {}  # (monday, user) -> {entry}
    held = set()  # weeks with recorded attendance (for the averages)
    rows = TrainingSessionParticipant.objects.filter(
        user__isnull=False, session__date__date__gte=first_monday, session__date__date__lte=today
    ).values_list("user", "session_id", "session__date")
    for user_id, entry_id, day in rows:
        monday = day.date() - timedelta(days=day.weekday())
        visits.setdefault((monday, user_id), set()).add(entry_id)
        held.add(monday)
    trained = set()  # (monday, user)
    for through in (TrainingSessionEntry.trainer.through, TrainingSessionEntry.cotrainer.through):
        for user_id, day in through.objects.filter(
            trainingsessionentry__date__date__gte=first_monday, trainingsessionentry__date__date__lte=today
        ).values_list("trainer__user_id", "trainingsessionentry__date"):
            monday = day.date() - timedelta(days=day.weekday())
            trained.add((monday, user_id))  # not in held: a week with only trainers entered has no attendance recorded
    for key in trained:  # counted as trainer that week, not again as participant
        visits.pop(key, None)

    weeks = []
    for n in range(WEEKS):
        monday = first_monday + timedelta(weeks=n)
        counts = [len(entries) for (week, _), entries in visits.items() if week == monday]
        once, twice, more = (sum(1 for c in counts if c == 1), sum(1 for c in counts if c == 2), sum(1 for c in counts if c >= 3))
        trainers = sum(1 for week, _ in trained if week == monday)
        weeks.append({"monday": monday, "week": monday.isocalendar()[1], "members": len(counts),
                      "once": once, "twice": twice, "more": more, "trainers": trainers, "people": len(counts) + trainers})
    top = max([w["people"] for w in weeks] + [1])
    step = nice_step(top)
    top = -(-top // step) * step  # rounded up to the next gridline
    # as text with a dot: in the German locale the template would print "33,3", which CSS does not read
    for w in weeks:
        w["pct"] = {k: f"{w[k] / top * 100:.2f}" for k in ("members", "once", "twice", "more", "trainers")}

    member_weeks = [len(entries) for entries in visits.values()]
    total = len(member_weeks) or 1
    return {
        "weeks": weeks,
        "weeks_count": WEEKS,
        "weeks_ticks": [{"value": v, "pct": f"{v / top * 100:.2f}"} for v in range(0, top + 1, step)],
        "weeks_held": len(held),
        "avg_members_per_week": round(sum(w["members"] for w in weeks if w["monday"] in held) / (len(held) or 1), 1),
        "avg_trainers_per_week": round(sum(w["trainers"] for w in weeks if w["monday"] in held) / (len(held) or 1), 1),
        "avg_visits_per_week": round(sum(member_weeks) / total, 2),
        "share_once": round(sum(1 for c in member_weeks if c == 1) / total * 100),
        "share_twice": round(sum(1 for c in member_weeks if c == 2) / total * 100),
        "share_more": round(sum(1 for c in member_weeks if c >= 3) / total * 100),
    }
