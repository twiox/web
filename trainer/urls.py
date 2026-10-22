from django.urls import path
from . import views

urlpatterns = [
    path("", views.trainer_index, name="trainer_index"),
    path("daten", views.trainer_data, name="trainer_data"),
    path("probetraining", views.trainer_trials, name="trainer_trials"),
    path('update/', views.TrainerSelfUpdateView.as_view(),name="trainer_self_update_form"),
    path('mails/<int:sessionid>', views.get_session_emails, name='trainer_get_sessionemails'),
]

