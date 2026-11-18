from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path("", views.trainer_index, name="trainer_index"),
    path("gruppen", views.trainer_groups, name="trainer_groups"),
    path("gruppen/<int:pk>", views.trainer_group_detail, name="trainer_group_detail"),
    path("gruppen/<int:pk>/entfernen/<int:profile_pk>", views.trainer_group_remove, name="trainer_group_remove"),
    path("daten", views.trainer_data, name="trainer_data"),
    # was its own tab, now a section on the groups page
    path("probetraining", RedirectView.as_view(url="/trainer/gruppen#probetraining", permanent=True)),
    path('update/', views.TrainerSelfUpdateView.as_view(),name="trainer_self_update_form"),
]

