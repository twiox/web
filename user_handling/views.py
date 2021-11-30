from .forms import *
from .tokens import account_activation_token
from .permissions import trainer_permissions, chairman_permissions
from members.models import Group, Chairman, Profile
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.forms import UserCreationForm,PasswordChangeForm
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.auth.models import User, Permission
from django.contrib.auth.models import Group as Permission_group
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin,PermissionRequiredMixin, UserPassesTestMixin
from django.views.generic import DeleteView, UpdateView, CreateView, ListView
from django.contrib.auth.views import LoginView, PasswordResetView, LogoutView, PasswordResetConfirmView
from django.urls import reverse

@permission_required('auth.add_user', raise_exception=True)
def index(request):
     return render(request, 'user_handling/index.html')


#register user
@login_required
@permission_required('auth.add_user', raise_exception=True)
def register(request):
    if request.method == "POST": #if the form is filled out
        form = MemberCreationForm(request.POST) 
        form2 = ProfileCreationForm(request.POST)
        if(form.is_valid() and form2.is_valid()): #and the form is valid
            real_user = form.save(commit=False) #save the user to fire the signal
            real_user.username=form.cleaned_data.get("first_name").lower()+form2.cleaned_data.get('member_num')
            password = User.objects.make_random_password()
            real_user.set_password(password)
            real_user.is_active=False
            real_user.save()
            real_user.refresh_from_db() #get the user again
            for key, value in form2.cleaned_data.items():
                setattr(real_user.profile, key, value)
            real_user.save() #save the entries
            current_site = get_current_site(request)
            password_reset_token = PasswordResetTokenGenerator()
            
            mail_subject="Aktiviere deinen Account für den Twio Mitgliederbereich"
            message= render_to_string("user_handling/acc_active_email.html",{
                "user":real_user,
                "domain":current_site.domain,
                "uid": urlsafe_base64_encode(force_bytes(real_user.pk)),
                "token":account_activation_token.make_token(real_user),
                }       
            )
            to_email = form.cleaned_data.get("email")
            email=EmailMessage(mail_subject, message, to=[to_email])
            email.send()
            messages.add_message(request, messages.SUCCESS, 'Account angelegt. Das Mitglied bekommt eine Email')
            return redirect("register")
    else:
        current_member = sorted([x.member_num for x in Profile.objects.all()])[-1]
        form = MemberCreationForm()
        form2 = ProfileCreationForm()
    return render(request, 'user_handling/register.html', context={"form":form, "form2":form2,"current_member":current_member})

def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token) and user.is_active==False:
        user.is_active = True
        user.save()
        
        password_reset_token = PasswordResetTokenGenerator()
        uid2 = urlsafe_base64_encode(force_bytes(user.pk))
        token2 = password_reset_token.make_token(user)
        
        # return redirect('home')
        return render(request, "user_handling/activate.html", context={"user":user, "uid":uid2, "token":token2})
    else:
        return render(request, "user_handling/activate_fail.html", context={"uidb64":uidb64, "token":token}  )   

def resend_activate(request, uidb64, token):
    uid = force_text(urlsafe_base64_decode(uidb64))
    try:
        real_user = User.objects.get(pk=uid)
        to_email = real_user.email
    
        password_reset_token = PasswordResetTokenGenerator()
        mail_subject="Aktiviere deinen Account für den Twio Mitgliederbereich"
        message= render_to_string("user_handling/acc_active_email.html",{
            "user":real_user,
            "domain":get_current_site(request).domain,
            "uid": urlsafe_base64_encode(force_bytes(real_user.pk)),
            "token":account_activation_token.make_token(real_user),
            }       
        )
        
        email=EmailMessage(mail_subject, message, to=[to_email])
        email.send()
        messages.add_message(request, messages.SUCCESS, 'Neuer Aktivierungslink verschickt')
    except:
        messages.add_message(request, messages.SUCCESS, 'FEHLER: Der Benutzer existiert nicht. Bitte wende dich an den Vorstand')
    return redirect("activate", uidb64=uidb64, token=token)

class MemberListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = User
    permission_required = 'auth.add_user'
    template_name = "user_handling/member_list.html"
    
    def get_queryset(self):
        return User.objects.order_by('profile__membership_start')
    
class UserDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = User
    template_name = "user_handling/user_confirm_delete.html"
    #who can delete the user?
    permission_required = 'auth.delete_user'
    
    def get_success_url(self, **kwargs):
        return reverse("member_list")

@login_required
@permission_required('auth.add_user', raise_exception=True)
def member_update(request, pk):
    real_user = get_object_or_404(User,pk=pk)
    
    if request.method == "POST": #if the form is filled out
    
        form = MemberListUserUpdateForm(request.POST) 
        form2 = MemberListProfileUpdateForm(request.POST)
        
        if(form.is_valid() and form2.is_valid()): #and the form is valid
            
            for key, value in form.cleaned_data.items():
                setattr(real_user, key, value)
                
            for key, value in form2.cleaned_data.items():
                setattr(real_user.profile, key, value)
                
            real_user.save() #save the entries
            messages.add_message(request, messages.SUCCESS, 'Account erfolgreich bearbeitet')
            return redirect("member_list")
    else:
        form = MemberListUserUpdateForm(instance=real_user)
        form2 = MemberListProfileUpdateForm(instance=real_user.profile)
    return render(request, 'user_handling/register.html', context={"form":form, "form2":form2})

class ChairmanCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    #template: event_detail.html
    model = Chairman
    fields=["user","public_telnr","public_email","competences","image","show"]
    template_name="user_handling/chairman_form.html"
    permission_required = 'members.add_chairman'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["choices"] = [(x.pk, f"{x.first_name} {x.last_name} ({x.profile.member_num})") for x in User.objects.filter(chairman__id__isnull=True)]
        return context
    
    
    def form_valid(self, form):
        self.object = form.save()
        user = self.object.user
        try:
            chairman_group = Permission_group.objects.get(name='Vorstand') 
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
    permission_required = 'members.delete_chairman'
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        user=self.object.user
        success_url = self.get_success_url()
        try:
            chairman_group = Permission_group.objects.get(name='Vorstand')
            chairman_group.user_set.remove(user)
            chairman_group.save()
        except: #if we created chairman via the webiste...
            pass 
        self.object.delete()
        return HttpResponseRedirect(success_url)
    
    def get_success_url(self, **kwargs):
        return reverse("chairman_list")

class ChairmanUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    #template: event_form.html
    model = Chairman
    fields=["public_telnr","public_email","competences","image","show"]
    template_name="user_handling/chairman_form.html"
    permission_required = 'members.change_chairman'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["checked_shows"] = [x for x in self.get_object().show]
        return context

    
class ChairmanListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Chairman
    permission_required = 'members.change_chairman'
    template_name = "user_handling/chairman_list.html"

class PasswordResetView(PasswordResetView):
    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        messages.add_message(self.request, messages.SUCCESS, 'Email verschickt. Bitte schau in deinen Posteingang')
        return reverse("login") 

class LogoutView(LogoutView):
    def get_next_page(self):
        next_page = super(LogoutView, self).get_next_page()
        messages.add_message(self.request, messages.SUCCESS, 'Erfolgreich ausgeloggt')
        return next_page
        
class PasswordResetConfirmView(PasswordResetConfirmView):
    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        messages.add_message(self.request, messages.SUCCESS, 'Passwort erstellt. Du kannst dich nun einloggen')
        return reverse("index")
