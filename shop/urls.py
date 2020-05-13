from django.urls import path
from . import views

# Create your tests here.
urlpatterns = [
    path("", views.ShopHomeView.as_view(), name="shop_home"),
    ]