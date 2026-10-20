import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django import forms
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from .models import (
    is_trainer,
    is_chairman,
    Event,
    Profile,
    Chairman,
    Session,
    Spot,
    Message,
    News,
    AdditionalEmail,
    ShopItem,
    Image,
    Gallery,
    MemberParticipant,
    Document,
    EventAsset,
)
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    UserPassesTestMixin,
    PermissionRequiredMixin,
)
from .forms import (
    EventUpdateParticipantForm,
    EventUpdateParticipantForm2,
    SessionForm,
    EventForm,
    UpdateMemberInformationForm,
    UpdateMemberEmailForm,
    SpotForm,
    MessageForm,
    EventFileForm,
)
from django.contrib import messages
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.views import PasswordChangeView
from django.conf import settings
from django.utils.text import slugify
import markdown

# Create your views here.
import os


def chairman_check(request):
    user = request.user
    return is_chairman(user) or user.is_superuser


def trainer_check(request):
    user = request.user
    return is_trainer(user) or user.is_superuser


def past_events_q():
    # same rule as Event.is_past_due: over for more than 3 days
    return Q(end_date__lt=datetime.now() - timedelta(days=3))


def prepare_event_cards(request, events):
    """Adds what the event cards need; members see all events, the ones outside their age greyed out."""
    privileged = is_trainer(request.user) or is_chairman(request.user)
    age = request.user.profile.age
    events = list(events)
    for event in events:
        event.visible = privileged or event.allows_age(age)
        event.is_participant = request.user in event.participant_users
        # every event the member may see opens its detail page, past ones included
        event.can_open = event.visible
        # titles of the notices linked to this event, shown on its card
        event.notices = [notice.title for notice in event.messages.all()] if event.visible else []
    return events


PAST_EVENTS_PER_PAGE = 4  # one row


@login_required
def past_events(request):
    """The "Vergangene Veranstaltungen" button: the next batch of past event cards, newest first."""
    offset = int(request.GET.get("offset", 0)) if request.GET.get("offset", "").isdigit() else 0
    past = Event.objects.filter(past_events_q()).order_by("-start_date").prefetch_related("messages")
    events = prepare_event_cards(request, past[offset:offset + PAST_EVENTS_PER_PAGE])
    next_offset = offset + PAST_EVENTS_PER_PAGE
    return render(request, "members/snippets/past_events.html", {
        "events": events,
        "next_offset": next_offset if past.count() > next_offset else None,
        "first_batch": offset == 0,
    })


@login_required
def index(request):
    """This is the View for the homepage"""
    # TODO: meet with martin and implement django-crontabs. this is hardly an acceptable soultion -.-
    # we never have more than 1-2 messages, so thats okay for now
    for msg in Message.objects.all():
        if msg.delme:
            msg.delete()

    # now the actual view
    age = request.user.profile.age
    privileged = is_trainer(request.user) or is_chairman(request.user)
    notices = Message.objects.all() if privileged else Message.visible_for_age(age)

    # all upcoming events are listed, the ones outside the member's age are greyed out
    events = prepare_event_cards(request, Event.objects.exclude(past_events_q()).prefetch_related("messages"))
    training_messags = notices.filter(display="sessions")
    event_messags = notices.filter(display="events")
    chairmen = Chairman.objects.filter(active=True, show__contains="member_site")

    posts = News.objects.all().order_by("-id")[:3]

    # all sessions are listed, the ones outside the member's age are greyed out
    sessions = list(Session.objects.prefetch_related("messages").order_by("start_time"))
    for session in sessions:
        session.visible = privileged or session.allows_age(age)
        # titles of the notices linked to this session, shown as a small warning sign
        session.notices = [notice.title for notice in session.messages.all()]
    session_days = sorted({(x.day, x.weekday, x.order) for x in sessions}, key=lambda x: x[2])
    grouped_sessions = {short: [x for x in sessions if x.day == short] for short, _, _ in session_days}

    return render(
        request,
        "members/index.html",
        {
            "chairmen": chairmen,
            "sessions": grouped_sessions,
            "session_days": session_days,
            "events": events,
            "has_past_events": Event.objects.filter(past_events_q()).exists(),
            "training_messags": training_messags,
            "event_messags": event_messags,
            "chairman": is_chairman(request.user),
            "posts": posts,
            "spots": spot_map_data(sessions, for_editors=request.user.has_perm("members.change_spot")),
        },
    )


