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
    path('users/', user_views.MemberListView.as_view(), name="member_list"),
    path('users/<int:pk>/remove', user_views.UserDeleteView.as_view(), name="remove_user"),
    path('users/<int:pk>/update', user_views.ProfileUpdateView.as_view(), name="update_user"),
    path('register/', user_views.register, name="register"),
    path('register_trainer/', user_views.register_trainer, name="register_trainer"),
    path('trainer/',user_views.TrainerListView.as_view(), name="trainer_list"),
    path('trainer/<int:pk>/update', user_views.TrainerUpdateView.as_view(),name="trainer_update_form"),
    path('chairman/new/', user_views.ChairmanCreateView.as_view(), name="chairman_create"),
    path('chairman/', user_views.ChairmanListView.as_view(), name="chairman_list"),
    path('chairman/<int:pk>/remove/', user_views.ChairmanDeleteView.as_view(), name="chairman_delete"),
    path('chairman/<int:pk>/update/', user_views.ChairmanUpdateView.as_view(), name="chairman_update"),
    path('remove_trainer/', user_views.remove_trainer, name="remove_trainer"),
    path("login/", auth_views.LoginView.as_view(template_name="user_handling/login.html"), name="login"),
    path("logout/", user_views.LogoutView.as_view(template_name="user_handling/logout.html"), name="logout"),
    path("activate/<str:uidb64>/<str:token>/", user_views.activate, name="activate"),
    path("reset_pw/", user_views.PasswordResetView.as_view(template_name="user_handling/password_reset.html"), name="password_reset"),
    path("reset_pw/confirm/<str:uidb64>/<str:token>/", auth_views.PasswordResetConfirmView.as_view(template_name="user_handling/password_reset_confirm.html"), name="password_reset_confirm"),
    path("reset_pw/complete/",auth_views.PasswordResetCompleteView.as_view(template_name="user_handling/password_reset_complete.html"), name="password_reset_complete"),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
