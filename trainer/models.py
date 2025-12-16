from django.db import models
from members.models import Trainer, Group, Session, User
from multiselectfield import MultiSelectField
from PIL import Image
from django.urls import reverse

class Trainer_table(models.Model):
    title = models.CharField(max_length=140, blank=True, null=True)
    active = models.BooleanField(default=True)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
    final_file = models.FileField(upload_to="trainer_tables", blank=True, null=True)
    
class Table_entry(models.Model):
    table = models.ForeignKey(Trainer_table, blank=True, null=True, on_delete=models.SET_NULL)
    date = models.DateTimeField(blank=True, null=True)
    day = models.TextField(blank=True, null=True)
    group = models.TextField(blank=True, null=True)
    start = models.TextField(blank=True, null=True)
    end = models.TextField(blank=True, null=True)
    dur = models.TextField(blank=True, null=True)
    notes = models.TextField(default = "")
    
    def __str__(self):
        return f"{self.date.strftime('%d.%m.%Y')}\t{self.day}\t{self.group}\t{self.start}\t{self.end}\t{self.dur}\t{self.notes}"

#
# We need to track the participation of members in the training sessions. This will eventually replace the Trainer_table model
# (or fill it automatically at the end of the month)
#

class TrainingSessionEntry(models.Model):
    trainer = models.ManyToManyField(Trainer, related_name='trainer', blank=True)
    cotrainer = models.ManyToManyField(Trainer, related_name='cotrainer', blank=True) # in the case we ever have different rates of payment again...
    session = models.ForeignKey(Session, related_name='session', blank=True, null=True, on_delete=models.SET_NULL) # link to a session to get all the related information
    date = models.DateTimeField(blank=True, null=True)
    day = models.TextField(blank=True, null=True)
    group = models.TextField(blank=True, null=True)
    start = models.TextField(blank=True, null=True)
    end = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    billed = models.BooleanField(default=False) # invoice sent!
    payed = models.BooleanField(default=False) # invoice payed

    def __str__(self):
        return f"{self.date.strftime('%d.%m.%Y')}-{self.group}"


class TrainingSessionParticipant(models.Model):
    session = models.ForeignKey(TrainingSessionEntry, on_delete=models.CASCADE, related_name='participant')
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )  # set null, so that we still see the number of participants even after user is gone
    name = models.CharField("Name", max_length=200, null=True, blank=True) # in case of Probetraining or non-members
    notes = models.TextField("Notizen", blank=True, null=True) #add notes, e.g. if left earlier or if needed first aid

    def __str__(self):
        if user:
            return f"{self.user.first_name} {self.user.last_name}"
        return self.name