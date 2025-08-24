from django.urls import path
from . import views
from user_handling import views as user_views

urlpatterns = [
    path("", views.trainer_index, name="trainer_index"),
    path("abrechnung", views.abrechnungstable, name="abrechnung"),
    path("abrechnung/<int:pk>", views.AbrechnungstableDetailView.as_view(), name="abrechnung_detail"),
    path("abrechnung/ajax/add_week/", views.add_week, name='add_week'),
    path("abrechnung/ajax/reset/", views.reset_table, name='reset_table'),
    path("abrechnung/ajax/save_entries/", views.save_entries, name='save_entries'),
    path("abrechnung/ajax/delete_row/", views.delete_row, name='delete_row'),
    path("abrechnung/ajax/add_row/", views.add_row, name='add_row'),
    path("abrechnung/ajax/send_table/", views.send_table, name='send_table'),
    path('update/', views.TrainerSelfUpdateView.as_view(),name="trainer_self_update_form"),
    path('mails/<int:sessionid>', views.get_session_emails, name='trainer_get_sessionemails'),
]

