from django.shortcuts import render
from django.views.generic import ListView
from .models import Group, Event, Profile
from django.contrib.auth.decorators import login_required

# Create your views here.

@login_required
def index(request):
    """ This is the View for the homepage """
    #get the group of the logged in user
    group = Profile.objects.filter(user = request.user)[0].group
    return render(request, "members/index.html",{"group":group})

