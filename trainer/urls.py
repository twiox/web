from django.urls import path
from . import views
from user_handling import views as user_views

urlpatterns = [
    path("", views.trainer_index, name="trainer_index"),
    path("abrechnung", views.abrechnungstable, name="abrechnung"),
    path('alle',views.TrainerListView.as_view(), name="trainer_list"),
    path('entferne/', views.remove_trainer, name="remove_trainer"),
    path('ändere/<int:pk>', views.TrainerUpdateView.as_view(),name="trainer_update_form"),
    path('neu/', views.register_trainer, name="register_trainer"),
]

