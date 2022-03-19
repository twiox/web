from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView
    )
from .models import Group, Event, Profile, Chairman, Session, Trainer, Spot, Message, News, AdditionalEmail,ShopItem, Image, Gallery
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin,PermissionRequiredMixin
from .forms import EventUpdateParticipantForm,EventUpdateParticipantForm2, SessionForm, EventForm, UpdateMemberInformationForm,UpdateMemberEmailForm,SpotForm
from django.contrib import messages
from datetime import datetime
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.views import PasswordChangeView
from django.conf import settings
import markdown
# Create your views here.
import os


@login_required
def index(request):
    """ This is the View for the homepage """
    group = Profile.objects.get(user = request.user).group
    sessions = Session.objects.filter(group=group)
    events = Event.objects.filter(allowed_groups=group)
    chairmen = Chairman.objects.filter(show__contains="member_site")
    training_messags = Message.objects.filter(groups=group).filter(display="sessions")
    event_messags = Message.objects.filter(groups=group).filter(display="events")
    posts = News.objects.all().order_by('-id')
    if len(posts) > 3:
        posts = posts[:3]

    if(hasattr(request.user, "trainer")):
        if(group.group_id != "T"):
            sessions = Session.objects.filter(group__group_id__in=["T",group.group_id])
        events = Event.objects.all()
        training_messags = Message.objects.all().filter(display="sessions")
        event_messags = Message.objects.all().filter(display="events")
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
         "training_messags":training_messags,
         "event_messags":event_messags,
         "chairman":hasattr(request.user, "chairman"),
         "groups":Group.objects.all(),
         "posts":posts,
         }
            )

"""FOR THE EVENTS"""

class EventListView(LoginRequiredMixin, ListView, UserPassesTestMixin):
    model = Event
    template = "members/event_list.html"
    
    def test_func(self):
        user_group = self.request.user.profile.group
        return bool(hasattr(self.request.user, "trainer")+ hasattr(self.request.user,"chairman"))

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
    
    def form_valid(self, form):
        self.object = form.save()
        self.object.description_rendered = markdown.markdown(self.object.description)
        messages.add_message(self.request, messages.SUCCESS, 'Veranstaltung erstellt')
        return super().form_valid(form)

class EventUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    #template: event_detail.html
    model = Event
    form_class = EventForm
    #who can update the event?
    permission_required = 'members.change_event'
    
    def get_context_data(self, **kwargs):
        context = {"picked_groups" : [id for id,_ in self.object.allowed_groups.values_list()]}
        context['object'] = self.request.user
        context.update(kwargs)
        return super().get_context_data(**context)
    
    
    def form_valid(self, form):
        self.object = form.save()
        self.object.description_rendered = markdown.markdown(self.object.description)
        messages.add_message(self.request, messages.SUCCESS, 'Veranstaltung geändert')
        return super().form_valid(form)

class EventDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Event
    #success_url = "/mitglieder/#events"
    #who can delete the event?
    permission_required = 'members.delete_event'
    
    def get_success_url(self, **kwargs):
        return reverse("index")+"#events"

class EventParticipateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    template_name = 'members/event_participate.html'
    form_class = EventUpdateParticipantForm
    model = Event

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            event = self.get_object()
            event.participants.add(request.user)
            event.save()
            messages.add_message(request, messages.SUCCESS, 'Du hast dich erfolgreich angemeldet')
            return HttpResponseRedirect(reverse("event_detail", kwargs={"pk":event.id}))
        return render(request, self.template_name, {'form': form, 'object':self.get_object()})

    def test_func(self):
        user_group = self.request.user.profile.group
        event = self.get_object()
        perms = bool(hasattr(self.request.user, "trainer")+ hasattr(self.request.user,"chairman"))
        return True if user_group in event.allowed_groups.all() else perms

class EventUnParticipateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    template_name = 'members/event_unparticipate.html'
    form_class = EventUpdateParticipantForm2
    model = Event

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            event = self.get_object()
            event.participants.remove(self.request.user)
            event.save()
            messages.add_message(request, messages.SUCCESS, 'Du hast dich erfolgreich abgemeldet')
            return HttpResponseRedirect(reverse("event_detail", kwargs={"pk":event.id}))
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
        perms = bool(hasattr(self.request.user, "trainer")+hasattr(self.request.user,"chairman"))
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

    def get_context_data(self, **kwargs):
        context = {"api_key":settings.GOOGLE_API_KEY}
        if self.object:
            context['object'] = self.object
            context_object_name = self.get_context_object_name(self.object)
            if context_object_name:
                context[context_object_name] = self.object
        context.update(kwargs)
        return super().get_context_data(**context)

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
        messages.add_message(self.request, messages.SUCCESS, 'Einheit erstellt')
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
        messages.add_message(self.request, messages.SUCCESS, 'Einheit geändert')
        return super().form_valid(form)


class SessionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Session
    permission_required = 'members.delete_session'

    def post(self, request, *args, **kwargs):
        messages.add_message(request, messages.SUCCESS, 'Einheit gelöscht')
        return self.delete(request, *args, **kwargs)
    
    def get_success_url(self, **kwargs):
        return reverse("index")+"#training"

"""FOR THE SPOTS"""
class SpotListView(LoginRequiredMixin, ListView):
    model = Spot

class SpotDetailView(LoginRequiredMixin, DetailView):
    model = Spot

    def get_context_data(self, **kwargs):
        context = {"api_key":settings.GOOGLE_API_KEY}
        if self.object:
            context['object'] = self.object
            context_object_name = self.get_context_object_name(self.object)
            if context_object_name:
                context[context_object_name] = self.object
        context.update(kwargs)
        return super().get_context_data(**context)

class SpotCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    #template: event_form.html
    model = Spot
    form_class = SpotForm
    permission_required = 'members.add_spot'

    def form_valid(self, form):
        self.object = form.save()
        self.object.description_rendered = markdown.markdown(self.object.description)
        messages.add_message(self.request, messages.SUCCESS, 'Spot geändert')
        return super().form_valid(form)

class SpotUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    #template: event_form.html
    model = Spot
    form_class = SpotForm
    permission_required = 'members.change_spot'

    def form_valid(self, form):
        self.object = form.save()
        self.object.description_rendered = markdown.markdown(self.object.description)
        messages.add_message(self.request, messages.SUCCESS, 'Spot geändert')
        return super().form_valid(form)

class SpotDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Spot
    permission_required = 'members.delete_spot'

    def post(self, request, *args, **kwargs):
        messages.add_message(request, messages.SUCCESS, 'Spot gelöscht')
        return self.delete(request, *args, **kwargs)
    
    def get_success_url(self, **kwargs):
        return reverse("spot_list")

"""For the news"""
class NewsListView(LoginRequiredMixin, ListView):
    model = News

class NewsDetailView(LoginRequiredMixin, DetailView):
    model = News

class NewsCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    #template: event_form.html
    model = News
    permission_required = 'members.add_news'
    fields = ["title","capture","content"]

    def form_valid(self, form):
        self.object = form.save()
        self.object.content_rendered = markdown.markdown(self.object.content)
        messages.add_message(self.request, messages.SUCCESS, 'Beitrag erstellt')
        return super().form_valid(form)

class NewsUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    #template: event_form.html
    model = News
    permission_required = 'members.change_news'
    fields = ["title","capture", "content"]

    def form_valid(self, form):
        self.object = form.save()
        self.object.content_rendered = markdown.markdown(self.object.content)
        messages.add_message(self.request, messages.SUCCESS, 'Beitrag geändert')
        return super().form_valid(form)

class NewsDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = News
    permission_required = 'members.delete_news'

    def post(self, request, *args, **kwargs):
        messages.add_message(request, messages.SUCCESS, 'Beitrag gelöscht')
        return self.delete(request, *args, **kwargs)
    
    def get_success_url(self, **kwargs):
        return reverse("news_list")

