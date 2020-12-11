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
from django.contrib.auth.decorators import user_passes_test

def trainer_check(user):
    return hasattr(user, "trainer")


@user_passes_test(trainer_check)
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
 
@user_passes_test(trainer_check)
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
    soup = BeautifulSoup(html, features="html.parser")
    trainer = soup.find(id="js_trainerdata")
    header = soup.find(id="bs4_header")
    entries = soup.find_all("tr", {"class":"bs4_body"})
    summary = soup.find(id="js_summary")
    data = {
        "Datum":f"{datetime.today().strftime('%d.%m.%Y')}",
        "Trainer":trainer.text.strip(),
        "Einheiten": "\n".join([
            header.text.strip().replace("\n","\t").replace("Aktion",""),
            "\n".join([
                x.text.strip().replace("\n","\t") for x in entries]),
            ]),
        "Abrechnung":summary.text.strip().replace("\n","\t")
    }
    
    mail_subject=f"{datetime.today().strftime('%d.%m.%Y')}_Abrechnung_{request.user.first_name}_{request.user.last_name}"
    message= f"Trainerabrechnung von {request.user.first_name} {request.user.last_name}"
    to_email = settings.TO_EMAIL
    with open(f"media/trainer_tables/{datetime.today().strftime('%d.%m.%Y')}_Abrechnung_{request.user.first_name}.txt", "w") as outfile:
        print("\n--------\n".join(data.values()), file=outfile)
    email=EmailMessage(mail_subject, message, to=[to_email], cc=[request.user.trainer.trainer_email])
    email.attach_file(f"media/trainer_tables/{datetime.today().strftime('%d.%m.%Y')}_Abrechnung_{request.user.first_name}.txt")
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
                messages.add_message(request, messages.SUCCESS, "Trainer angelegt. Gruppe wurde auf T gesetzt")
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
