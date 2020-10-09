from django.urls import path,include
from . import views

urlpatterns = [
    path("", views.interested_index, name="interested_index"),
    path("interessierte-angebot", views.interested_offers, name="offers"),
    path("interessierte-philosophie", views.interested_philosophy, name="philosophy"),
    path("interessierte-team", views.interested_team, name="team"),
    path("team/neu/leipzig/", views.TeamerLeipzigCreateView.as_view(),name="teamer_leipzig_create"),
    path("team/neu/jena/", views.TeamerJenaCreateView.as_view(),name="teamer_jena_create"),
    path("team/<int:pk>/ändern/", views.TeamerUpdateView.as_view(),name="teamer_update"),
    path("team/<int:pk>/löschen/", views.TeamerDeleteView.as_view(),name="teamer_delete"),
]