"""For the Groups"""
class GroupCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Group
    permission_required = "members.create_group"
    fields = ["group_id"]

    def form_valid(self, form):
        self.object = form.save()
        messages.add_message(self.request, messages.SUCCESS, 'Gruppe erstellt')
        return super().form_valid(form)


class GroupDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Group
    permission_required = "members.delete_group"

    def delete(self, request, *args, **kwargs):
        """
        Call the delete() method on the fetched object and then redirect to the
        success URL.
        """
        self.object = self.get_object()

        if(len(User.objects.filter(profile__group = self.object)) == 0):
            success_url = self.get_success_url()
            self.object.delete()
            messages.add_message(request, messages.SUCCESS, 'Gruppe gelöscht')
            return HttpResponseRedirect(success_url)

        else:
            messages.add_message(request, messages.ERROR, 'Fehler. Die Gruppe ist nicht leer')
            return HttpResponseRedirect(reverse("group_delete",kwargs={"pk":self.object.id}))
    
    def get_success_url(self, **kwargs):
        return reverse("group_list")

class GroupListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Group
    permission_required = 'members.delete_group'
    

class RealGroupDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Group
    template_name = "members/real_group_detail.html"
    
    def test_func(self):
        if hasattr(self.request.user, 'trainer'):
            return True
        if hasattr(self.request.user,'chairman'):
            return True
        return False
    
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

    def form_valid(self, form):
        self.object = form.save()
        messages.add_message(self.request, messages.SUCCESS, 'Name der Gruppe geändert')
        return super().form_valid(form)

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
    permission_required = 'members.delete_message'
    
    def get_success_url(self, **kwargs):
        return reverse("index")

class MessageUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    #template: event_form.html
    model = Message
    fields=["title","message","groups"]
    permission_required = 'members.change_message'
    
    def get_context_data(self, **kwargs):
        context = {"group_values" : [id for id,_ in self.object.groups.values_list()]}
        context['object'] = self.request.user
        context.update(kwargs)
        return super().get_context_data(**context)
    
    def form_valid(self, form):
        message = form.save()
        message.author = self.request.user
        message.date = datetime.now()
        message.save()
        return super(MessageUpdateView, self).form_valid(form)

"""USER STUFF"""
class UserDetailView(LoginRequiredMixin, UpdateView):
    # TODO: get email for every change in "Hinweis"
    model = User
    template_name = 'members/user_detail.html'
    form_class = UpdateMemberInformationForm
    
    def get_object(self, queryset=None):
        obj = self.request.user
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['additional_emails'] = AdditionalEmail.objects.filter(user=self.object)
        return super().get_context_data(**context)

    def handle_uploaded_file(self,f, name):
        try:
            os.mkdir("media/user_uploads")
        except:
            pass

        with open(f'media/user_uploads/{name}', 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            mail_subject=f"Mitteilung von {request.user.first_name} {request.user.last_name}"
            message = form.cleaned_data.get("comment")
            to_email = settings.TO_EMAIL
            email=EmailMessage(mail_subject, message, to=[to_email], cc=[request.user.email])
            if(request.FILES.get('attachment')):
                document = request.FILES.get('attachment')
                self.handle_uploaded_file(document, str(document))
                email.attach_file('media/user_uploads/'+str(document))
            email.send()
            messages.add_message(request, messages.SUCCESS, 'Nachricht erfolgreich versendet')
            return HttpResponseRedirect(reverse("profile_detail", kwargs={"pk": request.user.id}))
        return render(request, self.template_name, {'form': form})



class EmailUpdateView(LoginRequiredMixin,UserPassesTestMixin, UpdateView):
    model = User
    template_name = 'members/update_email.html'
    form_class = UpdateMemberEmailForm
    
    def get_object(self, queryset=None):
        obj = self.request.user
        return obj
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            #check the password
            if(request.user.check_password(form.cleaned_data.get("password"))):
                #check, if both mails are the same
                if(form.cleaned_data.get("email1") == form.cleaned_data.get("email2")):
                    request.user.email = form.cleaned_data.get("email1")
                    request.user.save()
                    messages.add_message(request, messages.SUCCESS, 'E-Mail erfolgreich geändert')
                    return HttpResponseRedirect(reverse("profile_detail"))
                form.add_error('email1', 'Die E-Mails stimmen nicht überein')
                return render(request, self.template_name, {'form': form, "object":request.user})
            form.add_error('password', 'Das Passwort stimmt nicht')
            return render(request, self.template_name, {'form': form, "object":request.user})
        return render(request, self.template_name, {'form': form, "object":request.user})

    def test_func(self):
        user = self.request.user
        person = self.get_object()
        return user == person

class PasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'members/update_pw.html'

    def get_object(self, queryset=None):
        obj = self.request.user
        return obj

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            request.user=form.save()
            update_session_auth_hash(request,request.user)
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
            
    def get_context_data(self, **kwargs):
        context = {}
        context['object'] = self.request.user
        context.update(kwargs)
        return super().get_context_data(**context)

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, 'Passwort erfolgreich geändert')
        return HttpResponseRedirect(reverse("profile_detail"))

class UsernameUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'members/update_username.html'
    fields = ["username"]
    

    def get_object(self, queryset=None):
        obj = self.request.user
        return obj

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, 'Nutzername erfolgreich geändert')
        return reverse('profile_detail')
        

class AddressChangeView(LoginRequiredMixin, UpdateView):
    model = Profile
    template_name = 'members/update_address.html'
    fields = ["address", "telephone", "parent", "parent_telnr"]
    
    def get_object(self, queryset=None):
        obj = self.request.user.profile
        return obj

    def get_success_url(self):
        return reverse('profile_detail')



class ShopItemListView(LoginRequiredMixin, ListView):
    model = ShopItem


class ShopItemUpdateView(LoginRequiredMixin, UpdateView, PermissionRequiredMixin):
    model = ShopItem
    fields = ["title","description","price"]
    permission_required = 'members.update_shop_item'


    def get_success_url(self):
        return reverse('shop')
    
    def form_valid(self, form):
        self.object = form.save()
        self.object.description_rendered = markdown.markdown(self.object.description)
        return super().form_valid(form)

    
## AJAX ##
@login_required
def get_image_data(request):
    data = {x:v[0] for (x,v) in dict(request.GET).items()}
    image = Image.objects.get(pk=data["id"])
    return JsonResponse({"data":{"title":image.title, "alt":image.alt, "priority":image.priority}})


@login_required
def set_image_data(request):
    data = {x:v[0] for (x,v) in dict(request.GET).items()}
    image = Image.objects.get(pk=data["id"])
    image.alt = data['alt']
    image.priority = data['prio']
    image.title = data['title']
    image.save()
    return JsonResponse({"data":{"title":image.title, "alt":image.alt, "priority":image.priority}})


@login_required
def delete_image(request):
    data = {x:v[0] for (x,v) in dict(request.GET).items()}
    image = Image.objects.get(pk=data["id"])
    image.delete()
    return JsonResponse({"data":True})

@csrf_exempt
def add_image(request):
    print('test')
    print(request)

@login_required
def add_another_email(request):
    data = request.POST
    user = request.user
    data = {k:v[0] for (k,v) in dict(request.POST).items()}
    email = AdditionalEmail.objects.create(user=user, title=data['title'], email=data['email'])
    email.save()
    return JsonResponse({"data":data})

@login_required
def delete_additional_email(request):
    data = {x:v[0] for (x,v) in dict(request.GET).items()}
    user = request.user
    email = AdditionalEmail.objects.get(user=user, pk=int(data['id']))
    email.delete()
    return JsonResponse({"data":data})

@permission_required('auth.add_user')
def delete_additional_email_chair(request, pk):
    data = {x:v[0] for (x,v) in dict(request.GET).items()}
    user =  User.objects.get(pk=pk)
    email = AdditionalEmail.objects.get(user=user, pk=int(data['id']))
    email.delete()
    return JsonResponse({"data":data})
