from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # QR Code Management (Check-in only)
    path('qr/generate/', views.generate_qr_code, name='generate_qr_code'),
    path('qr/scan/', views.scan_qr_code, name='scan_qr_code'),
    
    # Attendance Management
    path('checkout/button/', views.checkout_button, name='checkout_button'),
    path('attendance/', views.get_attendance, name='get_attendance'),
    path('attendance/today/', views.get_today_attendance, name='get_today_attendance'),
    
    # Leave Management
    path('leave/apply/', views.apply_leave, name='apply_leave'),
    path('leave/applications/', views.get_leave_applications, name='get_leave_applications'),
    path('leave/update/<int:leave_id>/', views.update_leave_status, name='update_leave_status'),
    
    # Checkout Correction Requests
    path('checkout/correction/request/', views.request_checkout_correction, name='request_checkout_correction'),
    path('checkout/correction/requests/', views.get_checkout_requests, name='get_checkout_requests'),
    path('checkout/correction/update/<int:request_id>/', views.update_checkout_request, name='update_checkout_request'),
]
