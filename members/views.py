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
from .models import Group, Event, Profile, Chairman, Session, Trainer, Spot, Message
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin,PermissionRequiredMixin
from .forms import EventUpdateParticipantForm, SessionForm, EventForm
from django.contrib import messages
from datetime import datetime
# Create your views here.

@login_required
def index(request):
    """ This is the View for the homepage """
    group = Profile.objects.get(user = request.user).group
    sessions = Session.objects.filter(group=group)
    events = Event.objects.filter(allowed_groups=group)
    chairmen = Chairman.objects.all()
    training_messags = Message.objects.filter(groups=group).filter(display="sessions")
    event_messags = Message.objects.filter(groups=group).filter(display="events")
    if(hasattr(request.user, "trainer")):
        trainer_sessions = Session.objects.filter(trainer=Trainer.objects.get(user=request.user))
        events = Event.objects.all()
        training_messags = Message.objects.all().filter(display="sessions")
        event_messags = Message.objects.all().filter(display="events")
    else:
        trainer_sessions = None
    return render(
        request, "members/index.html",
        {"group":group, 
         "chairmen":chairmen, 
         "sessions":sessions, 
         "events":events,
         "trainer_sessions":trainer_sessions,
         "training_messags":training_messags,
         "event_messags":event_messags,
         }
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
    form_class = EventForm
    permission_required = 'members.add_event'
    
class EventUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    #template: event_detail.html
    model = Event
    form_class = EventForm
    #who can update the event?
    permission_required = 'members.change_event'

class EventDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Event
    success_url = "/members/#events"
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
    form_class = SessionForm
    permission_required = 'members.add_session'
    
class SessionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    #template: event_form.html
    model = Session
    form_class = SessionForm
    permission_required = 'members.change_session'


class SessionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Session
    success_url = "/members/#training"
    permission_required = 'members.delete_session'

"""FOR THE SPOTS"""
class SpotListView(LoginRequiredMixin, ListView):
    model = Spot

class SpotDetailView(LoginRequiredMixin, DetailView):
    model = Spot
        
class SpotCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    #template: event_form.html
    model = Spot
    fields=["title","lat","long","description"]
    permission_required = 'members.add_spot'

class SpotUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    #template: event_form.html
    model = Spot
    fields=["title","lat","long","description"]
    permission_required = 'members.change_spot'
 
class SpotDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Spot
    success_url = "/members/"
    permission_required = 'members.delete_spot'

"""For the Groups"""
class GroupCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Group
    permission_required = "members.create_group"
    fields = ["group_id"]

class GroupDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Group
    permission_required = "members.delete_crew"
    success_url = '/members/group/'

class GroupListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Group
    permission_required = 'members.delete_spot'

"""For The Messages"""
class MessageEveCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    #template: event_detail.html
    model = Message
    fields=["title","message","groups"]
    permission_required = 'members.add_message'
    
    def form_valid(self, form):
        message = form.save()
        message.author = self.request.user
        message.display = "events"
        message.save()
        return super(MessageEveCreateView, self).form_valid(form)

class MessageSessCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    #template: event_detail.html
    model = Message
    fields=["title","message","groups"]
    permission_required = 'members.add_message'
    
    def form_valid(self, form):
        message = form.save()
        message.author = self.request.user
        message.display = "sessions"
        message.save()
        return super(MessageSessCreateView, self).form_valid(form)
        
class MessageDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Message
    success_url = "/members/"
    permission_required = 'members.delete_message'

class MessageUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    #template: event_form.html
    model = Message
    fields=["title","message","groups"]
    permission_required = 'members.change_message'
    
    def form_valid(self, form):
        message = form.save()
        message.author = self.request.user
        message.date = datetime.now()
        message.save()
        return super(MessageUpdateView, self).form_valid(form)
