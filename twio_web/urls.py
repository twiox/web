"""The site's sections; each app holds its own URLs."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("public.urls")),  # landing, Impressum, Datenschutz, /veranstalter/, /interessierte/
    path("", include("accounts.urls")),  # /vorstand/, /mitglieder/profil/, login, password reset
    path("mitglieder/", include("members.urls")),
    path("trainer/", include("trainer.urls")),
    path("session/", include("trainer.trainingsession")),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
