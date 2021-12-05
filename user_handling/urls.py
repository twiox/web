from django.contrib import admin
from django.urls import path, include
from . import views
from trainer import views as trainer_views
from members import views as member_views

urlpatterns = [
    path("", views.index, name="chairman_index"), 
    path('mitglieder/', views.MemberListView.as_view(), name="member_list"),
    path('mitglieder/<int:pk>/entfernen', views.UserDeleteView.as_view(), name="remove_user"),
    path('mitglieder/<int:pk>/ändern', views.member_update, name="update_user"),
    path('mitglieder/neu/', views.register, name="register"),
    path('liste/', views.ChairmanListView.as_view(), name="chairman_list"),
    path('liste/neu/', views.ChairmanCreateView.as_view(), name="chairman_create"),
    path('liste/<int:pk>/entfernen/', views.ChairmanDeleteView.as_view(), name="chairman_delete"),
    path('liste/<int:pk>/ändern/', views.ChairmanUpdateView.as_view(), name="chairman_update"),
    path('trainer/',trainer_views.TrainerListView.as_view(), name="trainer_list"),
    path('trainer/entferne/', trainer_views.remove_trainer, name="remove_trainer"),
    path('trainer/ändere/<int:pk>', trainer_views.TrainerUpdateView.as_view(),name="trainer_update_form"),
    path('trainer/neu/', trainer_views.register_trainer, name="register_trainer"),
    path("verwaltung/gruppen/", member_views.GroupListView.as_view(),name="group_list"),
    path("verwaltung/events/", member_views.EventListView.as_view(),name="event_list"),
    path("verwaltung/mailing-lists/", views.mailing_lists,name="mailing_lists"),
    path("ajax/kopiere-email-listen", views.get_all_emails, name="get_all_emails"),
    path("ajax/mitglieder/detail_form/<int:pk>", views.member_detail_form,name="get_member_detail_form"),
    path("ajax/mitglieder/detail_form/<int:pk>/update", views.member_detail_update,name="member_detail_form_update"),
    
]
