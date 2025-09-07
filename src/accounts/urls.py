from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    
    # User Profile
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    
    # User Management
    path('users/', views.get_users, name='get_users'),
    path('branches/', views.get_branches, name='get_branches'),
]
