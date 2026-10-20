from django.urls import path
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from datetime import datetime, timedelta
from itertools import groupby
from trainer.forms import TrainingSessionForm
from trainer.models import TrainingSessionEntry, TrainingSessionParticipant, TrainingSessionInvoice
from members.models import Trainer, Profile, Session, is_trainer, is_chairman
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_POST
from django.db import transaction
from django.db.models import Count, Q
from django.contrib import messages
from django.db.models.signals import post_save
from django.dispatch import receiver

def trainer_check(user):
    return is_trainer(user)

def chairman_check(user):
    return is_chairman(user) or user.is_superuser

@csrf_exempt
@user_passes_test(trainer_check)
def session_delete(request, pk):
    TrainingSessionEntry.objects.get(pk=pk).delete()
    return HttpResponse("") 

## HTMX snippets
@user_passes_test(trainer_check)
def get_participants_list(request, pk):
    """
    Get the trainer-list snippet for display in session-detail view 
    """
    session = TrainingSessionEntry.objects.get(pk=pk)
    type = request.GET.get('type')

    context = {'session':session, 'type':type}

    if type=='member':
        context.update({'object_list':session.participant.filter(user__isnull=False)})
    else:
        context.update({'object_list':session.participant.filter(user__isnull=True)})
    return render(request,'trainingsession/snippet_participantslist.html',context)

@user_passes_test(trainer_check)
def get_participants_table(request, pk):
    """
    Get the participants-table snippet for display in session-detail view 
    """
    session = TrainingSessionEntry.objects.get(pk=pk)
    context = {'session':session}
    context.update({'object_list':session.participant.filter(user__isnull=False)})

    return render(request,'trainingsession/snippet_participantslist_contact.html',context)

@user_passes_test(trainer_check)
def get_trainer_list(request, pk):
    """
    Get the trainer-list snippet for display in session-detail view 
    """
    session = TrainingSessionEntry.objects.get(pk=pk)
    type = request.GET.get('type')

    context = {'session':session, 'type':type}

    if type=='trainer':
        context.update({'object_list':session.trainer.all()})
    else:
        context.update({'object_list':session.cotrainer.all()})
    return render(request,'trainingsession/snippet_trainerlist.html',context)

@csrf_exempt
@user_passes_test(trainer_check)
def remove_trainer(request, pk):
    """
    Remove trainer or cotrainer from session,then return the list-snippet 
    """
    session = TrainingSessionEntry.objects.get(pk=pk)
    trainer = Trainer.objects.get(pk=int(request.POST.get('trainer_pk')))
    type = request.GET.get('type')

    if type == 'trainer':
        session.trainer.remove(trainer)
    else:
        session.cotrainer.remove(trainer)
    return get_trainer_list(request, pk)

@csrf_exempt
@user_passes_test(trainer_check)
def add_trainer(request, pk):
    """
    Add trainer or cotrainer from session,then return the list-snippet 
    """
    session = TrainingSessionEntry.objects.get(pk=pk)
    trainer = Trainer.objects.get(pk=int(request.POST.get('trainer_pk')))
    type = request.GET.get('type')

    if type == 'trainer':
        session.trainer.add(trainer)
    else:
        session.cotrainer.add(trainer)
    return get_trainer_list(request, pk)


@csrf_exempt
@user_passes_test(trainer_check)
def add_member(request, pk):
    """
    Add member to session,then return the list-snippet 
    """
    session = TrainingSessionEntry.objects.get(pk=pk)
    member = Profile.objects.get(pk=int(request.POST.get('member_pk')))
    type = request.GET.get('type')

    # create the participant
    TrainingSessionParticipant(
        session = session,
        user = member.user
    ).save()

    return get_participants_list(request, pk)

@csrf_exempt
@user_passes_test(trainer_check)
def add_nonmember(request, pk):
    session = TrainingSessionEntry.objects.get(pk=pk)
    type = request.GET.get('type')
    name = request.POST.get('name','').strip()

    # create the participant
    TrainingSessionParticipant(
        session = session,
        name = name
    ).save()

    return get_participants_list(request, pk)

@csrf_exempt
@user_passes_test(trainer_check)
def delete_participant(request, pk):
    """
    Remove participant from session,then return the list-snippet 
    """    
    TrainingSessionParticipant.objects.get(pk=int(request.POST.get('part_pk'))).delete()

    return get_participants_list(request, pk)

@user_passes_test(trainer_check)
def search(request, pk):
    """
    search function (trainer or member)
    return a list of items based on the searched term and type!
    """
    session = TrainingSessionEntry.objects.get(pk=pk)
    type = request.GET.get('type')
    context = {'session':session, 'type':type}
    try:
        query = request.GET.get("query", "").strip().split()[0]
    
        if type=='member':
            results = Profile.objects.filter(
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query)
            )
        elif type in ['trainer', 'cotrainer']:
            results = Trainer.objects.filter(active=True).filter(
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query)
            )
        else:
            results = []
    except IndexError: #empty string
        results = []
    
    context.update({'object_list':results})
    
    return render(request, 'trainingsession/snippet_searchresult.html', context)

