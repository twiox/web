"""The member's own profile page (/mitglieder/profil/): personal data, login e-mail, username,
password, further e-mail addresses, a message to the board, and cancelling the membership."""
import html as html_lib
import re
from datetime import date, datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import PasswordChangeView as DjangoPasswordChangeView
from django.core.mail import EmailMessage, EmailMultiAlternatives, get_connection
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import path, reverse, reverse_lazy
from django.utils.html import strip_tags
from django.views.decorators.http import require_POST
from django.views.generic import FormView, UpdateView

from members.models import AdditionalEmail, Profile

from .forms import (
    AdditionalEmailForm,
    MemberPasswordChangeForm,
    ProfileSelfForm,
    UpdateMemberEmailForm,
    UpdateMemberInformationForm,
    UsernameForm,
)
from .membership import cancellation_dates


class UserDetailView(LoginRequiredMixin, UpdateView):
    # TODO: get email for every change in "Hinweis"
    model = User
    template_name = "user_handling/profile/detail.html"
    form_class = UpdateMemberInformationForm

    def get_object(self, queryset=None):
        obj = self.request.user
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["additional_emails"] = AdditionalEmail.objects.filter(user=self.object)
        # when a cancellation today would end the membership (see membership.py)
        context["cancel_end"], context["cancel_deadline"] = cancellation_dates()
        return super().get_context_data(**context)

    def post(self, request, *args, **kwargs):
        self.object = request.user
        form = self.form_class(request.POST, request.FILES)
        if not form.is_valid():
            for errors in form.errors.values():
                for error in errors:
                    messages.add_message(request, messages.ERROR, error)
            return HttpResponseRedirect(reverse("profile_detail"))
        email = EmailMessage(
            f"Mitteilung von {request.user.first_name} {request.user.last_name}",
            form.cleaned_data["comment"],
            to=[settings.TO_EMAIL],
            cc=[request.user.email],
        )
        # attached straight from the upload: nothing is stored on the server (media/ is public)
        attachment = form.cleaned_data.get("attachment")
        if attachment:
            email.attach(attachment.name, attachment.read(), attachment.content_type)
        email.send()
        messages.add_message(request, messages.SUCCESS, "Nachricht erfolgreich versendet")
        return HttpResponseRedirect(reverse("profile_detail"))


def html_email(subject, template, context, to, reply_to=None):
    """An HTML e-mail with a plain-text version for mail apps without HTML."""
    html = render_to_string(template, context)
    text = re.sub(r"<br\s*/?>\s*", "\n", html)
    text = re.sub(r"<hr\s*/?>", "\n\n___\n\n", text)
    text = re.sub(r"</(p|li|ul|h\d)>", "\n\n", text)
    text = re.sub(r"[ \t]+\n", "\n", html_lib.unescape(strip_tags(text)))
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    message = EmailMultiAlternatives(subject, text, settings.DEFAULT_FROM_EMAIL, to, reply_to=reply_to)
    message.attach_alternative(html, "text/html")
    return message


@login_required
@require_POST
def profile_cancel(request):
    """The member cancels the own membership (profile page, after a confirmation): status "Kündigung",
    end date by the rule in membership.py, a confirmation to the member and a note to the board."""
    profile = request.user.profile
    if profile.status == "Kündigung" or profile.membership_end:
        messages.add_message(request, messages.INFO, "Deine Mitgliedschaft ist bereits gekündigt.")
        return HttpResponseRedirect(reverse("profile_detail"))
    end, _ = cancellation_dates()
    previous_status = profile.status
    profile.status = "Kündigung"
    profile.membership_end = datetime.combine(end, datetime.min.time())
    profile.save(update_fields=["status", "membership_end"])
    context = {"user": request.user, "profile": profile, "end": end, "today": date.today(), "previous_status": previous_status}
    name = request.user.get_full_name()
    mails = [html_email(f"Twio X e.V. | Kündigung zum {end:%d.%m.%Y}", "user_handling/emails/cancellation_board.html", context, [settings.TO_EMAIL],
                        reply_to=[request.user.email] if request.user.email else None)]
    if request.user.email:
        mails.insert(0, html_email(f"Twio X e.V. | Deine Kündigung zum {end:%d.%m.%Y}", "user_handling/emails/cancellation_member.html",
                                   context, [request.user.email], reply_to=[settings.TO_EMAIL]))
    try:
        get_connection().send_messages(mails)
        sent = True
    except Exception:
        sent = False
    text = f"Deine Mitgliedschaft ist zum {end:%d.%m.%Y} gekündigt."
    text += " Du bekommst eine Bestätigung per E-Mail." if sent and request.user.email else " Die Bestätigung per E-Mail konnte nicht gesendet werden, der Vorstand ist aber informiert." if not sent else ""
    messages.add_message(request, messages.SUCCESS, text)
    return HttpResponseRedirect(reverse("profile_detail"))


