"""
Leave management views
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import datetime, date
import json
from ..models import LeaveApplication
from core.services import LeaveQueryService

User = get_user_model()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_leave(request):
    """
    Apply for leave
    """
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['leave_type', 'start_date', 'end_date', 'reason']
        for field in required_fields:
            if field not in data:
                return Response({
                    'error': f'{field} is required'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        leave_type = data['leave_type']
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        reason = data['reason']
        
        # Validate leave type
        if leave_type not in ['sick', 'casual', 'emergency']:
            return Response({
                'error': 'Invalid leave type'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate dates
        if start_date > end_date:
            return Response({
                'error': 'Start date cannot be after end date'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if start_date < date.today():
            return Response({
                'error': 'Cannot apply for past dates'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate leave days
        leave_days = (end_date - start_date).days + 1
        month_year = start_date.strftime('%Y-%m')
        
        # Check for overlapping leave applications
        overlapping_leaves = LeaveApplication.objects.filter(
            employee=user,
            status__in=['pending', 'approved'],
            start_date__lte=end_date,
            end_date__gte=start_date
        )
        
        if overlapping_leaves.exists():
            return Response({
                'error': 'You already have a leave application for this period'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create leave application
        leave_application = LeaveApplication.objects.create(
            employee=user,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            leave_days=leave_days,
            month_year=month_year,
            status='pending'
        )
        
        return Response({
            'message': 'Leave application submitted successfully',
            'leave_application': {
                'id': leave_application.id,
                'leave_type': leave_application.leave_type,
                'start_date': leave_application.start_date.isoformat(),
                'end_date': leave_application.end_date.isoformat(),
                'reason': leave_application.reason,
                'status': leave_application.status,
                'leave_days': leave_application.leave_days,
                'applied_at': leave_application.applied_at.isoformat(),
            }
        }, status=status.HTTP_201_CREATED)
        
    except json.JSONDecodeError:
        return Response({
            'error': 'Invalid JSON data'
        }, status=status.HTTP_400_BAD_REQUEST)
    except ValueError as e:
        return Response({
            'error': 'Invalid date format. Use YYYY-MM-DD'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_leave_applications(request):
    """
    Get leave applications based on user role
    """
    try:
        filters = {
            'status': request.GET.get('status'),
            'employee_id': request.GET.get('employee_id')
        }
        
        result = LeaveQueryService.get_leave_applications_optimized(
            user=request.user,
            filters=filters
        )
        
        if 'error' in result:
            return Response(result, status=status.HTTP_403_FORBIDDEN)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_leave_status(request, leave_id):
    """
    Update leave application status (HR/Supervisor only)
    """
    try:
        user = request.user
        
        # Check permissions
        if user.role not in ['hr', 'superadmin', 'supervisor']:
            return Response({
                'error': 'Unauthorized'
            }, status=status.HTTP_403_FORBIDDEN)
        
        data = json.loads(request.body)
        new_status = data.get('status')
        
        if new_status not in ['approved', 'rejected']:
            return Response({
                'error': 'Status must be either "approved" or "rejected"'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        leave_application = get_object_or_404(LeaveApplication, id=leave_id)
        
        # Supervisors can only update leaves for their branch
        if user.role == 'supervisor' and leave_application.employee.branch != user.branch:
            return Response({
                'error': 'Unauthorized'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if leave_application.status != 'pending':
            return Response({
                'error': 'Can only update pending leave applications'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        leave_application.status = new_status
        leave_application.approved_by = user
        leave_application.approved_at = timezone.now()
        leave_application.save()
        
        return Response({
            'message': f'Leave application {new_status} successfully',
            'leave_application': {
                'id': leave_application.id,
                'status': leave_application.status,
                'approved_by': f"{user.first_name} {user.last_name}",
                'approved_at': leave_application.approved_at.isoformat(),
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
