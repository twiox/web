from bs4 import BeautifulSoup
from .forms import *
from .models import Trainer_table, Table_entry
from django.shortcuts import render, redirect
from members.models import Trainer, Profile, Event, Message, Session, Group
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import DeleteView, UpdateView, CreateView, ListView
from django.urls import reverse
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.auth.models import Group as Permission_group
from django.http import JsonResponse
from datetime import datetime
from django.core.mail import EmailMessage
from django.conf import settings


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
    table, _ = Trainer_table.objects.get_or_create(trainer=request.user.trainer)
    sessions = Session.objects.filter(trainer=request.user.trainer)
    if(request.GET.get('reset', '')=="true"):
        Table_entry.objects.filter(table=table).all().delete()
        for sess in sessions.all():
            try:
                temp, created = Table_entry.objects.get_or_create(table=table, session=sess)
            except Table_entry.MultipleObjectsReturned:
                pass

    entries = Table_entry.objects.filter(table=table).all()
    return render(request, "trainer/abrechnung_form.html", context={"table":table, "entries":entries})

### JQUERY AJAX STUFF ###

def reset_table(request):
    table = Trainer_table.objects.get(trainer=request.user.trainer)
    sessions = Session.objects.filter(trainer=request.user.trainer)
    Table_entry.objects.filter(table=table).all().delete()
    for sess in sessions.all():
        try:
            temp, created = Table_entry.objects.get_or_create(table=table, session=sess)
        except Table_entry.MultipleObjectsReturned:
            pass
    entries = Table_entry.objects.filter(table=table).all()
    data = {}
    for obj in entries:
        data[obj.pk] = {
            "day":obj.session.day,
            "start_time":obj.session.start_time.strftime("%H:%M"),
            "end_time":obj.session.end_time.strftime("%H:%M"),
            "group":obj.session.group.group_id,
        }
    return JsonResponse(data)
    
    
def add_week(request):
    table = Trainer_table.objects.get(trainer=request.user.trainer)
    sessions = Session.objects.filter(trainer=request.user.trainer)

    entries = []
    data = {}
    for sess in sessions.all():
        temp = Table_entry.objects.create(table=table, session=sess)
        entries.append(temp)

    for obj in entries:
        data[obj.pk] = {
            "day":obj.session.day,
            "start_time":obj.session.start_time.strftime("%H:%M"),
            "end_time":obj.session.end_time.strftime("%H:%M"),
            "group":obj.session.group.group_id,
        }
    return JsonResponse(data)

def delete_row(request):
    _,_,pk = request.GET.get('id', None).split("_")
    Table_entry.objects.filter(id=pk).delete()
    row_id = f"js_row_{pk}"
    data = {'row':row_id}
    return JsonResponse(data)

def send_table(request):
    html = request.GET.get('html', None)
    soup = BeautifulSoup(html)
    trainer = soup.find(id="js_trainerdata")
    entries = soup.find(id="abrechenform")
    summary = soup.find(id="js_summary")
    data = {
        "trainer":trainer.text.strip().replace("\n",","),
        "entries":entries.text.strip().replace("\n\n\n\n",";").replace("\n",",").replace(";","\n"),
        "summary":summary.text.strip().replace("\n",",")
    }
    
    mail_subject="Trainerabrechnungstabelle"
    message= "\n\n".join(data.values())
    to_email = settings.TO_EMAIL
    email=EmailMessage(mail_subject, message, to=[to_email])
    email.send()
    messages.add_message(request, messages.SUCCESS, 'Abrechnungstabelle verschickt')
    
    return JsonResponse(data)

#### More views ####

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
