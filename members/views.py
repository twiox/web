from django.shortcuts import render
from django.views.generic import ListView
from .models import Group, Event, Profile, Chairman, Session, Trainer
from django.contrib.auth.decorators import login_required

# Create your views here.

@login_required
def index(request):
    """ This is the View for the homepage """
    #get the group of the logged in user
    group = Profile.objects.get(user = request.user).group
    sessions = Session.objects.filter(group=group)
    events = Event.objects.filter(allowed_groups=group)
    chairmen = Chairman.objects.all()
    trainer_sessions = None
    if(Trainer.objects.get(user=request.user)):
        trainer_sessions = Session.objects.filter(trainer=Trainer.objects.get(user=request.user))
    
    return render(
        request, "members/index.html",
        {"group":group, 
         "chairmen":chairmen, 
         "sessions":sessions, 
         "events":events,
         "trainer_sessions":trainer_sessions}
            )

