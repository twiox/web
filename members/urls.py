from django.urls import path,include

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("events/<int:pk>/", views.EventDetailView.as_view(),name="event_detail"),
    path("events/new/", views.EventCreateView.as_view(),name="event_create"),
    path("events/<int:pk>/update/", views.EventUpdateView.as_view(),name="event_update"),
    path("events/<int:pk>/delete/", views.EventDeleteView.as_view(),name="event_delete"),
    path("events/<int:pk>/participate/", views.EventParticipateView.as_view(),name="event_participate"),
    path("events/<int:pk>/unparticipate/", views.EventUnParticipateView.as_view(),name="event_unparticipate"),
    path("sessions/<int:pk>/", views.SessionDetailView.as_view(),name="session_detail"),
    path("sessions/new/", views.SessionCreateView.as_view(),name="session_create"),
    path("sessions/<int:pk>/update/", views.SessionUpdateView.as_view(),name="session_update"),
    path("sessions/<int:pk>/delete/", views.SessionDeleteView.as_view(),name="session_delete"),
    path("spots/", views.SpotListView.as_view(),name="spot_list"),
    path("spots/<int:pk>/", views.SpotDetailView.as_view(),name="spot_detail"),
    path("spots/new/", views.SpotCreateView.as_view(),name="spot_create"),
    path("spots/<int:pk>/update/", views.SpotUpdateView.as_view(),name="spot_update"),
    path("spots/<int:pk>/delete/", views.SpotDeleteView.as_view(),name="spot_delete"),
    path("message/new/event/", views.MessageEveCreateView.as_view(),name="message_eve_create"),
    path("message/new/session/", views.MessageSessCreateView.as_view(),name="message_sess_create"),
    path("message/<int:pk>/delete/", views.MessageDeleteView.as_view(),name="message_delete"),
    path("message/<int:pk>/update/", views.MessageUpdateView.as_view(),name="message_update"),
    path("group/", views.GroupListView.as_view(),name="group_list"),
    path("group/new/", views.GroupCreateView.as_view(),name="group_create"),
    path("group/<int:pk>/update", views.GroupUpdateView.as_view(),name="group_update"),
    path("group/<int:pk>/delete/", views.GroupDeleteView.as_view(),name="group_delete"),
]

