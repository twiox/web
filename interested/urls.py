from django.urls import path,include
from . import views

urlpatterns = [
    path("", views.interested_index, name="interested_index"),
]

