from .forms import *
from .models import Trainer_table, Table_entry, TrainingSessionEntry
from django.core.files import File
from django.core.files.base import ContentFile
from django.shortcuts import render, redirect
from members.models import Trainer, Profile, Event, Message, Session, Group, AdditionalEmail
from django.contrib import messages
from user_handling.permissions import trainer_permissions
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.views.generic import DeleteView, UpdateView, CreateView, ListView, DetailView
from django.urls import reverse
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.auth.models import Group as Permission_group
from django.http import JsonResponse
from datetime import datetime
from django.core.mail import EmailMessage
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
import json
import codecs
import django
from django.db.models import Q


def trainer_check(user):
    return hasattr(user, "trainer")

@user_passes_test(trainer_check)
def trainer_index(request):
    """ I just assume for the moment, that the user is a trainer """
    user = request.user
    trainer_sessions = TrainingSessionEntry.objects.filter(
        Q(trainer=user.trainer) |
        Q(cotrainer=user.trainer)
    ).order_by('-date')

    return render(
        request,"trainer/trainer_index.html",
        {"trainer_sessions":trainer_sessions,
         }
    )

@user_passes_test(trainer_check)
def abrechnungstable(request):
    table, created = Trainer_table.objects.get_or_create(trainer=request.user.trainer, active=True)
    sessions = Session.objects.filter(trainer=request.user.trainer)
    if created:
        for sess in sessions.all():
            Table_entry.objects.create(table=table, day=sess.day, group=sess.agegroup, start=sess.start_time.strftime("%H:%M"), end=sess.end_time.strftime("%H:%M"))

    entries = Table_entry.objects.filter(table=table).all()
    tables = Trainer_table.objects.filter(trainer=request.user.trainer, active=False).order_by('-id')[:10]
    return render(request, "trainer/abrechnung_form.html", context={"tables":tables, "entries":entries})

@user_passes_test(trainer_check)
def trainer_data(request):
    """ I just assume for the moment, that the user is a trainer """
    return render(
        request,"trainer/trainer_data.html",
    )

### JQUERY AJAX STUFF ###
def is_privileged(user):
    return user.profile.privileged

@user_passes_test(is_privileged)
def get_session_emails(request, sessionid):
    """
    Get the emails of all members in the agegroup of a session
    """
    session = Session.objects.get(pk=sessionid)
    if agegroup := session.agegroup:
        emails = []
        for profile in agegroup.get_profiles():
            #only use ordentliche mitglieder
            if profile.status != 'Ordentliches Mitglied':
                continue
            emails.append(profile.user.email)
            query = AdditionalEmail.objects.filter(user=profile.user)
            emails.extend([x.email for x in query])
        for trainer in session.trainer.all():
            emails.append(trainer.trainer_email)
        emails = set(emails)
        return JsonResponse({'emailstring':','.join(emails)})
    return JsonResponse({'emailstring':''})


def reset_table(request):
    table = Trainer_table.objects.get(trainer=request.user.trainer, active=True)
    sessions = Session.objects.filter(trainer=request.user.trainer)
    Table_entry.objects.filter(table=table).all().delete()

    for sess in sessions.all():
        Table_entry.objects.create(table=table, day=sess.day, group=sess.agegroup, start=sess.start_time.strftime("%H:%M"), end=sess.end_time.strftime("%H:%M"))

    entries = Table_entry.objects.filter(table=table).all()
    data = {}
    for obj in entries:
        data[obj.pk] = {
            "day":obj.day,
            "start_time":obj.start,
            "end_time":obj.end,
            "group":obj.group,
            "notes":obj.notes
        }
    return JsonResponse(data)

def save_entries(request):
    table = Trainer_table.objects.get(trainer=request.user.trainer, active=True)
    data = request.POST

    for entry in zip(*[tuple(x[1]) for x in data.lists()][1:]):
        tab = Table_entry.objects.get(pk=entry[0])
        tab.date = entry[1]
        tab.day = entry[2]
        tab.group = entry[3]
        tab.start = entry[4]
        tab.end = entry[5]
        tab.dur = entry[6]
        tab.notes = entry[7]
        try:
            tab.save()
        except django.core.exceptions.ValidationError:
            return JsonResponse({"data":False})
    return JsonResponse({"data":True})

def add_week(request):
    table = Trainer_table.objects.get(trainer=request.user.trainer, active=True)
    sessions = Session.objects.filter(trainer=request.user.trainer)

    entries = []
    data = {}
    for sess in sessions.all():
        temp = Table_entry.objects.create(table=table, day=sess.day, group=str(sess.agegroup), start=sess.start_time.strftime("%H:%M"), end=sess.end_time.strftime("%H:%M"))
        entries.append(temp)

    for obj in entries:
        data[obj.pk] = {
            "day":obj.day,
            "start_time":obj.start,
            "end_time":obj.end,
            "group":obj.group,
            "notes":obj.notes
        }
    return JsonResponse(data)

