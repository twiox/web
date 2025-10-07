from django.urls import path
from django.shortcuts import render, reverse
from django.http import HttpResponseRedirect
from datetime import datetime
from trainer.forms import TrainingSessionForm
from trainer.models import TrainingSessionEntry
from members.models import Trainer
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q

## HTMX snippets
def get_trainer_list(request, pk):
    """
    Get the trainer-list snippet for display in session-detail view 
    """
    session = TrainingSessionEntry.objects.get(pk=pk)
    type = request.GET.get('type')

    context = {'session':session, 'type':type}

    if type=='trainer':
        context.update({'trainer_list':session.trainer.all()})
    else:
        context.update({'trainer_list':session.cotrainer.all()})
    return render(request,'trainingsession/snippet_trainerlist.html',context)

@csrf_exempt
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
def add_trainer(request, pk):
    """
    Add trainer or cotrainer from session,then return the list-snippet 
    """
    session = TrainingSessionEntry.objects.get(pk=pk)
    trainer = Trainer.objects.get(pk=int(request.POST.get('trainer_pk')))
    type = request.GET.get('type')

    print(session, trainer,type)    

    if type == 'trainer':
        session.trainer.add(trainer)
    else:
        session.cotrainer.add(trainer)
    return get_trainer_list(request, pk)

def trainer_search(request, pk):
    """
    return a list of trainers based on the searched term
    """
    session = TrainingSessionEntry.objects.get(pk=pk)
    context = {'session':session, 'type':request.GET.get('type')}

    query = request.GET.get("trainer", "").strip().split()[0]

    results = Trainer.objects.filter(
        Q(user__first_name__icontains=query) |
        Q(user__last_name__icontains=query)
    )
    context.update({'trainer_list':results})
    
    return render(request, 'trainingsession/snippet_trainer-searchresult.html', context)


def session_detail_view(request, pk):
    object = TrainingSessionEntry.objects.get(pk=pk)
    return render(request, 'trainingsession/detail.html', {'object':object})

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
    path("<int:pk>/trainer", get_trainer_list, name='trainingsession_get_trainerlist'),
    path("<int:pk>/remove-trainer", remove_trainer, name='trainingsession_del_trainer'),
    path("<int:pk>/add-trainer", add_trainer, name='trainingsession_add_trainer'),
    path("<int:pk>/trainer-search", trainer_search, name="trainingsession_trainer_search"),
]

