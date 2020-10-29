from django.db import models
from multiselectfield import MultiSelectField
from PIL import Image
from django.urls import reverse

# Create your models here.
class Teamer(models.Model):
    choices =(
        ("leipzig","Leipzig"),
        ("jena","Jena")
    )
    priority = models.IntegerField()
    city = models.CharField("Stadt",max_length=30,choices=choices,blank=True)
    
    picture = models.ImageField("Foto", upload_to="team_pictures/")
    name = models.CharField("Name", max_length=100, default="Jon Doe")
    position = models.CharField("Position", max_length=100, default="Trainer")
    notes = models.TextField("Sonstiges", blank=True)
    public_telnr = models.CharField("Telefonnummer", max_length=100, blank=True, null=True)
    public_email = models.CharField("Email", max_length=150, blank=True, null=True)
    
    def get_absolute_url(self):
        return reverse('team')
        
    def save(self):
        super().save()
        img = Image.open(self.picture.path)
        if(img.height > img.width):
            cut = int((img.height-img.width)/2)
            img = img.crop((0, 0+cut, img.width, img.height-cut))
            img2 = img.resize((720,720))
            img2.save(self.picture.path)
        elif(img.width > img.height):
            cut = int((img.width-img.height)/2)
            img = img.crop((0+cut, 0, img.width-cut, img.height))
            img2 = img.resize((720,720))
            img2.save(self.picture.path)
        
    class Meta:
        ordering = ["priority"]
    
