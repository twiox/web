from django.urls import path,include
from . import views

urlpatterns = [
    path("", views.interested_index, name="interested_index"),
    path("offers", views.interested_offers, name="offers"),
    path("philosophy", views.interested_philosophy, name="philosophy"),
    path("team", views.interested_team, name="team"),
]