class EmailUpdateView(LoginRequiredMixin, FormView):
    template_name = "user_handling/profile/form.html"
    form_class = UpdateMemberEmailForm
    extra_context = {"title": "E-Mail-Adresse ändern"}

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), "user": self.request.user}

    def get_context_data(self, **kwargs):
        hint = f"Aktuell: {self.request.user.email or 'keine'}. Mit der neuen Adresse meldest du dich auch an."
        return super().get_context_data(hint=hint, **kwargs)

    def form_valid(self, form):
        self.request.user.email = form.cleaned_data["email1"]
        self.request.user.save(update_fields=["email"])
        messages.add_message(self.request, messages.SUCCESS, "E-Mail erfolgreich geändert")
        return HttpResponseRedirect(reverse("profile_detail"))


class PasswordChangeView(LoginRequiredMixin, DjangoPasswordChangeView):
    """Django's view: saves the password and keeps the member logged in."""

    template_name = "user_handling/profile/form.html"
    form_class = MemberPasswordChangeForm
    success_url = reverse_lazy("profile_detail")
    extra_context = {"title": "Passwort ändern", "hint": "Mindestens 8 Zeichen, nicht nur Ziffern und nicht zu ähnlich zu deinem Namen."}

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, "Passwort erfolgreich geändert")
        return super().form_valid(form)


class UsernameUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "user_handling/profile/form.html"
    form_class = UsernameForm
    extra_context = {"title": "Nutzername ändern", "hint": "Du kannst dich mit dem Nutzernamen oder deiner E-Mail-Adresse anmelden."}

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Nutzername erfolgreich geändert")
        return reverse("profile_detail")


class AddressChangeView(LoginRequiredMixin, UpdateView):
    model = Profile
    template_name = "user_handling/profile/address.html"
    form_class = ProfileSelfForm

    def get_object(self, queryset=None):
        obj = self.request.user.profile
        return obj

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Daten erfolgreich geändert")
        return reverse("profile_detail")


@login_required
@require_POST
def add_another_email(request):
    """A further address on the own profile (e.g. a parent's), for the info mails."""
    form = AdditionalEmailForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"errors": " ".join(e for errors in form.errors.values() for e in errors)}, status=400)
    form.instance.user = request.user
    form.save()
    return JsonResponse({"pk": form.instance.pk})


@login_required
@require_POST
def delete_additional_email(request):
    """Only the own addresses; anything else is not found."""
    try:
        pk = int(request.POST.get("id", ""))
    except ValueError:
        return JsonResponse({"errors": "Keine Adresse angegeben."}, status=400)
    get_object_or_404(AdditionalEmail, user=request.user, pk=pk).delete()
    return JsonResponse({"deleted": pk})


# included at "mitglieder/profil/" (twio_web/urls.py)
urlpatterns = [
    path("", UserDetailView.as_view(), name="profile_detail"),
    path("ändere_email/", EmailUpdateView.as_view(), name="profile_update_email"),
    path("ändere_nutzername/", UsernameUpdateView.as_view(), name="profile_update_username"),
    path("ändere_daten/", AddressChangeView.as_view(), name="profile_update_address"),
    path("ändere_passwort/", PasswordChangeView.as_view(), name="profile_update_pw"),
    path("kündigen/", profile_cancel, name="profile_cancel"),
    path("weitere_email/neu/", add_another_email, name="add_another_email"),
    path("weitere_email/löschen/", delete_additional_email, name="delete_additional_email"),
]
