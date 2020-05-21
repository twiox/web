from django.db import models
from django.contrib.auth.models import User

CATEGORY_CHOICES = (
    ("T-Shirt", "tshirt"),
    ("Pullover", "pullover"),
)

# Create your models here.
class Item(models.Model):
    title = models.CharField("Titel", max_length=100)
    price = models.FloatField()
    category = models.CharField("Kategorie", choices=CATEGORY_CHOICES, max_length=30)
    description = models.TextField("Beschreibung")

    def __str__(self):
        return self.title
        
class QuantityCounter(models.Model):
    category = models.CharField("Größe", max_length=30)
    quantity = models.IntegerField("Anzahl auf Vorrat")
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    
    def __str__(self):
        return f'{self.item.title}_{self.category}'
        
class ItemImage(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    img1 = models.ImageField("Bild1 hochladen", upload_to="webshop")
    img2 = models.ImageField("Bild2 hochladen", blank=True, upload_to="webshop")
    img3 = models.ImageField("Bild3 hochladen", blank=True, upload_to="webshop")


class OrderItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} of {self.item.title}"

    def get_total_item_price(self):
        return self.quantity * self.item.price
