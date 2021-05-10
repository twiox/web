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
    path('events/<slug:event_slug>/', views.PublicEventView.as_view(), name='public_event'),
    path('events/neu', views.PublicEventCreateView.as_view(), name='public_event_add'),
    path('events/<slug:event_slug>/anmelden', views.event_participant_create_view, name='event_participant_create'),
    path('events/<slug:event_slug>/list', views.event_participant_list_view, name='event_participant_list'),
    path('events/<int:pk>/löschen', views.PublicEventDeleteView.as_view(), name='public_event_delete'),
    path('events/<int:pk>/bearbeiten', views.PublicEventUpdateView.as_view(), name='public_event_change'),
    path('events/participants/<int:pk>/löschen', views.EventParticipantDeleteView.as_view(), name="eventparticipant_remove"),
    path('events/participants/<int:pk>/ändern', views.EventParticipantUpdateView.as_view(), name="eventparticipant_change"),
    path('events/merch/neu', views.EventMerchCreateView.as_view(), name='eventmerch_create'),
    path('events/merch/<int:pk>/ändern', views.EventMerchUpdateView.as_view(), name='eventmerch_update'),
    path('events/merch/<int:pk>/löschen', views.EventMerchDeleteView.as_view(), name='eventmerch_delete'),
]