"""FOR THE EVENTS"""


def event_test_func(request, event):
    if bool(trainer_check(request) or chairman_check(request)):
        return True
    return Event.visible_for_age(request.user.profile.age).filter(pk=event.pk).exists()


class EventListView(LoginRequiredMixin, ListView, UserPassesTestMixin):
    model = Event
    template = "members/event_list.html"

    def test_func(self):
        return self.request.user.profile.privileged


class EventDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    # template: event_detail.html
    model = Event

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        part = MemberParticipant.objects.filter(event=self.object, user=user).first()
        is_participant = part is not None and not part.storno
        context.update(
            part=part,
            is_participant=is_participant,
            # expired notices are only cleaned up on the members page
            notices=[notice for notice in self.object.messages.all() if not notice.delme],
            # the meeting point is meant for the people who come along
            show_meeting_point=is_participant or trainer_check(self.request) or chairman_check(self.request),
        )
        return context

    def test_func(self):
        event = self.get_object()
        return event_test_func(self.request, event)


class EventCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    # template: event_detail.html
    model = Event
    form_class = EventForm
    permission_required = "members.add_event"

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, "Veranstaltung erstellt")
        return super().form_valid(form)


class EventUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    # template: event_detail.html
    model = Event
    form_class = EventForm
    # who can update the event?
    permission_required = "members.change_event"


    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, "Veranstaltung geändert")
        return super().form_valid(form)


# allowed uploads in the event editor; no HTML or SVG, the media folder is served from our domain
EVENT_UPLOAD_TYPES = {
    EventAsset.IMAGE: {".jpg", ".jpeg", ".png", ".gif", ".webp"},
    EventAsset.FILE: {".pdf", ".doc", ".docx", ".odt", ".xls", ".xlsx", ".ods", ".ppt", ".pptx", ".odp",
                      ".txt", ".csv", ".zip", ".jpg", ".jpeg", ".png"},
}
EVENT_UPLOAD_MAX_MB = {EventAsset.IMAGE: 10, EventAsset.FILE: 20}


def check_event_upload(kind, upload):
    """Returns an error message, or None if the upload is fine."""
    if upload is None:
        return "Keine Datei erhalten."
    if os.path.splitext(upload.name)[1].lower() not in EVENT_UPLOAD_TYPES[kind]:
        return "Dieser Dateityp ist nicht erlaubt."
    if upload.size > EVENT_UPLOAD_MAX_MB[kind] * 1024 * 1024:
        return f"Die Datei ist größer als {EVENT_UPLOAD_MAX_MB[kind]} MB."
    if kind == EventAsset.IMAGE:
        try:
            forms.ImageField().clean(upload)
        except ValidationError:
            return "Die Datei ist kein gültiges Bild."
    return None


@login_required
@require_POST
def event_asset_upload(request, kind):
    """Upload endpoint for the image and file blocks of the event editor (Editor.js response format)."""
    if kind not in EVENT_UPLOAD_TYPES:
        raise Http404
    user = request.user
    if not (user.has_perm("members.add_event") or user.has_perm("members.change_event")):
        return JsonResponse({"success": 0, "message": "Keine Berechtigung."}, status=403)
    upload = request.FILES.get("file")
    if error := check_event_upload(kind, upload):
        return JsonResponse({"success": 0, "message": error}, status=400)

    asset = EventAsset.objects.create(kind=kind, file=upload, name=upload.name[:200])
    if kind == EventAsset.IMAGE:
        asset.shrink_image()
    # uploads that never made it into a saved event
    for orphan in EventAsset.objects.filter(event=None, uploaded__lt=datetime.now() - timedelta(days=1)):
        orphan.delete()

    file = {"url": asset.file.url}
    if kind == EventAsset.FILE:
        file.update(name=asset.name, size=asset.file.size, extension=os.path.splitext(asset.name)[1].lstrip(".").lower())
    return JsonResponse({"success": 1, "file": file})


class EventDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Event
    # success_url = "/mitglieder/#events"
    # who can delete the event?
    permission_required = "members.delete_event"

    def get_success_url(self, **kwargs):
        return reverse("index") + "#events"


class EventParticipateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    template_name = "members/event_participate.html"
    form_class = EventUpdateParticipantForm
    model = Event

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            event = self.get_object()
            user = request.user
            part, created = MemberParticipant.objects.get_or_create(
                event=event,
                user=user,
            )
            if form.cleaned_data.get("ticket", False):
                part.has_ticket = True

            if created == False:  # was storno before
                part.storno = False

            part.save()

            messages.add_message(
                request, messages.SUCCESS, "Du hast dich erfolgreich angemeldet"
            )
            return HttpResponseRedirect(
                reverse("event_detail", kwargs={"pk": event.id})
            )
        return render(
            request, self.template_name, {"form": form, "object": self.get_object()}
        )

    def test_func(self):
        event = self.get_object()
        return event_test_func(self.request, event)


class EventUnParticipateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    template_name = "members/event_unparticipate.html"
    form_class = EventUpdateParticipantForm2
    model = Event

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            user = request.user
            event = self.get_object()

            try:  # the very edge-case that in a legacy event people unparticipate before being converted to new participants
                part = MemberParticipant.objects.get(event=event, user=request.user)
                part.storno = True
                part.save()
            except:
                pass

            # because of legacy reasons
            if user in event.participants.all():
                event.participants.remove(user)
                event.save()

            messages.add_message(
                request, messages.SUCCESS, "Du hast dich erfolgreich abgemeldet"
            )
            return HttpResponseRedirect(
                reverse("event_detail", kwargs={"pk": event.id})
            )
        return render(request, self.template_name, {"form": form})

    def test_func(self):
        event = self.get_object()
        return event_test_func(self.request, event)


