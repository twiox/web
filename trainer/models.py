from django.db import models
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

