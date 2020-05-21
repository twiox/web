from django.contrib import admin
from .models import Item, QuantityCounter, ItemImage
# Register your models here.

admin.site.register(Item)
admin.site.register(QuantityCounter)
admin.site.register(ItemImage)
