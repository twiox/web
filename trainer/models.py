from django.db import models
from members.models import Trainer, Session
from multiselectfield import MultiSelectField
from PIL import Image
from django.urls import reverse


# Create your models here.
class Education(models.Model):
    title = models.CharField("Titel", max_length=100)
    date = models.DateTimeField("Datum", blank=True, null=True)
    credits = models.IntegerField("Lernpunkte", blank=True, null=True)
    certificate = models.FileField(
        "Teilnahmebestätigung", upload_to="trainer_stuff", blank=True, null=True
    )

    def get_absolute_url(self):
        return reverse("trainer")


class Trainer_table(models.Model):
    title = models.CharField(max_length=140, blank=True, null=True)
    active = models.BooleanField(default=True)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
    final_file = models.FileField(upload_to="trainer_tables", blank=True, null=True)


class Table_entry(models.Model):
    table = models.ForeignKey(
        Trainer_table, blank=True, null=True, on_delete=models.SET_NULL
    )
    date = models.DateTimeField(blank=True, null=True)
    day = models.TextField(blank=True, null=True)
    group = models.TextField(blank=True, null=True)
    start = models.TextField(blank=True, null=True)
    end = models.TextField(blank=True, null=True)
    dur = models.TextField(blank=True, null=True)
    notes = models.TextField(default="")

    def __str__(self):
        return f"{self.date.strftime('%d.%m.%Y')}\t{self.day}\t{self.group}\t{self.start}\t{self.end}\t{self.dur}\t{self.notes}"
