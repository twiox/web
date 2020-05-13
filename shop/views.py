from django.shortcuts import render
from django.views.generic import ListView
from .models import Item
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin,PermissionRequiredMixin, UserPassesTestMixin

# Create your views here.
class ShopHomeView(LoginRequiredMixin, ListView):
    template_name = 'shop/shop_home.html'
    model = Item
        