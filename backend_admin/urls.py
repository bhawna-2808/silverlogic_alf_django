from django.urls import path, include
from . import views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path("logout/", views.user_logout, name="logout"),

]