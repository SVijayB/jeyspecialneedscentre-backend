"""
URL configuration for jeycentre project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

def root_view(request):
    """Root endpoint"""
    return JsonResponse({
        'message': 'Jey Special Needs Centre API',
        'version': '1.0.0',
        'docs': '/api/docs/',
        'schema': '/api/schema/',
        'health': '/health/'
    })

urlpatterns = [
    path('', root_view, name='root'),
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/', include('core.urls')),
    path('api/auth/', include('accounts.urls')),
    path('api/attendance/', include('attendance.urls')),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # Health checks
    path('health/', include('health_check.urls')),  # Django health check
]