class EventOrgaView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Participants, payments and documents of an event; for trainers and chairmen."""

    model = Event
    template_name = "members/event_organisation.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.object
        # older events kept their participants in Event.participants: convert them once
        known = set(MemberParticipant.objects.filter(event=event).values_list("user_id", flat=True))
        for user in event.participants.all():
            if user.pk not in known:
                MemberParticipant.objects.create(user=user, event=event)
            event.participants.remove(user)

        participants = list(
            MemberParticipant.objects.filter(event=event).select_related("user__profile")
            .order_by("storno", "user__last_name", "user__first_name")
        )
        active = [p for p in participants if not p.storno]
        context.update(
            participants=participants,
            count_active=len(active),
            count_payed=sum(p.payed for p in active),
            count_ticket=sum(p.has_ticket for p in active),
            count_storno=len(participants) - len(active),
            form=kwargs.get("form") or EventFileForm(),
        )
        return context

    def post(self, request, *args, **kwargs):
        """Uploads a document: public (shown on the event page) or only for the orga."""
        self.object = self.get_object()
        form = EventFileForm(request.POST, request.FILES)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))
        doc = form.save(commit=False)
        if form.cleaned_data["orga"]:
            doc.event_orga = self.object
        else:
            doc.event_public = self.object
        doc.save()
        messages.add_message(request, messages.SUCCESS, "Dokument hochgeladen")
        return redirect("event_participants", pk=self.object.pk)

    def test_func(self):
        return trainer_check(self.request) or chairman_check(self.request)


@login_required
def event_participants_csv(request, pk):
    """Participant list as CSV (semicolons, so Excel opens it directly)."""
    if not (trainer_check(request) or chairman_check(request)):
        raise PermissionDenied
    event = get_object_or_404(Event, pk=pk)
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="teilnehmende-{slugify(event.title)}.csv"'
    response.write("\ufeff")  # BOM: Excel recognises the umlauts
    writer = csv.writer(response, delimiter=";")
    writer.writerow(["Nr.", "Nachname", "Vorname", "Geburtsdatum", "Alter", "E-Mail", "Telefon",
                     "Ansprechpartner*in", "Notfallnummer", "Bezahlt", "Deutschlandticket", "Storniert", "Notizen"])
    participants = MemberParticipant.objects.filter(event=event).select_related("user__profile").order_by(
        "storno", "user__last_name", "user__first_name")
    for p in participants:
        user, profile = p.user, getattr(p.user, "profile", None)
        writer.writerow([
            getattr(profile, "member_num", ""), user.last_name, user.first_name,
            profile.birthday.strftime("%d.%m.%Y") if profile and profile.birthday else "", getattr(profile, "age", "") or "",
            user.email, getattr(profile, "telephone", "") or "", getattr(profile, "parent", "") or "",
            getattr(profile, "parent_telnr", "") or "",
            "ja" if p.payed else "nein", "ja" if p.has_ticket else "nein", "ja" if p.storno else "nein", p.notes or "",
        ])
    return response


@login_required
@require_POST
def ajax_event_filehandle(request):
    """Orga page: switch a document between public and orga-only, or delete it."""
    if not (trainer_check(request) or chairman_check(request)):
        return JsonResponse({"success": False}, status=403)
    doc = get_object_or_404(Document, pk=request.POST.get("id"))
    if request.POST.get("type") == "toggle":
        doc.event_toggle()
    elif request.POST.get("type") == "delete":
        doc.file.delete(save=False)
        doc.delete()
    return JsonResponse({"success": True})


## Ajax Event Orga Stuff
@login_required
@require_POST
def update_memberparticipant(request):
    """Orga page: trainers/chairmen edit payed, notes and ticket; participants only their own ticket."""
    part = get_object_or_404(MemberParticipant, pk=request.POST.get("id"))
    field = request.POST.get("field")
    is_orga = trainer_check(request) or chairman_check(request)
    own_ticket = field == "has_ticket" and part.user == request.user and not part.event.deadline_reached
    if field not in ["payed", "has_ticket", "notes"] or not (is_orga or own_ticket):
        return JsonResponse({"success": False}, status=403)

    check, text = request.POST.get("value", "").split(",", 1)
    setattr(part, field, check == "true" if field in ["payed", "has_ticket"] else text)
    part.save(update_fields=[field])
    return JsonResponse({"success": True})


"""FOR THE SESSIONS"""
# this happens just in the background, no return value...
def session_participation_toggle(request):
    session = Session.objects.get(pk=int(request.GET.get('pk')))
    user = request.user
    if user.profile in session.participants.all():
        session.participants.remove(user.profile)
    else:
        session.participants.add(user.profile)
    return JsonResponse({"success": True})


class SessionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Session
    form_class = SessionForm
    permission_required = "members.add_session"

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, "Einheit erstellt")
        return super().form_valid(form)


class SessionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Session
    form_class = SessionForm
    permission_required = "members.change_session"

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, "Einheit geändert")
        return super().form_valid(form)


class SessionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Session
    permission_required = "members.delete_session"

    def post(self, request, *args, **kwargs):
        messages.add_message(request, messages.SUCCESS, "Einheit gelöscht")
        return self.delete(request, *args, **kwargs)

    def get_success_url(self, **kwargs):
        return reverse("index") + "#training"


"""FOR THE SPOTS"""

# after changing a spot, go back to the dashboard with the map open
SPOT_MAP_URL = reverse_lazy("index")


class SpotCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Spot
    form_class = SpotForm
    permission_required = "members.add_spot"

    def get_initial(self):
        # "Neuer Spot" on the map passes the clicked position
        return {key: self.request.GET[key] for key in ("lat", "long") if key in self.request.GET}

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, "Spot angelegt")
        return super().form_valid(form)

    def get_success_url(self):
        return f"{SPOT_MAP_URL}?karte=1"


class SpotUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Spot
    form_class = SpotForm
    permission_required = "members.change_spot"

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, "Spot geändert")
        return super().form_valid(form)

    def get_success_url(self):
        return f"{SPOT_MAP_URL}?karte=1"


class SpotDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Spot
    permission_required = "members.delete_spot"

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, "Spot gelöscht")
        return super().form_valid(form)

    def get_success_url(self):
        return f"{SPOT_MAP_URL}?karte=1"


@login_required
@permission_required("members.change_spot", raise_exception=True)
@require_POST
def spot_move(request, pk):
    """Saves a new position after a marker was dragged on the map."""
    spot = get_object_or_404(Spot, pk=pk)
    form = SpotForm({"title": spot.title, "description": spot.description,
                     "lat": request.POST.get("lat"), "long": request.POST.get("long")}, instance=spot)
    if not form.is_valid():
        return JsonResponse({"errors": form.errors}, status=400)
    form.save()
    return JsonResponse({"lat": float(spot.lat), "long": float(spot.long)})


def spot_map_data(sessions, for_editors):
    """All spots for the map; training times and edit links only for those who manage spots."""
    by_spot = {}
    for session in sessions:
        if session.spot_id:
            by_spot.setdefault(session.spot_id, []).append(f"{session.title}, {session.day} {session.format_start_time}")
    spots = []
    for spot in Spot.objects.order_by("title"):
        data = {"id": spot.pk, "title": spot.title, "description": spot.description,
                "lat": float(spot.lat), "long": float(spot.long)}
        if for_editors:
            data.update(
                sessions=by_spot.get(spot.pk, []),
                edit_url=reverse("spot_update", args=[spot.pk]),
                delete_url=reverse("spot_delete", args=[spot.pk]),
                move_url=reverse("spot_move", args=[spot.pk]),
            )
        spots.append(data)
    return spots


"""For the news"""


class NewsListView(LoginRequiredMixin, ListView):
    model = News


class NewsDetailView(LoginRequiredMixin, DetailView):
    model = News


class NewsCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    # template: event_form.html
    model = News
    permission_required = "members.add_news"
    fields = ["title", "capture", "content"]

    def form_valid(self, form):
        self.object = form.save()
        self.object.content_rendered = markdown.markdown(self.object.content)
        messages.add_message(self.request, messages.SUCCESS, "Beitrag erstellt")
        return super().form_valid(form)


class NewsUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    # template: event_form.html
    model = News
    permission_required = "members.change_news"
    fields = ["title", "capture", "content"]

    def form_valid(self, form):
        self.object = form.save()
        self.object.content_rendered = markdown.markdown(self.object.content)
        messages.add_message(self.request, messages.SUCCESS, "Beitrag geändert")
        return super().form_valid(form)


class NewsDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = News
    permission_required = "members.delete_news"

    def post(self, request, *args, **kwargs):
        messages.add_message(request, messages.SUCCESS, "Beitrag gelöscht")
        return self.delete(request, *args, **kwargs)

    def get_success_url(self, **kwargs):
        return reverse("news_list")


"""For The Messages"""


class MessageCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Base for the two kinds of notices; ?session=<pk> or ?event=<pk> starts with that one ticked."""

    model = Message
    form_class = MessageForm
    permission_required = "members.add_message"
    kind = None

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), "kind": self.kind}

    def get_initial(self):
        param = "session" if self.kind == "sessions" else "event"
        return {self.kind: [pk for pk in self.request.GET.getlist(param) if pk.isdigit()]}

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.display = self.kind
        return super().form_valid(form)


