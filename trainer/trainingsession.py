from django.urls import path
from django.shortcuts import render, reverse
from django.http import HttpResponseRedirect
from datetime import datetime
from trainer.forms import TrainingSessionForm
from trainer.models import TrainingSessionEntry

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
            return HttpResponseRedirect(reverse('trainingsession_detail', kwargs={'pk': session.pk}))

    today = datetime.today()
    return render(request, "trainingsession/index.html", {
        'today':today.strftime('%Y-%m-%d'),
        'form': form
    })

urlpatterns = [
    path("", session_create_view, name="trainingsession_create"),
    path("<int:pk>", session_detail_view, name="trainingsession_detail")
]

