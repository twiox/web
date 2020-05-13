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
    image = models.ImageField("Bild hochladen")

    def __str__(self):
        return self.title
        
class QuantityCounter(models.Model):
    category = models.CharField("Größe", max_length=30)
    quantity = models.IntegerField("Anzahl auf Vorrat")
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.category

class OrderItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} of {self.item.title}"

    def get_total_item_price(self):
        return self.quantity * self.item.price

"""
class Order(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    ref_code = models.CharField(max_length=20, blank=True, null=True)
    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    ordered = models.BooleanField(default=False)
    shipping_address = models.ForeignKey(
        'Address', related_name='shipping_address', on_delete=models.SET_NULL, blank=True, null=True)
    billing_address = models.ForeignKey(
        'Address', related_name='billing_address', on_delete=models.SET_NULL, blank=True, null=True)
    payment = models.ForeignKey(
        'Payment', on_delete=models.SET_NULL, blank=True, null=True)
    coupon = models.ForeignKey(
        'Coupon', on_delete=models.SET_NULL, blank=True, null=True)
    being_delivered = models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    refund_requested = models.BooleanField(default=False)
    refund_granted = models.BooleanField(default=False)



    def __str__(self):
        return self.user.username

    def get_total(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_final_price()
        if self.coupon:
            total -= self.coupon.amount
        return total
"""