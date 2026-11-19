from django.contrib.auth import views as auth_views
from django.urls import include, path
from . import views
from .forms import LoginForm
from trainer import views as trainer_views
from members import views as member_views
from public import views as public_views

# the board pages, under /vorstand/
board_urlpatterns = [
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
    path("verwaltung/probetraining/", public_views.TesterIndexView.as_view(), name="tester_index"),
    path("verwaltung/probetraining/liste/", public_views.TesterListView.as_view(), name="tester_list"),
    path("verwaltung/probetraining/neu/", public_views.TesterCreateView.as_view(), name="tester_create"),
    path("verwaltung/probetraining/<int:pk>/bearbeiten/", public_views.TesterUpdateView.as_view(), name="tester_update"),
    path("verwaltung/probetraining/<int:pk>/loeschen/", public_views.TesterDeleteView.as_view(), name="tester_delete"),
    path("verwaltung/probetraining/<int:pk>/einverstaendnis/", public_views.tester_consent, name="tester_consent"),
    path("verwaltung/probetraining/<int:pk>/einverstaendnis/hochladen/", public_views.tester_consent_upload, name="tester_consent_upload"),
    path("verwaltung/probetraining/<int:pk>/ergebnis/", public_views.tester_outcome, name="tester_outcome"),
    path("verwaltung/probetraining/<int:pk>/antrag/", public_views.tester_application, name="tester_application"),
    path("verwaltung/probetraining/<int:pk>/gruppe/", public_views.tester_set_group, name="tester_set_group"),
    path("verwaltung/probetraining/<int:pk>/notiz/", public_views.tester_note, name="tester_note"),
    path("verwaltung/probetraining/gruppen/neu/", public_views.TrialGroupCreateView.as_view(), name="trial_group_create"),
    path("verwaltung/probetraining/gruppen/<int:pk>/", public_views.TrialGroupDetailView.as_view(), name="trial_group_detail"),
    path("verwaltung/probetraining/gruppen/<int:pk>/bearbeiten/", public_views.TrialGroupUpdateView.as_view(), name="trial_group_update"),
    path("verwaltung/probetraining/gruppen/<int:pk>/loeschen/", public_views.TrialGroupDeleteView.as_view(), name="trial_group_delete"),
    path("verwaltung/probetraining/gruppen/<int:pk>/archivieren/", public_views.trial_group_archive, name="trial_group_archive"),
    path("verwaltung/events/", member_views.EventListView.as_view(),name="event_list"),
    path("verwaltung/mailing-lists/", views.mailing_lists,name="mailing_lists"),
    path("ajax/kopiere-email-listen", views.get_all_emails, name="get_all_emails"),
    path('ajax/kopiere-participant-listen',views.get_participants_emails, name='get_participants_emails'),
    path("ajax/mitglieder/detail_form/<int:pk>", views.member_detail_form,name="get_member_detail_form"),
    path("ajax/mitglieder/detail_form/<int:pk>/update", views.member_detail_update,name="member_detail_form_update"),
    path("ajax/mitglieder/<int:pk>/aktivieren", views.member_activate, name="member_activate"),
    path("ajax/mitglieder/<int:pk>/weitere_email/löschen", views.delete_additional_email_chair, name="delete_additional_email_chair"),
    path("ajax/mitglieder/<int:pk>/rolle/<str:role>", views.member_role, name="member_role"),
]

# included at the site root (twio_web/urls.py)
urlpatterns = [
    path("vorstand/", include(board_urlpatterns)),
    path("mitglieder/profil/", include("accounts.profile")),
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html", authentication_form=LoginForm), name="login"),
    path("logout/", views.TwioLogoutView.as_view(), name="logout"),
    path("passwort_zurücksetzen/", views.TwioPasswordResetView.as_view(template_name="accounts/password_reset.html"), name="password_reset"),
    path("passwort_zurücksetzen/bestätigen/<str:uidb64>/<str:token>/",
         views.TwioPasswordResetConfirmView.as_view(template_name="accounts/password_reset_confirm.html"), name="password_reset_confirm"),
]
