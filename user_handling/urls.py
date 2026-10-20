from django.urls import path
from . import views
from trainer import views as trainer_views
from members import views as member_views
from interested import views as interested_views

urlpatterns = [
    path("", views.index, name="chairman_index"),
    path('mitglieder/', views.MemberListView.as_view(), name="member_list"),
    path('mitglieder/<int:pk>/entfernen', views.UserDeleteView.as_view(), name="remove_user"),
    path('mitglieder/neu/', views.register, name="register"),
    path('liste/', views.ChairmanListView.as_view(), name="chairman_list"),
    path('liste/<int:pk>/entfernen/', views.ChairmanDeleteView.as_view(), name="chairman_delete"),
    path('liste/<int:pk>/ändern/', views.ChairmanUpdateView.as_view(), name="chairman_update"),
    path('trainer/',trainer_views.TrainerListView.as_view(), name="trainer_list"),
    path('trainer/ändere/<int:pk>', trainer_views.TrainerUpdateView.as_view(),name="trainer_update_form"),
    path('trainer/<int:pk>/entfernen/', trainer_views.TrainerDeleteView.as_view(), name="trainer_delete"),
    path("verwaltung/probetraining/", interested_views.TesterListView.as_view(),name="tester_list"),
    path("verwaltung/events/", member_views.EventListView.as_view(),name="event_list"),
    path("verwaltung/mailing-lists/", views.mailing_lists,name="mailing_lists"),
    path("ajax/kopiere-email-listen", views.get_all_emails, name="get_all_emails"),
    path('ajax/kopiere-participant-listen',views.get_participants_emails, name='get_participants_emails'),
    path("ajax/mitglieder/detail_form/<int:pk>", views.member_detail_form,name="get_member_detail_form"),
    path("ajax/mitglieder/detail_form/<int:pk>/update", views.member_detail_update,name="member_detail_form_update"),
    path("ajax/mitglieder/<int:pk>/aktivieren", views.member_activate, name="member_activate"),
    path("ajax/mitglieder/<int:pk>/rolle/<str:role>", views.member_role, name="member_role"),
]
