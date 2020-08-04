from django.urls import path,include
from . import views

urlpatterns = [
    path("", views.organizers_index, name="organizers_index"),
]

