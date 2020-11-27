from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static
from user_handling import views as user_views
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.landingPage, name="landing"),
    path('impressum', views.impressumPage, name="impressum"),
    path('datenschutzerklärung', views.dataProtectionPage, name="dataprotection"),
    path("mitglieder/", include('members.urls')),
    path("interessierte/", include('interested.urls')),
    path('veranstalter/', include('organizers.urls')),
    path("trainer/", include('trainer.urls')),
    path('nutzer/', user_views.MemberListView.as_view(), name="member_list"),
    path('nutzer/<int:pk>/entfernen', user_views.UserDeleteView.as_view(), name="remove_user"),
    path('nutzer/<int:pk>/ändern', user_views.member_update, name="update_user"),
    path('nutzer/hinzufügen/', user_views.register, name="register"),
    path('vorstände/neu/', user_views.ChairmanCreateView.as_view(), name="chairman_create"),
    path('vorstände/', user_views.ChairmanListView.as_view(), name="chairman_list"),
    path('vorstände/<int:pk>/entfernen/', user_views.ChairmanDeleteView.as_view(), name="chairman_delete"),
    path('vorstände/<int:pk>/ändern/', user_views.ChairmanUpdateView.as_view(), name="chairman_update"),
    path("login/", auth_views.LoginView.as_view(template_name="user_handling/login.html"), name="login"),
    path("logout/", user_views.LogoutView.as_view(template_name="user_handling/logout.html"), name="logout"),
    path("aktiviere/<str:uidb64>/<str:token>/", user_views.activate, name="activate"),
    path("aktiviere/<str:uidb64>/<str:token>/neu", user_views.resend_activate, name="resend_activate"),
    path("passwort_zurücksetzen/", user_views.PasswordResetView.as_view(template_name="user_handling/password_reset.html"), name="password_reset"),
    path("passwort_zurücksetzen/bestätigen/<str:uidb64>/<str:token>/", user_views.PasswordResetConfirmView.as_view(template_name="user_handling/password_reset_confirm.html"), name="password_reset_confirm"),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
