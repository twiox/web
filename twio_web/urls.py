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
    path("session/", include('trainer.trainingsession')),
    path("vorstand/", include('user_handling.urls')),
    path("login/", auth_views.LoginView.as_view(template_name="user_handling/login.html"), name="login"),
    path("logout/", user_views.LogoutView.as_view(template_name="user_handling/logout.html"), name="logout"),
    path("aktiviere/<str:uidb64>/<str:token>/", user_views.activate, name="activate"),
    path("aktiviere/<str:uidb64>/<str:token>/neu", user_views.resend_activate, name="resend_activate"),
    path("passwort_zurücksetzen/", user_views.PasswordResetView.as_view(template_name="user_handling/password_reset.html"), name="password_reset"),
    path("passwort_zurücksetzen/bestätigen/<str:uidb64>/<str:token>/", user_views.PasswordResetConfirmView.as_view(template_name="user_handling/password_reset_confirm.html"), name="password_reset_confirm"),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
