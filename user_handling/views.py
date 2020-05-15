from .forms import *
from .tokens import account_activation_token
from members.models import Group
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.forms import UserCreationForm,PasswordChangeForm
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.auth.models import User
from django.contrib.auth.models import Group as Permission_group
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin,PermissionRequiredMixin, UserPassesTestMixin
from django.views.generic import DeleteView, UpdateView
from django.contrib.auth.views import LoginView

class LoginView(LoginView):
    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, 'Fehler. Bitte prüfe deine Einloggdaten')
        return self.render_to_response(self.get_context_data(form=form))

#register user
@login_required
@permission_required('auth.add_user', raise_exception=True)
def register(request):
    if(request.method == "POST"): #if the form is filled out
        form = MemberCreationForm(request.POST) 
        form2 = ProfileCreationForm(request.POST)
        
        if(form.is_valid() and form2.is_valid()): #and the form is valid (= submitted and passwords match etc.)
            real_user = form.save(commit=False) #save the user to fire the signal
            real_user.username=form.cleaned_data.get("first_name").lower()+form2.cleaned_data.get('member_num')
            password = User.objects.make_random_password()
            real_user.set_password(password)
            real_user.is_active=False
            real_user.save()
            real_user.refresh_from_db() #get the user again
            real_user.profile.group = form2.cleaned_data.get('group') #add the user's group
            real_user.profile.member_num = form2.cleaned_data.get('member_num') #add the user's number
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
        form = MemberCreationForm()
        form2 = ProfileCreationForm()
    return render(request, 'user_handling/register.html', context={"form":form, "form2":form2})

def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        
        password_reset_token = PasswordResetTokenGenerator()
        uid2 = urlsafe_base64_encode(force_bytes(user.pk))
        token2 = password_reset_token.make_token(user)
        
        # return redirect('home')
        return render(request, "user_handling/activate.html", context={"user":user, "uid":uid2, "token":token2})
    else:
        return render(request, "user_handling/activate_fail.html" )   

class UserDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = User
    template_name = "user_handling/user_confirm_delete.html"
    success_url = "/remove/"
    #who can delete the user?
    permission_required = 'auth.delete_user'


@login_required
@permission_required('auth.delete_user', raise_exception=True)
def remove_user(request):
    if(request.method == "POST"): #if the form is filled out
        form = MemberDeletionForm(request.POST) 
        if(form.is_valid()):
            user = form.cleaned_data.get('member') #save the user
            return HttpResponseRedirect(f"/remove/user/{user.id}/")
        return render(request, "user_handling/remove_member.html", context={"form":form})
    else:
        form = MemberDeletionForm() 
        return render(request, "user_handling/remove_member.html", context={"form":form})
        
        
@login_required
@permission_required('members.add_trainer', raise_exception=True)
def register_trainer(request):
    if(request.method == "POST"): #if the form is filled out
        form = TrainerCreationForm(request.POST) 
        if(form.is_valid()): #and the form is valid (= submitted and passwords match etc.)
            new_trainer = form.save() #save the trainer
            user = new_trainer.user
            user.profile.group = Group.objects.get(group_id="T")
            trainer_group = Permission_group.objects.get(name='Trainer') 
            trainer_group.user_set.add(user)
            trainer_group.save()
            user.save()
            messages.add_message(request, messages.SUCCESS, "Trainer angelegt. Gruppe wurde auf 'T' gesetzt")
            return redirect("register_trainer")
    else:
        form = TrainerCreationForm()
    return render(request, 'user_handling/register_trainer.html', context={"form":form})

@login_required
@permission_required('members.delete_trainer', raise_exception=True)
def remove_trainer(request):
    if(request.method == "POST"): #if the form is filled out
        form = TrainerDeletionForm(request.POST) 
        if(form.is_valid()):
            trainer = form.cleaned_data.get('trainer') #save the trainer
            user = trainer.user
            trainer.delete()
            group = form.cleaned_data.get('group')
            user.profile.group = group
            trainer_group = Permission_group.objects.get(name='Trainer') 
            trainer_group.user_set.remove(user)
            trainer_group.save()
            user.save()
            messages.add_message(request, messages.SUCCESS, f"Trainerstatus für {user.first_name} entfernt. Gruppe wurde auf {group} gesetzt")
            return redirect("remove_trainer")
        return render(request, "user_handling/remove_trainer.html", context={"form":form})
    else:
        form = TrainerDeletionForm() 
        return render(request, "user_handling/remove_trainer.html", context={"form":form})

@login_required
@permission_required('members.delete_trainer', raise_exception=True)
def change_group(request):
    if(request.method == "POST"): #if the form is filled out
        form = GroupChangeForm(request.POST) 
        if(form.is_valid()):
            user = form.cleaned_data.get('user') #save the user
            group = form.cleaned_data.get('group')
            user.profile.group = group
            user.save()
            messages.add_message(request, messages.SUCCESS, f"Gruppe für {user.first_name} auf Gruppe {group.group_id} geändert")
            return redirect("change_group")
        return render(request, "user_handling/change_group.html", context={"form":form})
    else:
        form = GroupChangeForm() 
        return render(request, "user_handling/change_group.html", context={"form":form})
        