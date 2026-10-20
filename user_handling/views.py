from .forms import MemberForm, ProfileForm, AdditionalEmailForm
from members.models import (
    is_trainer,
    is_chairman,
    Chairman,
    Trainer,
    Profile,
    AdditionalEmail,
    Event,
)
from interested.models import PublicEvent, EventParticipant
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseRedirect, JsonResponse
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
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import DeleteView, UpdateView, ListView
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


@login_required
@permission_required("auth.add_user", raise_exception=True)
def index(request):
    return render(request, "user_handling/index.html")


def member_number(user):
    """Numeric member number for sorting, 0 if missing or not a number."""
    try:
        return int(user.profile.member_num)
    except (ValueError, Profile.DoesNotExist):
        return 0


def new_member_initial():
    """Suggests the next member number and Mandatsreferenz (<number>-<yy>-<counter>)."""
    numbers = [int(n) for n in Profile.objects.values_list("member_num", flat=True) if n.isdigit()]
    member_num = max(numbers, default=0) + 1
    last_ref = (
        Profile.objects.exclude(mandatsref__isnull=True).exclude(mandatsref="")
        .order_by("pk").values_list("mandatsref", flat=True).last()
    )
    try:
        counter = int(last_ref.split("-", 2)[2]) + 1
    except (AttributeError, IndexError, ValueError):
        counter = "NA"
    year = str(datetime.date.today().year)[-2:]
    return {"member_num": member_num, "mandatsref": f"{member_num}-{year}-{counter}"}


@login_required
@permission_required("auth.add_user", raise_exception=True)
def register(request):
    if request.method == "POST":
        user_form = MemberForm(request.POST)
        profile_form = ProfileForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            real_user = user_form.save(commit=False)
            real_user.username = (
                user_form.cleaned_data["first_name"].lower()
                + profile_form.cleaned_data["member_num"]
            )
            alphabet = string.ascii_letters + string.digits
            password = "".join(secrets.choice(alphabet) for _ in range(8))
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
        profile_form = ProfileForm(initial=new_member_initial())
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
    permission_required = "auth.add_user"
    template_name = "user_handling/member_list.html"

    def get_queryset(self):
        users = sorted(User.objects.select_related("profile"), key=member_number)
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
    permission_required = "auth.delete_user"

    def get_success_url(self):
        return reverse("member_list")


class ChairmanDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Chairman
    template_name = "user_handling/chairman_confirm_delete.html"
    permission_required = "members.delete_chairman"

    def form_valid(self, form):
        # deactivate instead of delete, see member_role
        self.object.active = False
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("chairman_list")


class ChairmanUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Chairman
    fields = ["public_telnr", "public_email", "competences", "image", "show"]
    template_name = "user_handling/chairman_form.html"
    permission_required = "members.change_chairman"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["checked_shows"] = list(self.object.show)
        return context


class ChairmanListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    queryset = Chairman.objects.filter(active=True).select_related("user").order_by("user__last_name")
    permission_required = "members.change_chairman"
    template_name = "user_handling/chairman_list.html"


class TwioPasswordResetView(PasswordResetView):
    def get_success_url(self):
        messages.add_message(
            self.request, messages.SUCCESS, "Email verschickt. Bitte schau in deinen Posteingang"
        )
        return reverse("login")


class TwioLogoutView(LogoutView):
    def get_success_url(self):
        # after logout, so the message lands in the new session
        messages.add_message(self.request, messages.SUCCESS, "Erfolgreich ausgeloggt")
        return super().get_success_url()


class TwioPasswordResetConfirmView(PasswordResetConfirmView):
    def get_success_url(self):
        messages.add_message(
            self.request, messages.SUCCESS, "Passwort erstellt. Du kannst dich nun einloggen"
        )
        return reverse("index")


def trainer_or_chairman(user):
    return is_trainer(user) or is_chairman(user)


@user_passes_test(trainer_or_chairman)
def mailing_lists(request):
    return render(request, "user_handling/mailing-lists.html")


def emails_of(users):
    """The users' addresses plus their additional addresses."""
    emails = set(users.values_list("email", flat=True))
    emails |= set(AdditionalEmail.objects.filter(user__in=users).values_list("email", flat=True))
    return emails


def email_list_response(emails):
    return JsonResponse({"string": ",".join(sorted(e for e in emails if e))})


@user_passes_test(trainer_or_chairman)
def get_participants_emails(request):
    if request.GET.get("type"):
        event = get_object_or_404(PublicEvent, pk=request.GET.get("id"))
        return email_list_response(EventParticipant.objects.filter(event=event).values_list("email", flat=True))
    event = get_object_or_404(Event, pk=request.GET.get("id"))
    return email_list_response(emails_of(User.objects.filter(memberparticipant__event=event)))


@user_passes_test(trainer_or_chairman)
def get_all_emails(request):
    """id is "alle" or "email_<status>"."""
    list_id = request.GET.get("id", "")
    if list_id == "alle":
        users = User.objects.all()
        trainer_emails = set(Trainer.objects.filter(active=True).values_list("trainer_email", flat=True))
    elif list_id.startswith("email_"):
        users = User.objects.filter(profile__status=list_id.removeprefix("email_"))
        trainer_emails = set()
    else:
        raise Http404
    return email_list_response(emails_of(users) | trainer_emails)


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
            "chairman": Chairman.objects.filter(user=user, active=True).first(),
            "trainer": Trainer.objects.filter(user=user, active=True).first(),
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


ROLE_MODELS = {"chairman": Chairman, "trainer": Trainer}


@login_required
@require_POST
def member_role(request, pk, role):
    """Switches the chairman or trainer role on or off, the signals handle the permissions."""
    model = ROLE_MODELS.get(role)
    if model is None:
        raise Http404
    active = request.POST.get("active") == "1"
    action = "add" if active else "delete"
    if not request.user.has_perm(f"members.{action}_{role}"):
        raise PermissionDenied
    user = get_object_or_404(User, pk=pk)
    # never deleted, so switching a role back on restores its profile and history
    entry = model.objects.filter(user=user).first() or model(user=user)
    entry.active = active
    entry.save()
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
