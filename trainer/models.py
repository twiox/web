from django.db import models
from members.models import Trainer, Group, Session
from multiselectfield import MultiSelectField
from PIL import Image
from django.urls import reverse

# Create your models here.
class Education(models.Model):
    title = models.CharField("Titel", max_length=100)
    date = models.DateTimeField("Datum", blank=True, null=True)
    credits = models.IntegerField("Lernpunkte", blank=True, null=True)
    certificate = models.FileField("Teilnahmebestätigung", upload_to = "trainer_stuff", blank=True, null=True)
    
    def get_absolute_url(self):
        return reverse('trainer')

class Trainer_table(models.Model):
    title = models.CharField(max_length=140)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
    
class Table_entry(models.Model):
    table = models.ForeignKey(Trainer_table, blank=True, null=True, on_delete=models.SET_NULL)
    date = models.DateTimeField(blank=True, null=True)
    session = models.ForeignKey(Session,blank=True, null=True, on_delete=models.SET_NULL)
    notes = models.TextField(blank=True, null=True)