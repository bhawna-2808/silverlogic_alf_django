from django.urls import path, include
from . import views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path("logout/", views.user_logout, name="logout"),
    path("user_list/", views.user_list, name="user_list"),
    path("delete_user/<int:id>/", views.delete_user, name="delete_user"),
    path("edit_user/<int:id>/", views.edit_user, name="edit_user"),
    
    

]