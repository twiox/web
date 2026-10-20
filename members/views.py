from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
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
    Trainer,
    Spot,
    Message,
    News,
    AdditionalEmail,
    ShopItem,
    Image,
    Gallery,
    MemberParticipant,
    Document,
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
    EventFileForm,
)
from django.contrib import messages
from datetime import datetime
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.views import PasswordChangeView
from django.conf import settings
import markdown

# Create your views here.
import os


def chairman_check(request):
    user = request.user
    return is_chairman(user) or user.is_superuser


def trainer_check(request):
    user = request.user
    return is_trainer(user) or user.is_superuser


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
    if privileged:
        events = Event.objects.all()
        notices = Message.objects.all()
    else:
        events = Event.visible_for_age(age)
        notices = Message.visible_for_age(age)
    training_messags = notices.filter(display="sessions")
    event_messags = notices.filter(display="events")
    chairmen = Chairman.objects.filter(active=True, show__contains="member_site")

    posts = News.objects.all().order_by("-id")[:3]

    # all sessions are listed, the ones outside the member's age are greyed out
    sessions = list(Session.objects.order_by("start_time"))
    for session in sessions:
        session.visible = privileged or session.allows_age(age)
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
            "training_messags": training_messags,
            "event_messags": event_messags,
            "chairman": is_chairman(request.user),
            "posts": posts,
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
        context = super(EventDetailView, self).get_context_data(**kwargs)
        try:
            tmp = {
                "part": MemberParticipant.objects.get(
                    event=self.object, user=self.request.user
                )
            }
        except:
            tmp = {}
        context.update(tmp)
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
        self.object = form.save()
        self.object.description_rendered = markdown.markdown(self.object.description)
        messages.add_message(self.request, messages.SUCCESS, "Veranstaltung erstellt")
        return super().form_valid(form)


class EventUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    # template: event_detail.html
    model = Event
    form_class = EventForm
    # who can update the event?
    permission_required = "members.change_event"


    def form_valid(self, form):
        self.object = form.save()
        self.object.description_rendered = markdown.markdown(self.object.description)
        messages.add_message(self.request, messages.SUCCESS, "Veranstaltung geändert")
        return super().form_valid(form)


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
    model = Event
    template_name = "members/event_organisation.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        # get a list of event participants
        participants = list(MemberParticipant.objects.filter(event=self.object))
        # for older events - convert participants to MemberParticipants
        check = set([x.user for x in participants])
        for user in self.object.participants.all():
            if user not in check:
                tmp = MemberParticipant(user=user, event=self.object)
                tmp.save()
                participants.append(tmp)
                # remove from the legacy-list
                self.object.participants.remove(user)

        # update context
        context.update(
            {
                "participants": sorted(participants, key=lambda x: x.user.first_name),
                "form": EventFileForm(request.POST, request.FILES),
            }
        )
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        event = self.get_object()
        file = request.FILES.get("file")
        name = request.POST.get("name")
        if private := request.POST.get("orga") == "private":
            tmp = Document(file=file, event_orga=event, name=name)
        else:
            tmp = Document(file=file, event_public=event, name=name)
        tmp.save()
        return redirect(request.META["HTTP_REFERER"])

    def test_func(self):
        return trainer_check(self.request) or chairman_check(self.request)


def ajax_event_filehandle(request):
    doc = Document.objects.get(pk=int(request.POST.get("id")))
    if request.POST.get("type") == "toggle":
        doc.event_toggle()
    if request.POST.get("type") == "delete":
        doc.delete()
    return JsonResponse({"success": True})


## Ajax Event Orga Stuff
def update_memberparticipant(request):
    part = MemberParticipant.objects.get(pk=request.POST.get("id"))
    field = request.POST.get("field")
    check, text = request.POST.get("value").split(",", 1)
    if field in ["payed", "has_ticket"]:
        val = check == "true"
    else:
        val = text

    setattr(part, field, val)
    part.save()

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


class SpotListView(LoginRequiredMixin, ListView):
    model = Spot


class SpotDetailView(LoginRequiredMixin, DetailView):
    model = Spot

    def get_context_data(self, **kwargs):
        context = {"api_key": settings.GOOGLE_API_KEY}
        if self.object:
            context["object"] = self.object
            context_object_name = self.get_context_object_name(self.object)
            if context_object_name:
                context[context_object_name] = self.object
        context.update(kwargs)
        return super().get_context_data(**context)


class SpotCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    # template: event_form.html
    model = Spot
    form_class = SpotForm
    permission_required = "members.add_spot"

    def form_valid(self, form):
        self.object = form.save()
        self.object.description_rendered = markdown.markdown(self.object.description)
        messages.add_message(self.request, messages.SUCCESS, "Spot geändert")
        return super().form_valid(form)


class SpotUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    # template: event_form.html
    model = Spot
    form_class = SpotForm
    permission_required = "members.change_spot"

    def form_valid(self, form):
        self.object = form.save()
        self.object.description_rendered = markdown.markdown(self.object.description)
        messages.add_message(self.request, messages.SUCCESS, "Spot geändert")
        return super().form_valid(form)


class SpotDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Spot
    permission_required = "members.delete_spot"

    def post(self, request, *args, **kwargs):
        messages.add_message(request, messages.SUCCESS, "Spot gelöscht")
        return self.delete(request, *args, **kwargs)

    def get_success_url(self, **kwargs):
        return reverse("spot_list")


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


class MessageEveCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Message
    fields = ["title", "message", "sessions", "autodelete"]
    permission_required = "members.add_message"

    def form_valid(self, form):
        message = form.save()
        message.author = self.request.user
        message.display = "events"
        message.save()
        return super(MessageEveCreateView, self).form_valid(form)


class MessageSessCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Message
    fields = ["title", "message", "sessions", "autodelete"]
    permission_required = "members.add_message"

    def form_valid(self, form):
        message = form.save()
        message.author = self.request.user
        message.display = "sessions"
        message.save()
        return super(MessageSessCreateView, self).form_valid(form)


class MessageDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Message
    permission_required = "members.delete_message"

    def get_success_url(self, **kwargs):
        return reverse("index")


class MessageUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    # template: event_form.html
    model = Message
    fields = ["title", "message", "sessions", "autodelete"]
    permission_required = "members.change_message"

    def get_context_data(self, **kwargs):
        context = {"picked_sessions": list(self.object.sessions.values_list("pk", flat=True))}
        context["object"] = self.get_object()
        context.update(kwargs)
        return super().get_context_data(**context)

    def form_valid(self, form):
        message = form.save()
        message.author = self.request.user
        message.date = datetime.now()
        message.save()
        return super(MessageUpdateView, self).form_valid(form)


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
