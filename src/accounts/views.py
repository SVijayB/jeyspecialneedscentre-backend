from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from .models import CustomUser
from core.models import Branch
import json

User = get_user_model()


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login(request):
    """
    User login endpoint
    """
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return Response({
                'error': 'Username and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(username=username, password=password)
        
        if user and user.is_active and user.is_verified:
            token, created = Token.objects.get_or_create(user=user)
            
            return Response({
                'token': token.key,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'employee_id': user.employee_id,
                    'role': user.role,
                    'branch': user.branch.name if user.branch else None,
                    'mobile_number': user.mobile_number,
                    'login_time': user.login_time.strftime('%H:%M') if user.login_time else None,
                    'grace_time': user.grace_time,
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Invalid credentials or inactive account'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except json.JSONDecodeError:
        return Response({
            'error': 'Invalid JSON data'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    User logout endpoint
    """
    try:
        # Delete the user's token
        Token.objects.filter(user=request.user).delete()
        return Response({
            'message': 'Successfully logged out'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    """
    Get current user profile
    """
    try:
        user = request.user
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'employee_id': user.employee_id,
                'role': user.role,
                'branch': {
                    'id': user.branch.id,
                    'name': user.branch.name
                } if user.branch else None,
                'supervisor': {
                    'id': user.supervisor.id,
                    'name': f"{user.supervisor.first_name} {user.supervisor.last_name}",
                    'employee_id': user.supervisor.employee_id
                } if user.supervisor else None,
                'mobile_number': user.mobile_number,
                'login_time': user.login_time.strftime('%H:%M') if user.login_time else None,
                'grace_time': user.grace_time,
                'is_verified': user.is_verified,
                'date_joined': user.date_joined.isoformat(),
            }
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    Update user profile (limited fields)
    """
    try:
        data = json.loads(request.body)
        user = request.user
        
        # Only allow updating certain fields
        allowed_fields = ['first_name', 'last_name', 'email', 'mobile_number']
        
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
        
        user.save()
        
        return Response({
            'message': 'Profile updated successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'mobile_number': user.mobile_number,
            }
        }, status=status.HTTP_200_OK)
        
    except json.JSONDecodeError:
        return Response({
            'error': 'Invalid JSON data'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_users(request):
    """
    Get users based on role permissions
    """
    try:
        user = request.user
        
        if user.role == 'superadmin' or user.role == 'hr':
            # HR and superadmin can see all users
            users = User.objects.all().select_related('branch', 'supervisor')
        elif user.role == 'supervisor':
            # Supervisors can see users in their branch
            users = User.objects.filter(branch=user.branch).select_related('branch', 'supervisor')
        else:
            # Therapists can only see themselves
            users = User.objects.filter(id=user.id).select_related('branch', 'supervisor')
        
        users_data = []
        for u in users:
            users_data.append({
                'id': u.id,
                'username': u.username,
                'employee_id': u.employee_id,
                'first_name': u.first_name,
                'last_name': u.last_name,
                'email': u.email,
                'role': u.role,
                'branch': u.branch.name if u.branch else None,
                'supervisor': f"{u.supervisor.first_name} {u.supervisor.last_name}" if u.supervisor else None,
                'mobile_number': u.mobile_number,
                'is_active': u.is_active,
                'is_verified': u.is_verified,
                'login_time': u.login_time.strftime('%H:%M') if u.login_time else None,
                'grace_time': u.grace_time,
            })
        
        return Response({
            'users': users_data,
            'count': len(users_data)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_branches(request):
    """
    Get all branches
    """
    try:
        branches = Branch.objects.filter(is_active=True)
        branches_data = []
        
        for branch in branches:
            branches_data.append({
                'id': branch.id,
                'name': branch.name,
                'is_active': branch.is_active,
                'active_users_count': branch.active_users_count,
                'therapists_count': branch.therapists_count,
                'created_at': branch.created_at.isoformat(),
            })
        
        return Response({
            'branches': branches_data,
            'count': len(branches_data)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