# to populate the session form fields
def fill_session_details(request):
    session_id = request.GET.get("session_id")
    session = Session.objects.get(pk=session_id)

    return JsonResponse({
        "start_time": session.start_time.strftime("%H:%M"),
        "end_time": session.end_time.strftime("%H:%M"),
        "group": session.billing_label,
    })

# This is the detail-view
@user_passes_test(trainer_check)
def session_detail_view(request, pk):
    object = TrainingSessionEntry.objects.get(pk=pk)

    if request.method == 'POST':
        notes = request.POST.get('comment','')
        billable = request.POST.get('confirm','off')=='on'

        object.notes = notes
        object.billed = billable
        object.save()

    return render(request, 'trainingsession/detail.html', {'object':object})

# this is the main form for creating a new session entry
@user_passes_test(trainer_check)
def session_create_view(request):
    form = TrainingSessionForm
    if request.method == "POST":
        form = TrainingSessionForm(request.POST)  # if no files
        if form.is_valid():
            # get Form data
            session = form.save()
            session.trainer.add(request.user.trainer)
            return HttpResponseRedirect(reverse('trainingsession_detail', kwargs={'pk': session.pk}))

    today = datetime.today()
    return render(request, "trainingsession/index.html", {
        'today':today.strftime('%Y-%m-%d'),
        'form': form
    })


@user_passes_test(trainer_check)
def session_list_view(request):
    from collections import defaultdict
    from django.db.models.functions import ExtractYear

    year = request.GET.get('year', datetime.today().strftime('%Y'))
    all_years = (
        TrainingSessionEntry.objects
        .filter(date__isnull=False)
        .annotate(year=ExtractYear('date'))
        .values_list('year', flat=True)
        .distinct()
        .order_by('year')
    )

    # I want the structure
    # { month: {
    #     trainer: [
    #            Abrechnung 1,
    #            Abrechnung 2,
    #            Abrechnung 3  
    #         ]
    #     }   
    # }
    #

    grouping = {}
   
    sessions = TrainingSessionEntry.objects.filter(billed=True, date__year=int(year)).order_by('date')
    dates = []
    trainers = []

    for session in sessions:
        # compile a list of dates
        date = session.date.strftime('%Y-%m')
        if date not in dates:
            dates.append(date)
        if date not in grouping:
            grouping[date] = {}
        # compile a list of trainers
        for trainer in session.get_trainers:
            name = f"{trainer.user.first_name} {trainer.user.last_name}"
            if name not in trainers:
                trainers.append(name)
            # compile a list of sessions per date and trainer
            if name in grouping[date]:
                grouping[date][name].append(session)
            else:
                grouping[date][name] = [session]

    invoices = TrainingSessionInvoice.objects.select_related("trainer__user").annotate(session_count=Count("sessions"))
    unpayed_invoices = invoices.filter(date_payed__isnull=True).order_by('-date_billed')
    # the archive is grouped by the month an invoice was paid (default) or billed, newest first
    archive_by = 'rechnung' if request.GET.get('archiv') == 'rechnung' else 'bezahlt'
    if archive_by == 'bezahlt':
        archive_date = lambda inv: inv.date_payed
        payed_invoices = invoices.filter(date_payed__isnull=False).order_by('-date_payed')
    else:
        archive_date = lambda inv: inv.date_billed or inv.date_payed
        payed_invoices = invoices.filter(date_payed__isnull=False).order_by('-date_billed')
    archive = []
    for month, group in groupby(payed_invoices, key=lambda inv: archive_date(inv).replace(day=1).date()):
        group = list(group)
        archive.append({
            'month': month,
            'invoices': group,
            'total': sum(inv.total_money or 0 for inv in group),
        })

    return render(request, "trainingsession/list.html", {
            'grouping':grouping,
            # (key for the grouping, first day of the month for display)
            'months':[(d, datetime.strptime(d, '%Y-%m')) for d in sorted(dates)],
            'trainers':sorted(trainers),
            'unpayed_invoices':unpayed_invoices,
            'archive':archive,
            'archive_by':archive_by,
            'all_years':all_years,
            'year':int(year),
        }
    )

    
def hourly_rate(trainer):
    """The trainer's TAE per hour as a number, None if missing or invalid."""
    try:
        rate = float(trainer.salary.replace(",", "."))
    except (AttributeError, ValueError):
        return None
    return rate if rate > 0 else None


def session_hours(session):
    """Duration of a session entry in hours, None if start or end is not HH:MM."""
    try:
        start = datetime.strptime(session.start, "%H:%M")
        end = datetime.strptime(session.end, "%H:%M")
    except (TypeError, ValueError):
        return None
    return (end - start).total_seconds() / 3600


