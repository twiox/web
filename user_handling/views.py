from .forms import MemberForm, ProfileForm, AdditionalEmailForm
from .permissions import chairman_permissions
from members.models import (
    Group,
    Chairman,
    Profile,
    AdditionalEmail,
    Session,
    Event,
    MemberParticipant,
)
from interested.models import PublicEvent, EventParticipant
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.http import require_POST
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.decorators import (
    permission_required,
    login_required,
    user_passes_test,
)
from django.contrib.auth.models import User
from django.contrib.auth.models import Group as Permission_group
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import DeleteView, UpdateView, CreateView, ListView
from django.contrib.auth.views import (
    PasswordResetView,
    LogoutView,
    PasswordResetConfirmView,
)
from django.urls import reverse
import datetime
import logging
import string
import secrets

logger = logging.getLogger(__name__)


@permission_required("auth.add_user", raise_exception=True)
def index(request):
    return render(request, "user_handling/index.html")


def get_ordering(n):
    try:
        return int(n.profile.member_num)
    except:
        return 0


def get_mandatsref(old_ref):
    try:
        num, y, n = old_ref.split("-", 2)
        year = datetime.datetime.now().year
        return (str(year)[-2:], int(n) + 1)
    except:
        return ("NA", "NA")


# register user
@login_required
@permission_required("auth.add_user", raise_exception=True)
def register(request):
    current_member = User.objects.latest("pk")
    y, num = get_mandatsref(current_member.profile.mandatsref)
    ref = f"{get_ordering(current_member)+1}-{y}-{num}"
    initial = {"member_num": get_ordering(current_member) + 1, "mandatsref": ref}
    if request.method == "POST":
        user_form = MemberForm(request.POST)
        profile_form = ProfileForm(request.POST, initial=initial)
        if user_form.is_valid() and profile_form.is_valid():
            real_user = user_form.save(commit=False)
            real_user.username = (
                user_form.cleaned_data["first_name"].lower()
                + profile_form.cleaned_data["member_num"]
            )
            alphabet = string.ascii_letters + string.digits
            password = "".join(secrets.choice(alphabet) for i in range(8))
            real_user.set_password(password)
            real_user.save()  # fires the signal that creates the profile
            for key, value in profile_form.cleaned_data.items():
                setattr(real_user.profile, key, value)
            real_user.profile.save()
            try:
                send_set_password_email(request, real_user)
            except OSError:  # covers smtplib.SMTPException and DNS/socket errors
                logger.exception("Could not send set-password email to %s", real_user)
                messages.add_message(
                    request,
                    messages.WARNING,
                    "Account angelegt, aber die Email konnte nicht verschickt werden. "
                    "Das Mitglied kann über 'Passwort vergessen' einen Link anfordern.",
                )
            else:
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    "Account angelegt. Das Mitglied bekommt eine Email",
                )
            return redirect("register")
    else:
        user_form = MemberForm()
        profile_form = ProfileForm(initial=initial)
    return render(
        request,
        "user_handling/register.html",
        context={"user_form": user_form, "profile_form": profile_form},
    )


def send_set_password_email(request, user):
    message = render_to_string(
        "user_handling/set_password_email.html",
        {
            "user": user,
            "protocol": request.scheme,
            "domain": get_current_site(request).domain,
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": default_token_generator.make_token(user),
        },
    )
    email = EmailMessage(
        "Dein Account für den Twio Mitgliederbereich", message, to=[user.email]
    )
    email.content_subtype = "html"
    email.send()


class MemberListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = User
    permission_required = "auth.add_user"
    template_name = "user_handling/member_list.html"

    def get_queryset(self):
        users = sorted(User.objects.select_related("profile"), key=get_ordering)
        today = datetime.date.today()
        for user in users:
            birthday = user.profile.birthday
            # the parent contact is only relevant for minors
            user.is_minor = bool(birthday) and (
                today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
            ) < 18
        return users


class UserDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = User
    template_name = "user_handling/user_confirm_delete.html"
    # who can delete the user?
    permission_required = "auth.delete_user"

    def get_success_url(self, **kwargs):
        return reverse("member_list")


@login_required
@permission_required("auth.add_user", raise_exception=True)
def member_update(request, pk):
    real_user = get_object_or_404(User, pk=pk)
    user_form = MemberForm(request.POST or None, instance=real_user)
    profile_form = ProfileForm(request.POST or None, instance=real_user.profile)
    if request.method == "POST" and user_form.is_valid() and profile_form.is_valid():
        user_form.save()
        profile_form.save()
        messages.add_message(request, messages.SUCCESS, "Account erfolgreich bearbeitet")
        return redirect("member_list")
    return render(
        request,
        "user_handling/register.html",
        context={"user_form": user_form, "profile_form": profile_form},
    )


class ChairmanCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    # template: event_detail.html
    model = Chairman
    fields = ["user", "public_telnr", "public_email", "competences", "image", "show"]
    template_name = "user_handling/chairman_form.html"
    permission_required = "members.add_chairman"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["choices"] = [
            (x.pk, f"{x.first_name} {x.last_name} ({x.profile.member_num})")
            for x in User.objects.filter(chairman__id__isnull=True)
        ]
        return context

    def form_valid(self, form):
        self.object = form.save()
        user = self.object.user
        try:
            chairman_group = Permission_group.objects.get(name="Vorstand")
        except:
            chairman_group = Permission_group(name="Vorstand")
            chairman_group.save()
            for perm in chairman_permissions():
                chairman_group.permissions.add(perm)
        finally:
            chairman_group.user_set.add(user)
            chairman_group.save()
            user.save()
        return super().form_valid(form)


class ChairmanDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Chairman
    template_name = "user_handling/chairman_confirm_delete.html"
    permission_required = "members.delete_chairman"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        user = self.object.user
        success_url = self.get_success_url()
        try:
            chairman_group = Permission_group.objects.get(name="Vorstand")
            chairman_group.user_set.remove(user)
            chairman_group.save()
        except:  # if we created chairman via the webiste...
            pass
        self.object.delete()
        return HttpResponseRedirect(success_url)

    def get_success_url(self, **kwargs):
        return reverse("chairman_list")


class ChairmanUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    # template: event_form.html
    model = Chairman
    fields = ["public_telnr", "public_email", "competences", "image", "show"]
    template_name = "user_handling/chairman_form.html"
    permission_required = "members.change_chairman"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["checked_shows"] = [x for x in self.get_object().show]
        return context


class ChairmanListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Chairman
    permission_required = "members.change_chairman"
    template_name = "user_handling/chairman_list.html"


class PasswordResetView(PasswordResetView):
    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        messages.add_message(
            self.request,
            messages.SUCCESS,
            "Email verschickt. Bitte schau in deinen Posteingang",
        )
        return reverse("login")


class LogoutView(LogoutView):
    def get_next_page(self):
        next_page = super(LogoutView, self).get_next_page()
        messages.add_message(self.request, messages.SUCCESS, "Erfolgreich ausgeloggt")
        return next_page


class PasswordResetConfirmView(PasswordResetConfirmView):
    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        messages.add_message(
            self.request,
            messages.SUCCESS,
            "Passwort erstellt. Du kannst dich nun einloggen",
        )
        return reverse("index")


def mailing_lists(request):
    groups = Group.objects.all()
    return render(
        request, "user_handling/mailing-lists.html", context={"groups": groups}
    )


def trainer_or_chairman(user):
    if hasattr(user, "trainer"):
        return True
    if hasattr(user, "chairman"):
        return True
    return False


