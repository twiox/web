from django.contrib import admin
from .models import Teamer, PublicEvent, EventParticipant, PublicEventParticipantMerch, EventMerch, ContactPerson, Tester

# Register your models here.
admin.site.register(Teamer)
admin.site.register(ContactPerson)
admin.site.register(PublicEvent)
admin.site.register(EventParticipant)
admin.site.register(EventMerch)
admin.site.register(PublicEventParticipantMerch)
admin.site.register(Tester)