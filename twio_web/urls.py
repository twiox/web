"""twio_web URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static
from user_handling import views as user_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("members/", include('members.urls')),
    path("shop/", include('shop.urls')),
    path('register/', user_views.register, name="register"),
    path('remove/', user_views.remove_user, name="remove"),
    path('change_group/', user_views.change_group, name="change_group"),
    path('remove/user/<int:pk>/', user_views.UserDeleteView.as_view(), name="remove_user"),
    path('register_trainer/', user_views.register_trainer, name="register_trainer"),
    path('remove_trainer/', user_views.remove_trainer, name="remove_trainer"),
    path("login/", user_views.LoginView.as_view(template_name="user_handling/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(template_name="user_handling/logout.html"), name="logout"),
    path("activate/<str:uidb64>/<str:token>/", user_views.activate, name="activate"),
    path("reset_pw/", auth_views.PasswordResetView.as_view(template_name="user_handling/password_reset.html"), name="password_reset"),
    path("reset_pw_done/", auth_views.PasswordResetDoneView.as_view(template_name="user_handling/password_reset_done.html"), name="password_reset_done"),
    path("reset_pw/confirm/<str:uidb64>/<str:token>/", auth_views.PasswordResetConfirmView.as_view(template_name="user_handling/password_reset_confirm.html"), name="password_reset_confirm"),
    path("reset_pw/complete/",auth_views.PasswordResetCompleteView.as_view(template_name="user_handling/password_reset_complete.html"), name="password_reset_complete"),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
