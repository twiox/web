from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.index, name="chairman_index"), 
    path('nutzer/', views.MemberListView.as_view(), name="member_list"),
    path('nutzer/<int:pk>/entfernen', views.UserDeleteView.as_view(), name="remove_user"),
    path('nutzer/<int:pk>/ändern', views.member_update, name="update_user"),
    path('nutzer/neu/', views.register, name="register"),
    path('vorstände/', views.ChairmanListView.as_view(), name="chairman_list"),
    path('vorstände/neu/', views.ChairmanCreateView.as_view(), name="chairman_create"),
    path('vorstände/<int:pk>/entfernen/', views.ChairmanDeleteView.as_view(), name="chairman_delete"),
    path('vorstände/<int:pk>/ändern/', views.ChairmanUpdateView.as_view(), name="chairman_update"),
]
