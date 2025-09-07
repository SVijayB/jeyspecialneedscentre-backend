from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Avg, Sum, Case, When, IntegerField
from django.utils import timezone
from datetime import datetime, date, timedelta
import django
from django.db import connection
import json

from .models import Branch
from attendance.models import AttendanceLog, LeaveApplication, CheckoutRequest
from .services import AttendanceAnalyticsService

User = get_user_model()


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint to verify system status
    """
    try:
        # Test database connection
        connection.ensure_connection()
        
        health_status = {
            'status': 'healthy',
            'timestamp': django.utils.timezone.now().isoformat(),
            'django_version': django.get_version(),
            'debug_mode': settings.DEBUG,
            'database': 'connected',
            'environment': getattr(settings, 'DJANGO_ENVIRONMENT', 'unknown')
        }
        
        return Response(health_status, status=status.HTTP_200_OK)
        
    except Exception as e:
        health_status = {
            'status': 'unhealthy',
            'timestamp': django.utils.timezone.now().isoformat(),
            'error': str(e),
            'django_version': django.get_version(),
        }
        
        return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
@permission_classes([AllowAny])
def api_info(request):
    """
    Basic API information endpoint
    """
    api_info = {
        'name': 'Jey Special Needs Centre API',
        'version': '1.0.0',
        'description': 'Backend API for attendance and user management',
        'endpoints': {
            'health': '/api/health/',
            'info': '/api/info/',
            'auth': '/api/auth/',
            'users': '/api/users/',
            'attendance': '/api/attendance/',
        },
        'user_roles': [
            'Therapist',
            'Supervisor', 
            'HR',
            'Super Admin'
        ]
    }
    
    return Response(api_info, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    Get dashboard statistics based on user role
    """
    try:
        user = request.user
        today = timezone.now().date()
        
        stats = AttendanceAnalyticsService.get_dashboard_stats_optimized(user, today)
        
        return Response(stats, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def attendance_report(request):
    """
    Get attendance report for a date range
    """
    try:
        user = request.user
        
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        branch_id = request.GET.get('branch_id')
        employee_id = request.GET.get('employee_id')
        
        if not start_date or not end_date:
            today = date.today()
            start_date = today.replace(day=1)
            end_date = today
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        report_data = AttendanceAnalyticsService.get_attendance_report_optimized(
            user=user,
            start_date=start_date,
            end_date=end_date,
            branch_id=int(branch_id) if branch_id else None,
            employee_id=employee_id
        )
        
        if 'error' in report_data:
            return Response(report_data, status=status.HTTP_403_FORBIDDEN)
        
        return Response(report_data, status=status.HTTP_200_OK)
        
    except ValueError:
        return Response({
            'error': 'Invalid date format. Use YYYY-MM-DD'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
