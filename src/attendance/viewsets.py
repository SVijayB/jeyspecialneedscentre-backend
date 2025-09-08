"""
DRF ViewSets for Attendance management
Complete replacement for function-based views
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, time, date
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import AttendanceLog, LeaveApplication, CheckoutRequest
from .serializers import (
    AttendanceLogSerializer,
    AttendanceCreateSerializer,
    LeaveApplicationSerializer,
    LeaveApplicationCreateSerializer,
    CheckoutRequestSerializer,
    CheckoutRequestCreateSerializer
)
from accounts.permissions import BranchBasedPermission, IsSuperAdminOrHR
# from core.services import AttendanceAnalyticsService  # Comment out for now to avoid circular imports

User = get_user_model()


class AttendanceLogViewSet(viewsets.ModelViewSet):
    """
    Complete CRUD operations for attendance logs
    """
    permission_classes = [IsAuthenticated, BranchBasedPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'checkin_status', 'date', 'employee__branch']
    search_fields = ['employee__employee_id', 'employee__first_name', 'employee__last_name']
    ordering_fields = ['date', 'check_in_time', 'check_out_time']
    ordering = ['-date', 'employee__employee_id']
    
    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user
        
        queryset = AttendanceLog.objects.select_related(
            'employee', 'employee__branch'
        ).prefetch_related('checkout_requests')
        
        if user.role == 'superadmin':
            return queryset
        elif user.role == 'hr':
            return queryset.filter(employee__branch=user.branch)
        elif user.role == 'supervisor':
            return queryset.filter(employee__branch=user.branch)
        else:  # therapist
            return queryset.filter(employee=user)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return AttendanceCreateSerializer
        return AttendanceLogSerializer
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update']:
            permission_classes = [IsSuperAdminOrHR]
        elif self.action == 'destroy':
            permission_classes = [IsAuthenticated]  # Only superadmin (handled in destroy method)
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def destroy(self, request, *args, **kwargs):
        """Only superadmin can delete attendance records"""
        if request.user.role != 'superadmin':
            return Response(
                {'error': 'Only superadmin can delete attendance records'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's attendance for current user"""
        today = timezone.now().date()
        
        try:
            attendance = self.get_queryset().get(employee=request.user, date=today)
            serializer = self.get_serializer(attendance)
            return Response(serializer.data)
        except AttendanceLog.DoesNotExist:
            return Response(
                {'message': 'No attendance record for today'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def checkout(self, request):
        """Manual checkout functionality"""
        user = request.user
        current_time = timezone.now()
        today = current_time.date()
        
        # Check if it's past 6 PM
        if current_time.time() > time(18, 0):
            return Response({
                'error': 'Cannot checkout after 6 PM. Please submit a checkout correction request.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            attendance_log = AttendanceLog.objects.filter(
                employee=user,
                date=today,
                check_in_time__isnull=False,
                check_out_time__isnull=True
            ).latest('check_in_time')
        except AttendanceLog.DoesNotExist:
            return Response({
                'error': 'No active check-in record found for today.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Process checkout
        attendance_log.check_out_time = current_time
        attendance_log.save()
        
        serializer = self.get_serializer(attendance_log)
        return Response({
            'message': f'Successfully checked out at {current_time.strftime("%H:%M")}',
            'attendance': serializer.data
        })


class LeaveApplicationViewSet(viewsets.ModelViewSet):
    """
    Complete CRUD operations for leave applications
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'leave_type', 'employee__branch']
    search_fields = ['employee__employee_id', 'employee__first_name', 'employee__last_name', 'reason']
    ordering_fields = ['applied_at', 'start_date', 'end_date']
    ordering = ['-applied_at']
    
    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user
        
        queryset = LeaveApplication.objects.select_related(
            'employee', 'employee__branch', 'approved_by'
        )
        
        if user.role == 'superadmin':
            return queryset
        elif user.role in ['hr', 'supervisor']:
            return queryset.filter(employee__branch=user.branch)
        else:  # therapist
            return queryset.filter(employee=user)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return LeaveApplicationCreateSerializer
        return LeaveApplicationSerializer
    
    def get_permissions(self):
        """Set permissions based on action and user role"""
        if self.action == 'destroy':
            # Special handling for delete permissions
            permission_classes = [IsAuthenticated]
        elif self.action in ['update', 'partial_update']:
            # Special handling for update permissions
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def update(self, request, *args, **kwargs):
        """Handle leave application updates based on user role"""
        instance = self.get_object()
        user = request.user
        
        # Only allow editing pending applications
        if instance.status != 'pending':
            return Response(
                {'error': 'Can only edit pending leave applications'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check permissions
        if user.role == 'therapist' and instance.employee != user:
            return Response(
                {'error': 'You can only edit your own leave applications'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        elif user.role in ['supervisor', 'hr'] and instance.employee.branch != user.branch:
            return Response(
                {'error': 'You can only edit applications from your branch'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Handle leave application deletion based on user role"""
        instance = self.get_object()
        user = request.user
        
        # Check permissions
        if user.role == 'therapist':
            if instance.employee != user or instance.status != 'pending':
                return Response(
                    {'error': 'You can only delete your own pending leave applications'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        elif user.role in ['supervisor', 'hr']:
            if instance.employee.branch != user.branch:
                return Response(
                    {'error': 'You can only delete applications from your branch'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a leave application"""
        if request.user.role not in ['supervisor', 'hr', 'superadmin']:
            return Response(
                {'error': 'Only supervisors, HR, or superadmin can approve leaves'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        instance = self.get_object()
        
        if instance.status != 'pending':
            return Response(
                {'error': 'Can only approve pending applications'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        instance.status = 'approved'
        instance.approved_by = request.user
        instance.approved_at = timezone.now()
        instance.save()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a leave application"""
        if request.user.role not in ['supervisor', 'hr', 'superadmin']:
            return Response(
                {'error': 'Only supervisors, HR, or superadmin can reject leaves'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        instance = self.get_object()
        
        if instance.status != 'pending':
            return Response(
                {'error': 'Can only reject pending applications'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        instance.status = 'rejected'
        instance.approved_by = request.user
        instance.approved_at = timezone.now()
        instance.save()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class CheckoutRequestViewSet(viewsets.ModelViewSet):
    """
    Complete CRUD operations for checkout requests
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'therapist__branch']
    search_fields = ['therapist__employee_id', 'therapist__first_name', 'therapist__last_name', 'reason']
    ordering_fields = ['created_at', 'processed_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user
        
        queryset = CheckoutRequest.objects.select_related(
            'therapist', 'therapist__branch', 'supervisor', 'attendance_log'
        )
        
        if user.role == 'superadmin':
            return queryset
        elif user.role in ['hr', 'supervisor']:
            return queryset.filter(therapist__branch=user.branch)
        else:  # therapist
            return queryset.filter(therapist=user)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return CheckoutRequestCreateSerializer
        return CheckoutRequestSerializer
    
    def perform_create(self, serializer):
        """Set therapist and supervisor when creating request"""
        serializer.save(
            therapist=self.request.user,
            supervisor=self.request.user.supervisor
        )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a checkout request"""
        if request.user.role not in ['supervisor', 'hr', 'superadmin']:
            return Response(
                {'error': 'Only supervisors, HR, or superadmin can approve requests'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        instance = self.get_object()
        
        if instance.status != 'pending':
            return Response(
                {'error': 'Can only approve pending requests'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update the checkout request
        instance.status = 'approved'
        instance.processed_at = timezone.now()
        instance.supervisor_notes = request.data.get('notes', '')
        
        # Update the attendance log
        checkout_time = datetime.combine(
            instance.attendance_log.date,
            instance.requested_checkout_time
        )
        instance.attendance_log.check_out_time = checkout_time
        instance.attendance_log.save()
        
        instance.save()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a checkout request"""
        if request.user.role not in ['supervisor', 'hr', 'superadmin']:
            return Response(
                {'error': 'Only supervisors, HR, or superadmin can reject requests'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        instance = self.get_object()
        
        if instance.status != 'pending':
            return Response(
                {'error': 'Can only reject pending requests'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        instance.status = 'rejected'
        instance.processed_at = timezone.now()
        instance.supervisor_notes = request.data.get('notes', '')
        instance.save()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
