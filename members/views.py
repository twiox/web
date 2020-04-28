from django.shortcuts import render
from django.views.generic import (
    ListView, 
    DetailView, 
    CreateView, 
    UpdateView, 
    DeleteView 
    )
from .models import Group, Event, Profile, Chairman, Session, Trainer
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

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

class EventDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    #template: event_detail.html
    model = Event
    
    def get_context_data(self, **kwargs):
        context = super(EventDetailView, self).get_context_data(**kwargs)
        context['is_trainer'] = hasattr(self.request.user,"trainer")
        return context
    
    def test_func(self):
        user_group = self.request.user.profile.group
        event = self.get_object()
        return (user_group in event.allowed_groups.all())

class EventCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    #template: event_detail.html
    model = Event
    fields=["title","allowed_groups","description","start_date","end_date"]
    def test_func(self):
        return hasattr(self.request.user, "trainer")
    
class EventUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    #template: event_detail.html
    model = Event
    fields=["title","allowed_groups","description","start_date","end_date"]
    
    #who can update the event?
    #right now: All trainers
    def test_func(self):
        return hasattr(self.request.user, "trainer")

class EventDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Event
    success_url = "/members/"
    #who can delete the event?
    #right now: All trainers
    def test_func(self):
        return hasattr(self.request.user, "trainer")

class SessionDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    #template: session_detail.html
    model = Session
    
    def get_context_data(self, **kwargs):
        context = super(SessionDetailView, self).get_context_data(**kwargs)
        context['is_trainer'] = hasattr(self.request.user,"trainer")
        return context
    
    def test_func(self):
        user_group = self.request.user.profile.group
        session = self.get_object()
        #The trainers of the group and the members
        if(hasattr(self.request.user, "trainer")):
            if(self.request.user.trainer in session.trainer.all()):
                return True
        return (user_group == session.group)
    

class SessionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    #template: event_form.html
    model = Session
    fields=["group","trainer","spot","title","website_title","day","start_time","end_time","hinweis"]
    def test_func(self):
        return hasattr(self.request.user, "trainer")

class SessionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    #template: event_form.html
    model = Session
    fields=["group","trainer","spot","title","website_title","day","start_time","end_time","hinweis"]
    
    #who can update the session?
    #right now: All trainers
    def test_func(self):
        return hasattr(self.request.user, "trainer")

class SessionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Session
    success_url = "/members/"
    #who can delete the event?
    #right now: All trainers
    def test_func(self):
        return hasattr(self.request.user, "trainer")