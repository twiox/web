from django.urls import path, include
from . import views

urlpatterns = [
    path("training/", include("members.tools.training")),
    path("veranstaltungen/", include("members.tools.events")),
    path("news/", include("members.tools.news")),
    path("editor/", include("members.tools.editor")),
    path("spots/", include("members.tools.spots")),
    path("modal", views.get_modal, name="get_modal"),
    # this is the old stuff...
    path("profil/", views.UserDetailView.as_view(), name="profile_detail"),
    path(
        "profil/ändere_email/",
        views.EmailUpdateView.as_view(),
        name="profile_update_email",
    ),
    path(
        "profil/ändere_nutzername/",
        views.UsernameUpdateView.as_view(),
        name="profile_update_username",
    ),
    path(
        "profil/ändere_daten/",
        views.AddressChangeView.as_view(),
        name="profile_update_address",
    ),
    path(
        "profil/ändere_passwort/",
        views.PasswordChangeView.as_view(),
        name="profile_update_pw",
    ),
    path("ajax/get/bilder_daten", views.get_image_data, name="get_image_data"),
    path("ajax/set/bilder_daten", views.set_image_data, name="set_image_data"),
    path("ajax/weitere_email/neu", views.add_another_email, name="add_another_email"),
    path(
        "ajax/weitere_email/löschen",
        views.delete_additional_email,
        name="delete_additional_email",
    ),
    path(
        "ajax/weitere_email/löschen/<int:pk>",
        views.delete_additional_email_chair,
        name="delete_additional_email_chair",
    ),
]
