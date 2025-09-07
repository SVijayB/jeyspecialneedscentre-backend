from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import django
from django.db import connection


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
