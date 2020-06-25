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
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin,PermissionRequiredMixin
from .forms import EventUpdateParticipantForm, SessionForm, EventForm, UpdateMemberInformationForm
from django.contrib import messages
from datetime import datetime
from django.contrib.auth.models import User
# Create your views here.

@login_required
def index(request):
    """ This is the View for the homepage """
    group = Profile.objects.get(user = request.user).group
    sessions = Session.objects.filter(group=group)
    events = Event.objects.filter(allowed_groups=group)
    chairmen = Chairman.objects.filter(show__contains="member_site")
    training_messags = Message.objects.filter(groups=group).filter(display="sessions")
    event_messags = Message.objects.filter(groups=group).filter(display="events")
    if(hasattr(request.user, "trainer")):
        trainer_sessions = Session.objects.filter(trainer=Trainer.objects.get(user=request.user))
        events = Event.objects.all()
        training_messags = Message.objects.all().filter(display="sessions")
        event_messags = Message.objects.all().filter(display="events")
        trainer_groups = Group.objects.filter(session__trainer=Trainer.objects.get(user=request.user)).distinct()
    else:
        trainer_sessions = None
        trainer_groups = None
    if(hasattr(request.user, "chairman")):
        sessions = Session.objects.all()
        events = Event.objects.all()
        training_messags = Message.objects.all().filter(display="sessions")
        event_messags = Message.objects.all().filter(display="events")

    return render(
        request, "members/index.html",
        {"group":group, 
         "chairmen":chairmen, 
         "sessions":sessions, 
         "events":events,
         "trainer_sessions":trainer_sessions,
         "trainer_groups":trainer_groups,
         "training_messags":training_messags,
         "event_messags":event_messags,
         "chairman":hasattr(request.user, "chairman"),
         "groups":Group.objects.all(),
         }
            )

"""FOR THE EVENTS"""

class EventDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    #template: event_detail.html
    model = Event
    
    def test_func(self):
        user_group = self.request.user.profile.group
        event = self.get_object()
        perms = bool(hasattr(self.request.user, "trainer")+ hasattr(self.request.user,"chairman"))
        return True if user_group in event.allowed_groups.all() else perms

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
        perms = bool(hasattr(self.request.user, "trainer")+ hasattr(self.request.user,"chairman"))
        return True if user_group in event.allowed_groups.all() else perms

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
        perms = bool(hasattr(self.request.user, "trainer")+ hasattr(self.request.user,"chairman"))
        return True if user_group in event.allowed_groups.all() else perms

class EventParticipantsView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Event
    template_name = 'members/event_participants.html'
    
    def test_func(self):
        perms = bool(hasattr(self.request.user, "trainer")+ hasattr(self.request.user,"chairman"))
        return perms

"""FOR THE SESSIONS"""

class SessionDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    #template: session_detail.html
    model = Session
    
    def test_func(self):
        user_group = self.request.user.profile.group
        session = self.get_object()
        perms = bool(hasattr(self.request.user, "trainer")+ hasattr(self.request.user,"chairman"))
        #The trainers and the members 
        return True if user_group == session.group else perms

class SessionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    #template: event_form.html
    model = Session
    form_class = SessionForm
    permission_required = 'members.add_session'
    
    def form_valid(self, form):
        key={"Mo":1,"Di":2,"Mi":3,"Do":4,"Fr":5,"Sa":6,"So":7}
        self.object = form.save()
        if(self.object.day in key):
            self.object.day_key = key[self.object.day]
        return super().form_valid(form)
    
class SessionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    #template: event_form.html
    model = Session
    form_class = SessionForm
    permission_required = 'members.change_session'
    
    def form_valid(self, form):
        key={"Mo":1,"Di":2,"Mi":3,"Do":4,"Fr":5,"Sa":6,"So":7}
        self.object = form.save()
        if(self.object.day in key):
            self.object.day_key = key[self.object.day]
        return super().form_valid(form)


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
    permission_required = "members.delete_group"
    success_url = '/members/group/'
    
    def delete(self, request, *args, **kwargs):
        """
        Call the delete() method on the fetched object and then redirect to the
        success URL.
        """
        self.object = self.get_object()
        
        if(len(User.objects.filter(profile__group = self.object)) == 0):
            success_url = self.get_success_url()
            self.object.delete()
            return HttpResponseRedirect(success_url)
        
        else:
            messages.add_message(request, messages.ERROR, 'Fehler. Die Gruppe ist nicht leer')
            return HttpResponseRedirect(f"/members/group/{self.object.id}/delete/")

class GroupListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Group
    permission_required = 'members.delete_group'

class GroupDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Group
    permission_required = "members.see_group"
    
    def get_context_data(self, **kwargs):
        context = {"member_list":User.objects.filter(profile__group = self.object)}
        if self.object:
            context['object'] = self.object
            context_object_name = self.get_context_object_name(self.object)
            if context_object_name:
                context[context_object_name] = self.object
        context.update(kwargs)
        return super().get_context_data(**context)

class GroupUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    #template: event_detail.html
    model = Group
    #who can update the event?
    permission_required = 'members.change_group'
    fields = ["group_id"]

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

"""USER STUFF"""
class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'members/user_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super(UserDetailView, self).get_context_data(**kwargs)
        context['form'] = UpdateMemberInformationForm()
        return context