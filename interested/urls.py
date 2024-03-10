from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.interested_index, name="interested_index"),
    path("interessierte-angebot", views.interested_offers, name="offers"),
    path("interessierte-philosophie", views.interested_philosophy, name="philosophy"),
]
