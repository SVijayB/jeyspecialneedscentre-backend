from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # System endpoints
    path('health/', views.health_check, name='health_check'),
    path('info/', views.api_info, name='api_info'),
    
    # Dashboard and reports
    path('dashboard/', views.dashboard_stats, name='dashboard_stats'),
    path('reports/attendance/', views.attendance_report, name='attendance_report'),
]