class MessageEveCreateView(MessageCreateView):
    kind = "events"


class MessageSessCreateView(MessageCreateView):
    kind = "sessions"


class MessageDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Message
    permission_required = "members.delete_message"

    def get_success_url(self, **kwargs):
        return reverse("index")


class MessageUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Message
    form_class = MessageForm
    permission_required = "members.change_message"

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), "kind": "events" if self.object.display == "events" else "sessions"}

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


"""USER STUFF"""


class UserDetailView(LoginRequiredMixin, UpdateView):
    # TODO: get email for every change in "Hinweis"
    model = User
    template_name = "members/user_detail.html"
    form_class = UpdateMemberInformationForm

    def get_object(self, queryset=None):
        obj = self.request.user
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["additional_emails"] = AdditionalEmail.objects.filter(user=self.object)
        return super().get_context_data(**context)

    def handle_uploaded_file(self, f, name):
        try:
            os.mkdir("media/user_uploads")
        except:
            pass

        with open(f"media/user_uploads/{name}", "wb+") as destination:
            for chunk in f.chunks():
                destination.write(chunk)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            mail_subject = (
                f"Mitteilung von {request.user.first_name} {request.user.last_name}"
            )
            message = form.cleaned_data.get("comment")
            to_email = settings.TO_EMAIL
            email = EmailMessage(
                mail_subject, message, to=[to_email], cc=[request.user.email]
            )
            if request.FILES.get("attachment"):
                document = request.FILES.get("attachment")
                self.handle_uploaded_file(document, str(document))
                email.attach_file("media/user_uploads/" + str(document))
            email.send()
            messages.add_message(
                request, messages.SUCCESS, "Nachricht erfolgreich versendet"
            )
            return HttpResponseRedirect(reverse("profile_detail"))
        return render(request, self.template_name, {"form": form})


class EmailUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    template_name = "members/update_email.html"
    form_class = UpdateMemberEmailForm

    def get_object(self, queryset=None):
        obj = self.request.user
        return obj

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            # check the password
            if request.user.check_password(form.cleaned_data.get("password")):
                # check, if both mails are the same
                if form.cleaned_data.get("email1") == form.cleaned_data.get("email2"):
                    request.user.email = form.cleaned_data.get("email1")
                    request.user.save()
                    messages.add_message(
                        request, messages.SUCCESS, "E-Mail erfolgreich geändert"
                    )
                    return HttpResponseRedirect(reverse("profile_detail"))
                form.add_error("email1", "Die E-Mails stimmen nicht überein")
                return render(
                    request, self.template_name, {"form": form, "object": request.user}
                )
            form.add_error("password", "Das Passwort stimmt nicht")
            return render(
                request, self.template_name, {"form": form, "object": request.user}
            )
        return render(
            request, self.template_name, {"form": form, "object": request.user}
        )

    def test_func(self):
        user = self.request.user
        person = self.get_object()
        return user == person


class PasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = "members/update_pw.html"

    def get_object(self, queryset=None):
        obj = self.request.user
        return obj

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            request.user = form.save()
            update_session_auth_hash(request, request.user)
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = {}
        context["object"] = self.request.user
        context.update(kwargs)
        return super().get_context_data(**context)

    def form_valid(self, form):
        messages.add_message(
            self.request, messages.SUCCESS, "Passwort erfolgreich geändert"
        )
        return HttpResponseRedirect(reverse("profile_detail"))


class UsernameUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = "members/update_username.html"
    fields = ["username"]

    def get_object(self, queryset=None):
        obj = self.request.user
        return obj

    def get_success_url(self):
        messages.add_message(
            self.request, messages.SUCCESS, "Nutzername erfolgreich geändert"
        )
        return reverse("profile_detail")


