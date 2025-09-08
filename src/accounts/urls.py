from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .viewsets import UserViewSet, BranchViewSet

app_name = 'accounts'

# DRF Router for ViewSets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'branches', BranchViewSet, basename='branch')

urlpatterns = [
    # DRF ViewSet routes
    path('', include(router.urls)),
    
    # Authentication endpoints
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
]
