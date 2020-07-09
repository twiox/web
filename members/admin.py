from django.contrib import admin
from .models import Profile, Session, Spot, Event, Group, Trainer, Message, Chairman, Participant

# Register your models here.
admin.site.register(Profile)
admin.site.register(Session)
admin.site.register(Spot)
admin.site.register(Group)
admin.site.register(Event)
admin.site.register(Trainer)
admin.site.register(Message)
admin.site.register(Chairman)
admin.site.register(Participant)