### AJAX Functions
@user_passes_test(trainer_or_chairman)
def get_participants_emails(request):
    data = {k: v[0] for (k, v) in dict(request.GET).items()}
    emails = []
    if "type" in data:
        event = PublicEvent.objects.get(pk=int(data["id"]))
        for part in EventParticipant.objects.filter(event=event).all():
            emails.append(part.email)
    else:
        event = Event.objects.get(pk=int(request.GET.get("id")))
        for part in MemberParticipant.objects.filter(event=event):
            emails.append(part.user.email)
            query = AdditionalEmail.objects.filter(user=part.user)
            emails.extend([x.email for x in query])
    string = ",".join(set(emails)) if len(emails) > 0 else ""
    return JsonResponse({"string": string})


@user_passes_test(trainer_or_chairman)
def get_all_emails(request):
    data = {k: v[0] for (k, v) in dict(request.GET).items()}
    if data["only_active"] == "true":
        active_only = True
    else:
        active_only = False
    emails = []
    try:  # non-id = status
        group = Group.objects.get(pk=int(data["id"]))
        for profile in Profile.objects.filter(group=group):
            status = profile.status
            if active_only and status != "Ordentliches Mitglied":
                continue
            emails.append(profile.user.email)
            query = AdditionalEmail.objects.filter(user=profile.user)
            emails.extend([x.email for x in query])
        sessions = Session.objects.filter(group=group)
        for session in sessions:
            for trainer in session.trainer.all():
                emails.append(trainer.trainer_email)
    except:
        if data["id"] == "alle":
            for user in User.objects.all():
                emails.append(user.email)
                add_emails = AdditionalEmail.objects.filter(user=user)
                emails.extend([x.email for x in add_emails])
                if hasattr(user, "trainer"):
                    emails.append(user.trainer.trainer_email)
        elif data["id"].startswith("email"):
            _, stat = data["id"].split("_")
            for profile in Profile.objects.filter(status=stat):
                emails.append(profile.user.email)
                query = AdditionalEmail.objects.filter(user=profile.user)
                emails.extend([x.email for x in query])
    string = ",".join(set(emails)) if len(emails) > 0 else "other"
    return JsonResponse({"data": data, "string": string})


@login_required
@permission_required("auth.add_user", raise_exception=True)
def member_detail_form(request, pk):
    user = get_object_or_404(User.objects.select_related("profile"), pk=pk)
    return render(
        request,
        "user_handling/ajax/member_detail.html",
        context={
            "user": user,
            "user_form": MemberForm(instance=user),
            "profile_form": ProfileForm(instance=user.profile),
            # both fields are only required once something is typed, see has_input()
            "email_form": AdditionalEmailForm(prefix="add_email", use_required_attribute=False),
            "additional_emails": AdditionalEmail.objects.filter(user=user),
        },
    )


@login_required
@permission_required("auth.add_user", raise_exception=True)
@require_POST
def member_activate(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.is_active = True
    user.save(update_fields=["is_active"])
    return JsonResponse({"data": True})


@login_required
@permission_required("auth.add_user", raise_exception=True)
@require_POST
def member_detail_update(request, pk):
    user = get_object_or_404(User.objects.select_related("profile"), pk=pk)
    user_form = MemberForm(request.POST, instance=user)
    profile_form = ProfileForm(request.POST, instance=user.profile)
    email_form = AdditionalEmailForm(request.POST, prefix="add_email")
    forms = [user_form, profile_form]
    if email_form.has_input():
        forms.append(email_form)

    if not all([form.is_valid() for form in forms]):  # list: validate every form
        errors = {}
        for form in forms:
            for name, messages_ in form.errors.items():
                label = form.fields[name].label if name in form.fields else name
                errors[form.add_prefix(name)] = {"label": str(label), "messages": messages_}
        return JsonResponse({"data": False, "errors": errors}, status=400)

    with transaction.atomic():
        user_form.save()
        profile_form.save()
        if email_form in forms:
            additional_email = email_form.save(commit=False)
            additional_email.user = user
            additional_email.save()
    return JsonResponse({"data": True})