def add_row(request):
    table = Trainer_table.objects.get(trainer=request.user.trainer, active=True)
    obj = Table_entry.objects.create(table=table, day="Mo", start="17:00", end="19:00", group="A")
    data = {}
    data[obj.pk] = {
        "day":obj.day,
        "start_time":obj.start,
        "end_time":obj.end,
        "group":obj.group,
        "notes":obj.notes
        }
    return JsonResponse(data)

def delete_row(request):
    _,_,pk = request.GET.get('id', None).split("_")
    Table_entry.objects.filter(id=pk).delete()
    row_id = f"js_row_{pk}"
    data = {'row':row_id}
    return JsonResponse(data)

def send_email(table, hours):
    user = table.trainer.user
    try:
        sal = hours * float(user.trainer.salary.replace(",","."))
    except AttributeError:
        sal = 0.0

    with codecs.open(table.final_file.path, "w", encoding='windows-1252') as outfile:
        print(datetime.today().strftime('%d.%m.%Y'), file=outfile)
        print("--------", file=outfile)
        print(table.trainer.trainer_info(),file=outfile)
        print("--------", file=outfile)
        print("Datum\tWochentag\tGruppe\tVon\tBis\tDauer\tAnmerkung",file=outfile)
        print("\n".join([str(entry) for entry in Table_entry.objects.filter(table=table).all()]), file=outfile)
        print("--------", file=outfile)
        print(f"Stunden: {hours}\tTAE/Stunde: {user.trainer.salary} €\tGesamt: {sal:.2f} €",file=outfile)
    mail_subject=f"{datetime.today().strftime('%d.%m.%Y')}_Abrechnung_{user.first_name}_{user.last_name}"
    message= f"Trainerabrechnung von {user.first_name} {user.last_name}"
    to_email = settings.TO_EMAIL
    try:
        email=EmailMessage(mail_subject, message, to=[to_email], cc=[table.trainer.trainer_email])
        email.attach_file(table.final_file.path)
        email.send()
        table.final_file.delete()
        return True
    except ValueError:
        return False

def send_table(request):
    data = request.POST
    hours = 0

    for entry in zip(*[tuple(x[1]) for x in data.lists()][1:]):
        tab = Table_entry.objects.get(pk=entry[0])
        tab.date = entry[1]
        tab.day = entry[2]
        tab.group = entry[3]
        tab.start = entry[4]
        tab.end = entry[5]
        tab.dur = entry[6]
        hours += float(entry[6].replace(",","."))
        tab.notes = entry[7]
        try:
            tab.save()
        except django.core.exceptions.ValidationError:
            return JsonResponse({"data":False, "email":False})

    table = Trainer_table.objects.get(trainer=request.user.trainer, active=True)
    table.title = f"Abrechnung_{datetime.today().strftime('%d.%m.%Y')}_{request.user.first_name}_{request.user.last_name}"
    table.final_file.save(f"{datetime.today().strftime('%Y-%m-%d')}_Abrechnung_{request.user.first_name}_{request.user.last_name}.txt", ContentFile("Trainerabrechnung"))
    table.save()
    if send_email(table, hours):
        messages.add_message(request, messages.SUCCESS, 'Abrechnungstabelle verschickt')
        table.active = False
        table.save()
        return JsonResponse({"data":True})
    else:
        return JsonResponse({"data":False, "email":True})

#### More views ####

class AbrechnungstableDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Trainer_table

    def test_func(self):
        table = self.get_object()
        return hasattr(self.request.user,"chairman") or table.trainer == self.request.user.trainer

class TrainerListView(LoginRequiredMixin, ListView):
    model = Trainer
    template_name = "user_handling/trainer_list.html"

@login_required
@permission_required('members.add_trainer', raise_exception=True)
def register_trainer(request):
    choices = [(x.pk, f"{x.first_name} {x.last_name} ({x.profile.member_num})") for x in User.objects.filter(trainer__id__isnull=True)]
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
            return render(request, 'trainer/trainer_form.html', context={'form': form, "choices":choices})
    else:
        form = TrainerCreationForm()
    return render(request, 'trainer/trainer_form.html', context={"form":form,"choices":choices})

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



class TrainerSelfUpdateView(UpdateView, LoginRequiredMixin,UserPassesTestMixin):
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
        "image"
    ]
    template_name = "trainer/trainer_form.html"

    def get_object(self):
        return Trainer.objects.get(pk=self.request.user.trainer.pk)

    def test_func(self):
        return hasattr(self.user, "trainer")