@user_passes_test(trainer_check)
@require_POST
def generate_invoices(request):
    """One invoice per trainer for all billed sessions that have no invoice yet.

    Trainers with missing data are skipped; their sessions stay open for the next run.
    """
    sessions = list(
        TrainingSessionEntry.objects.filter(invoice__isnull=True, billed=True).prefetch_related("trainer", "cotrainer")
    )
    trainers = sorted(set().union(*(x.get_trainers for x in sessions)), key=lambda t: (t.user.last_name, t.user.first_name))
    date_billed = datetime.today()
    created, skipped = [], []

    for trainer in trainers:
        name = f"{trainer.user.first_name} {trainer.user.last_name}"
        open_sessions = [x for x in sessions if trainer in x.get_trainers]
        rate = hourly_rate(trainer)
        hours = [session_hours(x) for x in open_sessions]
        if rate is None:
            skipped.append(f"{name} (kein TAE-Satz)")
            continue
        if None in hours:
            skipped.append(f"{name} (ungültige Uhrzeit in einer Trainingsstunde)")
            continue

        total_time = sum(hours)
        with transaction.atomic():
            invoice = TrainingSessionInvoice.objects.create(
                date_billed=date_billed,
                trainer=trainer,
                total_time=total_time,
                total_money=round(total_time * rate, 2),
            )
            invoice.sessions.add(*open_sessions)
            invoice.generate_pdf()
        created.append(name)

    if skipped:
        text = f"{len(created)} Abrechnung(en) erstellt. Nicht abgerechnet, bitte Daten ergänzen: {', '.join(skipped)}"
        messages.add_message(request, messages.WARNING, text)
    elif created:
        messages.add_message(request, messages.SUCCESS, f"{len(created)} Abrechnung(en) erstellt.")
    else:
        messages.add_message(request, messages.INFO, "Keine offenen Trainingsstunden zum Abrechnen.")
    return redirect('trainingsession_list')


@user_passes_test(chairman_check)
@require_POST
def mark_invoice_as_payed(request, pk):
    invoice = get_object_or_404(TrainingSessionInvoice, pk=pk)
    invoice.date_payed = datetime.today()
    invoice.save()
    messages.add_message(request, messages.SUCCESS, "Rechnung als bezahlt markiert")
    return redirect('trainingsession_list')


@user_passes_test(chairman_check)
@require_POST
def delete_invoice(request, pk):
    """Deletes an unpaid invoice; its sessions are open again for the next run."""
    invoice = get_object_or_404(TrainingSessionInvoice, pk=pk, date_payed__isnull=True)
    invoice.invoice_pdf.delete(save=False)
    invoice.delete()
    messages.add_message(request, messages.SUCCESS, "Rechnung gelöscht, die Trainingsstunden sind wieder offen")
    return redirect('trainingsession_list')


# Add signals
@receiver(post_save, sender=TrainingSessionInvoice)
def update_session(sender, instance, **kwargs):
    # trigger after invoice payed
    if instance.date_payed != None:
        # check for each sessions of the invoice instance that all associated invoices are payed
        # and set the sessions to 'payed' if that is true
        for session in instance.sessions.all():
            if all([x.date_payed != None for x in session.invoice.all()]):
                session.payed = True
                session.save()


urlpatterns = [
    path("", session_create_view, name="trainingsession_create"),
    path("list", session_list_view, name="trainingsession_list"),
    path("generate-invoices", generate_invoices, name="generate_invoices"),
    path("<int:pk>", session_detail_view, name="trainingsession_detail"),
    path("<int:pk>/remove/", session_delete, name='trainingsession_delete'),
    path("<int:pk>/set-payed/", mark_invoice_as_payed, name='trainingsession_mark_invoice_as_payed'),
    path("rechnung/<int:pk>/loeschen/", delete_invoice, name='trainingsession_delete_invoice'),
    path("<int:pk>/search", search, name="trainingsession_search"),
    path("<int:pk>/trainer/list", get_trainer_list, name='trainingsession_get_trainerlist'),
    path("<int:pk>/trainer/add", add_trainer, name='trainingsession_add_trainer'),
    path("<int:pk>/trainer/remove", remove_trainer, name='trainingsession_del_trainer'),
    path("<int:pk>/participant/list", get_participants_list, name='trainingsession_get_participants'),
    path("<int:pk>/participant/table", get_participants_table, name='trainingsession_get_participants_table'),
    path("<int:pk>/participant/add", add_member, name='trainingsession_add_member'),
    path("<int:pk>/participant/remove/", delete_participant, name='trainingsession_del_participant'),
    path("<int:pk>/participant/non-member/", add_nonmember, name="trainingsession_nonmember_add"),
    path("ajax/session-details/", fill_session_details, name="fill_session_details")
]

