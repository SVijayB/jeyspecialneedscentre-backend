"""
Basic attendance management views (check-in, checkout, attendance records)
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, date, time, timedelta
from decimal import Decimal
import json
from ..models import AttendanceLog

User = get_user_model()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def checkout_button(request):
    """
    Simple button-based checkout (no QR scanning required)
    """
    try:
        user = request.user
        current_time = timezone.now()
        today = current_time.date()
        
        # Check if it's past 6 PM (18:00) - cannot checkout after 6 PM same day
        if current_time.time() > time(18, 0):
            return Response({
                'error': 'Cannot checkout after 6 PM. Please submit a checkout correction request.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get today's LATEST attendance log that hasn't been checked out yet
        try:
            attendance_log = AttendanceLog.objects.filter(
                employee=user,
                date=today,
                check_in_time__isnull=False,
                check_out_time__isnull=True
            ).latest('check_in_time')
            
        except AttendanceLog.DoesNotExist:
            return Response({
                'error': 'No active check-in record found for today. Please check-in first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if already checked out (this should not happen with our filter above, but just in case)
        if attendance_log.check_out_time is not None:
            return Response({
                'error': 'No active check-in found to checkout.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Process checkout
        attendance_log.check_out_time = current_time
        attendance_log.needs_checkout_correction = False
        
        # Calculate total hours
        duration = current_time - attendance_log.check_in_time
        attendance_log.total_hours = Decimal(str(round(duration.total_seconds() / 3600, 2)))
        
        attendance_log.save()
        
        return Response({
            'message': f'Successfully checked out at {current_time.strftime("%H:%M")}',
            'attendance': {
                'id': attendance_log.id,
                'date': attendance_log.date.isoformat(),
                'check_in_time': attendance_log.check_in_time.isoformat(),
                'check_out_time': attendance_log.check_out_time.isoformat(),
                'status': attendance_log.status,
                'checkin_status': attendance_log.checkin_status,
                'total_hours': str(attendance_log.total_hours),
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_attendance(request):
    """
    Get attendance records based on user role and filters
    """
    try:
        user = request.user
        
        # Get query parameters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        employee_id = request.GET.get('employee_id')
        branch_id = request.GET.get('branch_id')
        status_filter = request.GET.get('status')
        
        # Base queryset based on user role
        if user.role == 'therapist':
            queryset = AttendanceLog.objects.filter(employee=user)
        elif user.role == 'supervisor':
            queryset = AttendanceLog.objects.filter(employee__branch=user.branch)
        elif user.role in ['hr', 'superadmin']:
            queryset = AttendanceLog.objects.all()
        else:
            return Response({
                'error': 'Insufficient permissions'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Apply filters
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__gte=start_date)
            except ValueError:
                return Response({
                    'error': 'Invalid start_date format. Use YYYY-MM-DD'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__lte=end_date)
            except ValueError:
                return Response({
                    'error': 'Invalid end_date format. Use YYYY-MM-DD'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        if employee_id and user.role in ['supervisor', 'hr', 'superadmin']:
            queryset = queryset.filter(employee__employee_id=employee_id)
        
        if branch_id and user.role in ['hr', 'superadmin']:
            queryset = queryset.filter(employee__branch_id=branch_id)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Order by date (latest first)
        queryset = queryset.order_by('-date')
        
        # Serialize data
        attendance_data = []
        for log in queryset:
            attendance_data.append({
                'id': log.id,
                'employee': {
                    'id': log.employee.id,
                    'name': f"{log.employee.first_name} {log.employee.last_name}",
                    'employee_id': log.employee.employee_id,
                    'branch': log.employee.branch.name if log.employee.branch else None,
                },
                'date': log.date.isoformat(),
                'check_in_time': log.check_in_time.isoformat() if log.check_in_time else None,
                'check_out_time': log.check_out_time.isoformat() if log.check_out_time else None,
                'status': log.status,
                'checkin_status': log.checkin_status,
                'total_hours': str(log.total_hours),
                'needs_checkout_correction': log.needs_checkout_correction,
            })
        
        return Response({
            'attendance_records': attendance_data,
            'total_records': len(attendance_data)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_today_attendance(request):
    """
    Get today's attendance for the current user
    """
    try:
        user = request.user
        today = timezone.now().date()
        
        try:
            attendance = AttendanceLog.objects.get(employee=user, date=today)
            return Response({
                'attendance': {
                    'id': attendance.id,
                    'date': attendance.date.isoformat(),
                    'check_in_time': attendance.check_in_time.isoformat() if attendance.check_in_time else None,
                    'check_out_time': attendance.check_out_time.isoformat() if attendance.check_out_time else None,
                    'status': attendance.status,
                    'checkin_status': attendance.checkin_status,
                    'total_hours': str(attendance.total_hours),
                    'needs_checkout_correction': attendance.needs_checkout_correction,
                }
            }, status=status.HTTP_200_OK)
            
        except AttendanceLog.DoesNotExist:
            return Response({
                'attendance': None,
                'message': 'No attendance record for today'
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
