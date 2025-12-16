from django.urls import path
from django.shortcuts import render, reverse
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from datetime import datetime
from trainer.forms import TrainingSessionForm
from trainer.models import TrainingSessionEntry, TrainingSessionParticipant
from members.models import Trainer, Profile, Session
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q

def trainer_check(user):
    return hasattr(user, "trainer")

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
            results = Trainer.objects.filter(
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
        "start_time": session.start_time.strftime("%H:%m"),
        "end_time": session.end_time.strftime("%H:%m"),
        "age_upper": session.agegroup.upper,
        "age_lower": session.agegroup.lower
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

urlpatterns = [
    path("", session_create_view, name="trainingsession_create"),
    path("<int:pk>", session_detail_view, name="trainingsession_detail"),
    path("<int:pk>/remove/", session_delete, name='trainingsession_delete'),
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

