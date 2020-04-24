from django.contrib import admin
from .models import Profile, Session, Spot, Event, Group

# Register your models here.
admin.site.register(Profile)
admin.site.register(Session)
admin.site.register(Spot)
admin.site.register(Group)
admin.site.register(Event)
