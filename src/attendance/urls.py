from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .viewsets import AttendanceLogViewSet, LeaveApplicationViewSet, CheckoutRequestViewSet

app_name = 'attendance'

# DRF Router for ViewSets
router = DefaultRouter()
router.register(r'attendance', AttendanceLogViewSet, basename='attendance')
router.register(r'leaves', LeaveApplicationViewSet, basename='leave')
router.register(r'checkout-requests', CheckoutRequestViewSet, basename='checkout-request')

urlpatterns = [
    # DRF ViewSet routes
    path('', include(router.urls)),
    
    # QR Code Management
    path('qr/generate/', views.generate_qr_code, name='generate_qr_code'),
    path('qr/scan/', views.scan_qr_code, name='scan_qr_code'),
]
