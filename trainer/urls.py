from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path("", views.trainer_index, name="trainer_index"),
    path("gruppen", views.trainer_groups, name="trainer_groups"),
    path("daten", views.trainer_data, name="trainer_data"),
    # was its own tab, now a section on the groups page
    path("probetraining", RedirectView.as_view(url="/trainer/gruppen#probetraining", permanent=True)),
    path('update/', views.TrainerSelfUpdateView.as_view(),name="trainer_self_update_form"),
    path('mails/<int:sessionid>', views.get_session_emails, name='trainer_get_sessionemails'),
]

