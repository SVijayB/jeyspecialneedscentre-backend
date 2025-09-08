"""
DRF ViewSets for User and Branch management
Complete replacement for function-based views
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.contrib.auth import get_user_model
from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view

from core.models import Branch
from .serializers import (
    UserListSerializer, 
    UserDetailSerializer, 
    UserCreateSerializer,
    BranchSerializer
)
from .permissions import (
    IsSuperAdminOrHR, 
    IsSuperAdminOnly, 
    IsOwnerOrSuperAdminOrHR
)

User = get_user_model()


class BranchViewSet(viewsets.ModelViewSet):
    """
    Complete CRUD operations for branches
    Only superadmin can create/update/delete
    """
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsSuperAdminOnly]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]


class UserViewSet(viewsets.ModelViewSet):
    """
    Complete CRUD operations for users
    Role-based access control applied
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['role', 'branch', 'is_verified']
    search_fields = ['employee_id', 'username', 'first_name', 'last_name', 'email']
    ordering_fields = ['employee_id', 'first_name', 'last_name', 'created_at']
    ordering = ['employee_id']
    
    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user
        
        if user.role == 'superadmin':
            return User.objects.select_related('branch', 'supervisor').all()
        elif user.role == 'hr':
            return User.objects.select_related('branch', 'supervisor').filter(
                branch=user.branch
            )
        else:
            # Supervisors and therapists can only see themselves
            return User.objects.filter(id=user.id)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return UserDetailSerializer
        else:
            return UserListSerializer
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'destroy']:
            permission_classes = [IsSuperAdminOrHR]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [IsOwnerOrSuperAdminOrHR]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """Create user with proper branch assignment for HR users"""
        user = self.request.user
        if user.role == 'hr':
            # HR can only create users in their own branch
            serializer.save(branch=user.branch)
        else:
            serializer.save()
    
    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """Reset user password"""
        if request.user.role not in ['superadmin', 'hr']:
            return Response(
                {'error': 'Only superadmin or HR can reset passwords'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.get_object()
        new_password = request.data.get('new_password')
        
        if not new_password or len(new_password) < 8:
            return Response(
                {'error': 'Password must be at least 8 characters'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()
        
        return Response({'message': 'Password reset successfully'})
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """Update current user profile"""
        serializer = self.get_serializer(
            request.user, 
            data=request.data, 
            partial=request.method == 'PATCH'
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
