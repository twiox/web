from django.urls import path,include
from . import views

urlpatterns = [
    path("", views.interested_index, name="interested_index"),
    path("offers", views.interested_offers, name="offers"),
    path("philosophy", views.interested_philosophy, name="philosophy"),
    path("team", views.interested_team, name="team"),
    path("team/new/leipzig/", views.TeamerLeipzigCreateView.as_view(),name="teamer_leipzig_create"),
    path("team/new/jena/", views.TeamerJenaCreateView.as_view(),name="teamer_jena_create"),
    path("team/<int:pk>/update/", views.TeamerUpdateView.as_view(),name="teamer_update"),
    path("team/<int:pk>/delete/", views.TeamerDeleteView.as_view(),name="teamer_delete"),
]

