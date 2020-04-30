from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.views.generic import (
    ListView, 
    DetailView, 
    CreateView, 
    UpdateView, 
    DeleteView 
    )
from django.views import View
from .models import Group, Event, Profile, Chairman, Session, Trainer, Spot
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin,PermissionRequiredMixin
from .forms import EventUpdateParticipantForm
from django.contrib import messages
# Create your views here.

@login_required
def index(request):
    """ This is the View for the homepage """
    group = Profile.objects.get(user = request.user).group
    sessions = Session.objects.filter(group=group)
    events = Event.objects.filter(allowed_groups=group)
    chairmen = Chairman.objects.all()
    if(hasattr(request.user, "trainer")):
        trainer_sessions = Session.objects.filter(trainer=Trainer.objects.get(user=request.user))
    else:
        trainer_sessions = None
    return render(
        request, "members/index.html",
        {"group":group, 
         "chairmen":chairmen, 
         "sessions":sessions, 
         "events":events,
         "trainer_sessions":trainer_sessions}
            )

"""FOR THE EVENTS"""

class EventDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    #template: event_detail.html
    model = Event
    
    def test_func(self):
        user_group = self.request.user.profile.group
        event = self.get_object()
        return True if user_group in event.allowed_groups.all() else hasattr(self.request.user, "trainer")

class EventCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    #template: event_detail.html
    model = Event
    fields=["title","allowed_groups","description","start_date","end_date","hinweis","deadline"]
    permission_required = 'members.add_event'
    
class EventUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    #template: event_detail.html
    model = Event
    fields=["title","allowed_groups","description","start_date","end_date","hinweis","deadline"]
    #who can update the event?
    permission_required = 'members.change_event'

class EventDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Event
    success_url = "/members/"
    #who can delete the event?
    permission_required = 'members.delete_event'

class EventParticipateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    template_name = 'members/event_participate.html'
    form_class = EventUpdateParticipantForm
    model = Event
       
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            event = self.get_object()
            user = self.request.user
            event.participants.add(self.request.user)
            event.save()
            messages.add_message(request, messages.SUCCESS, 'Du bist erfolgreich angemeldet')
            return HttpResponseRedirect(f"/members/events/{event.id}")
        return render(request, self.template_name, {'form': form})
        
    def test_func(self):
        user_group = self.request.user.profile.group
        event = self.get_object()
        return True if user_group in event.allowed_groups.all() else hasattr(self.request.user, "trainer")

class EventUnParticipateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    template_name = 'members/event_unparticipate.html'
    form_class = EventUpdateParticipantForm
    model = Event
       
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            event = self.get_object()
            user = self.request.user
            event.participants.remove(self.request.user)
            event.save()
            messages.add_message(request, messages.SUCCESS, 'Du hast dich erfolgreich abgemeldet')
            return HttpResponseRedirect(f"/members/events/{event.id}")
        return render(request, self.template_name, {'form': form})
        
    def test_func(self):
        user_group = self.request.user.profile.group
        event = self.get_object()
        return True if user_group in event.allowed_groups.all() else hasattr(self.request.user, "trainer")        

"""FOR THE SESSIONS"""

class SessionDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    #template: session_detail.html
    model = Session
    
    def test_func(self):
        user_group = self.request.user.profile.group
        session = self.get_object()
        #The trainers and the members 
        return True if user_group == session.group else hasattr(self.request.user, "trainer")

class SessionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    #template: event_form.html
    model = Session
    fields=["group","trainer","spot","title","website_title","day","start_time","end_time","hinweis"]
    permission_required = 'members.add_session'
    
    
class SessionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    #template: event_form.html
    model = Session
    fields=["group","trainer","spot","title","website_title","day","start_time","end_time","hinweis"]
    permission_required = 'members.change_session'


class SessionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Session
    success_url = "/members/"
    permission_required = 'members.delete_session'

"""FOR THE SPOTS"""
class SpotListView(LoginRequiredMixin, ListView):
    model = Spot

class SpotDetailView(LoginRequiredMixin, DetailView):
    model = Spot
        
class SpotCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    #template: event_form.html
    model = Spot
    fields=["title","coords","adress","picture"]
    permission_required = 'members.add_spot'

class SpotUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    #template: event_form.html
    model = Spot
    fields=["title","coords","adress","picture"]
    permission_required = 'members.change_spot'
 
class SpotDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Spot
    success_url = "/members/"
    permission_required = 'members.delete_spot'
