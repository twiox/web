from .forms import *
from django.shortcuts import render, redirect
from members.models import Trainer, Profile, Event, Message, Session, Group
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import DeleteView, UpdateView, CreateView, ListView
from django.urls import reverse
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.auth.models import Group as Permission_group


def trainer_index(request):
    """ I just assume for the moment, that the user is a trainer """
    trainer_sessions = Session.objects.filter(trainer=Trainer.objects.get(user=request.user))
    trainer_groups = Group.objects.filter(session__trainer=Trainer.objects.get(user=request.user)).distinct()
    
    return render(
        request,"trainer/trainer_index.html",
        {"trainer_sessions":trainer_sessions,
         "trainer_groups":trainer_groups,
         }
            )
 

def abrechnungstable(request):
    return render(request, "trainer/abrechnung_form.html", context={})

class TrainerListView(LoginRequiredMixin, ListView):
    model = Trainer
    template_name = "trainer/trainer_list.html"

@login_required
@permission_required('members.add_trainer', raise_exception=True)
def register_trainer(request):
    if(request.method == "POST"): #if the form is filled out
        form = TrainerCreationForm(request.POST,request.FILES) 
        if(form.is_valid()):
            new_trainer = form.save() #save the trainer
            user = new_trainer.user
            group_t,_ = Group.objects.get_or_create(group_id="T")
            user.profile.group = group_t
            try:
                trainer_group = Permission_group.objects.get(name='Trainer') 
            except:
                trainer_group = Permission_group(name="Trainer")
                trainer_group.save()
                for perm in trainer_permissions():
                    trainer_group.permissions.add(perm)
            finally:
                trainer_group.user_set.add(user)
                trainer_group.save()
                user.save()
                new_trainer.save()
                messages.add_message(request, messages.SUCCESS, "Trainer angelegt. Gruppe wurde auf 'T' gesetzt")
                return redirect("register_trainer")
        else:
            return render(request, 'trainer/trainer_form.html', context={'form': form})
    else:
        form = TrainerCreationForm()
    return render(request, 'trainer/trainer_form.html', context={"form":form})

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
            messages.add_message(request, messages.SUCCESS, f"Trainerstatus für {user.first_name} entfernt. Gruppe wurde auf {group.group_id} gesetzt")
            return redirect("remove_trainer")
        return render(request, "trainer/remove_trainer.html", context={"form":form})
    else:
        form = TrainerDeletionForm() 
        return render(request, "trainer/remove_trainer.html", context={"form":form})



class TrainerUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    #template: event_form.html
    model = Trainer
    fields = [
        "trainer_telnr",
        "trainer_email",
        "license_number",
        "license_valid",
        "license_level",
        "contract",
        "license",
        "codex",
        "salary",
        "image"
        ]
    template_name="trainer/trainer_form.html"
    permission_required = 'members.change_trainer'
