"""Breadcrumbs that follow where someone came from.

Some pages are reached from several places: a training group from the trainer document, the board
dashboard or the members page; a training session from the trainer's tables, a training group, a trial
group or the invoice list. Their links carry the trail as ?von=<area>/<step>/<step>…, for example
"trainer/gruppen/gruppe:4". A page shows that trail as its breadcrumbs and passes it on, with itself
added, to the pages it links to (template: ?von={{ von_next|urlencode }}).

Areas are the roots (AREAS). Steps are fixed pages (PAGES, "probetraining") or object pages:
gruppe:<training time>, probe:<trial group>, stunde:<training session entry>. Anything unknown or
deleted is dropped, so an edited ?von= can only shorten the trail, never point somewhere else.
"""
import re
from urllib.parse import urlencode

from django.urls import reverse

AREAS = {
    "trainer": ("Trainerdokument", "trainer_index"),
    "vorstand": ("Vorstand", "chairman_index"),
    "mitglieder": ("Mitglieder", "index"),
}

PAGES = {
    "tabellen": ("Trainingstabellen", "trainer_index"),
    "gruppen": ("Trainingsgruppen", "trainer_groups"),
    "daten": ("Meine Daten", "trainer_data"),
    "anmeldungen": ("Anmeldungen", "tester_list"),
    "rechnungen": ("Trainingsstunden & Rechnungen", "trainingsession_list"),
    "trainerliste": ("Trainerliste", "trainer_list"),
    "mitgliederliste": ("Mitgliederliste", "member_list"),  # the board's dashboard is below it
}

OBJECT_STEP = re.compile(r"^(gruppe|probe|stunde):(\d+)$")

# longer trails lose their oldest steps (the area always stays)
MAX_STEPS = 6


def with_von(url, von):
    """The url with ?von=<trail>; a #fragment stays at the end."""
    if not von:
        return url
    url, hash_, fragment = url.partition("#")
    return f"{url}{'&' if '?' in url else '?'}{urlencode({'von': von})}{hash_}{fragment}"


def entry_label(entry):
    """A training session entry in breadcrumbs and titles: "Erwachsene, 12.11.2026"."""
    name = entry.group or (entry.session.title if entry.session_id else "") or "Trainingsstunde"
    return f"{name}, {entry.date:%d.%m.%Y}" if entry.date else name


def parse(raw):
    """(area, steps) from a trail, or None if it does not start with a known area."""
    parts = [part for part in (raw or "").split("/") if part]
    if not parts or parts[0] not in AREAS:
        return None
    steps = [step for step in parts[1:] if step in PAGES or step == "probetraining" or OBJECT_STEP.match(step)]
    return parts[0], steps


def resolve(area, step, trail):
    """(label, url) of a step; the url carries the trail up to it. None if the object is gone."""
    if step in PAGES:
        label, name = PAGES[step]
        return label, with_von(reverse(name), trail)
    if step == "probetraining":
        # trainers have their trial trainings as a section of the groups page, the board its dashboard
        if area == "trainer":
            return "Probetraining", reverse("trainer_groups") + "#probetraining"
        return "Probetraining", with_von(reverse("tester_index"), trail)
    kind, pk = OBJECT_STEP.match(step).groups()
    # imported here: this module is used by the apps whose models these are
    if kind == "gruppe":
        from members.models import Session
        obj = Session.objects.filter(pk=pk).first()
        return (obj.title, with_von(reverse("trainer_group_detail", args=[pk]), trail)) if obj else None
    if kind == "probe":
        from public.models import TrialGroup
        obj = TrialGroup.objects.filter(pk=pk).first()
        return (str(obj), with_von(reverse("trial_group_detail", args=[pk]), trail)) if obj else None
    from trainer.models import TrainingSessionEntry
    obj = TrainingSessionEntry.objects.select_related("session").filter(pk=pk).first()
    return (entry_label(obj), with_von(reverse("trainingsession_detail", args=[pk]), trail)) if obj else None


def trail(request, default, current, step=None, fixed=False):
    """Breadcrumb context for a page.

    default: the trail when the link carried none (or a broken one), e.g. a bookmark.
    current: the page's own label (the last, unlinked crumb).
    step: the page itself as a step, if pages it links to should show it in their trail.
    fixed: always use the default (the trainer document's tabs are only reached one way).

    Returns breadcrumbs [(label, url)], breadcrumb_current, von (the trail that led here, for forms
    and redirects that come back to this page), von_next (for links to the next pages) and back_url
    (the page before this one, e.g. to return to after saving).
    """
    raw = None if fixed else (request.GET.get("von") or request.POST.get("von"))
    area, steps = parse(raw) or parse(default)
    if step in steps:
        steps = steps[:steps.index(step)]  # back at a page that is already on the trail: back up to it
    steps = steps[-MAX_STEPS:]
    crumbs = [(AREAS[area][0], reverse(AREAS[area][1]))]
    kept = [area]
    for part in steps:
        resolved = resolve(area, part, "/".join(kept))
        if resolved:
            crumbs.append(resolved)
            kept.append(part)
    von = "/".join(kept)
    return {
        "breadcrumbs": crumbs,
        "breadcrumb_current": current,
        "von": von,
        "von_next": f"{von}/{step}" if step else von,
        "back_url": crumbs[-1][1],
    }