class AddressChangeView(LoginRequiredMixin, UpdateView):
    model = Profile
    template_name = "members/update_address.html"
    fields = ["address", "telephone", "parent", "parent_telnr"]

    def get_object(self, queryset=None):
        obj = self.request.user.profile
        return obj

    def get_success_url(self):
        return reverse("profile_detail")


class ShopItemDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = ShopItem

    def test_func(self):
        return chairman_check(self.request)

    def get_success_url(self):
        return reverse("shop")


class ShopItemListView(LoginRequiredMixin, ListView):
    model = ShopItem

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["privileged"] = chairman_check(self.request)
        return context

    def get_queryset(self):
        user = self.request.user
        if chairman_check(self.request):
            object_list = ShopItem.objects.all().order_by("priority")
        else:
            object_list = ShopItem.objects.filter(visible=True).order_by("priority")
        return object_list


@login_required
def create_shopitem(request):
    if chairman_check(request):
        gallery = Gallery()
        gallery.save()
        gallery.refresh_from_db()
        item = ShopItem(gallery=gallery, price=10, title="Neu", visible=False)
        item.save()
        item.refresh_from_db()
        return HttpResponseRedirect(reverse("shopitem_update", args=[item.pk]))
    else:
        return HttpResponseRedirect(reverse("shop"))


class ShopItemUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ShopItem
    fields = ["title", "description", "price", "visible", "priority"]

    def test_func(self):
        return chairman_check(self.request)

    def get_success_url(self):
        return reverse("shop")

    def form_valid(self, form):
        self.object = form.save()
        self.object.description_rendered = markdown.markdown(self.object.description)
        return super().form_valid(form)


## AJAX ##
@login_required
def get_image_data(request):
    data = {x: v[0] for (x, v) in dict(request.GET).items()}
    image = Image.objects.get(pk=data["id"])
    return JsonResponse(
        {"data": {"title": image.title, "alt": image.alt, "priority": image.priority}}
    )


@login_required
def set_image_data(request):
    if chairman_check(request):
        data = {x: v[0] for (x, v) in dict(request.GET).items()}
        image = Image.objects.get(pk=data["id"])
        image.alt = data["alt"]
        image.priority = data["prio"]
        image.title = data["title"]
        image.save()
        return JsonResponse(
            {
                "data": {
                    "title": image.title,
                    "alt": image.alt,
                    "priority": image.priority,
                }
            }
        )
    else:
        return JsonResponse({"data": False})


@login_required
def delete_image(request):
    if chairman_check(request):
        data = {x: v[0] for (x, v) in dict(request.GET).items()}
        image = Image.objects.get(pk=data["id"])
        image.delete()
        return JsonResponse({"data": True})
    else:
        return JsonResponse({"data": False})


@csrf_exempt
@login_required
def add_image(request):
    img = request.FILES["files[]"]
    obj = ShopItem.objects.get(pk=request.POST["object_id"])
    gallery = obj.gallery
    new = Image(image=img, gallery=gallery, priority=999, title="unset")
    new.save()
    new.refresh_from_db()
    return JsonResponse({"url": new.image.url, "pk": new.pk})


@login_required
def add_another_email(request):
    data = request.POST
    user = request.user
    data = {k: v[0] for (k, v) in dict(request.POST).items()}
    email = AdditionalEmail.objects.create(
        user=user, title=data["title"], email=data["email"]
    )
    email.save()
    return JsonResponse({"data": data})


@login_required
def delete_additional_email(request):
    data = {x: v[0] for (x, v) in dict(request.GET).items()}
    user = request.user
    email = AdditionalEmail.objects.get(user=user, pk=int(data["id"]))
    email.delete()
    return JsonResponse({"data": data})


@permission_required("auth.add_user", raise_exception=True)
@require_POST
def delete_additional_email_chair(request, pk):
    email = get_object_or_404(AdditionalEmail, user__pk=pk, pk=request.POST.get("id"))
    email.delete()
    return JsonResponse({"data": True})
