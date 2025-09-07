"""
Checkout correction request views
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import datetime
from decimal import Decimal
import json
from ..models import AttendanceLog, CheckoutRequest

User = get_user_model()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_checkout_correction(request):
    """
    Request checkout time correction
    """
    try:
        data = json.loads(request.body)
        
        user = request.user
        attendance_log_id = data.get('attendance_log_id')
        requested_time = data.get('requested_checkout_time')
        reason = data.get('reason')
        
        if not all([attendance_log_id, requested_time, reason]):
            return Response({
                'error': 'attendance_log_id, requested_checkout_time, and reason are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get attendance log
        attendance_log = get_object_or_404(AttendanceLog, id=attendance_log_id, employee=user)
        
        if not attendance_log.needs_checkout_correction:
            return Response({
                'error': 'This attendance record does not need checkout correction'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if request already exists
        existing_request = CheckoutRequest.objects.filter(
            therapist=user,
            attendance_log=attendance_log
        ).first()
        
        if existing_request:
            return Response({
                'error': 'Checkout correction request already exists for this attendance'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Parse requested time
        try:
            requested_checkout_time = datetime.strptime(requested_time, '%H:%M').time()
        except ValueError:
            return Response({
                'error': 'Invalid time format. Use HH:MM'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get supervisor
        supervisor = user.supervisor
        if not supervisor:
            return Response({
                'error': 'No supervisor assigned'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create checkout request
        checkout_request = CheckoutRequest.objects.create(
            therapist=user,
            attendance_log=attendance_log,
            requested_checkout_time=requested_checkout_time,
            reason=reason,
            supervisor=supervisor,
            status='pending'
        )
        
        return Response({
            'message': 'Checkout correction request submitted successfully',
            'checkout_request': {
                'id': checkout_request.id,
                'attendance_date': attendance_log.date.isoformat(),
                'requested_checkout_time': checkout_request.requested_checkout_time.strftime('%H:%M'),
                'reason': checkout_request.reason,
                'status': checkout_request.status,
                'created_at': checkout_request.created_at.isoformat(),
            }
        }, status=status.HTTP_201_CREATED)
        
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
def get_checkout_requests(request):
    """
    Get checkout correction requests based on user role
    """
    try:
        user = request.user
        
        # Get query parameters
        status_filter = request.GET.get('status')
        
        # Base queryset based on user role
        if user.role == 'therapist':
            queryset = CheckoutRequest.objects.filter(therapist=user)
        elif user.role == 'supervisor':
            queryset = CheckoutRequest.objects.filter(supervisor=user)
        elif user.role in ['hr', 'superadmin']:
            queryset = CheckoutRequest.objects.all()
        else:
            return Response({
                'error': 'Unauthorized'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Apply filters
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        checkout_requests = queryset.select_related(
            'therapist', 'attendance_log', 'supervisor'
        ).order_by('-created_at')
        
        requests_data = []
        for req in checkout_requests:
            requests_data.append({
                'id': req.id,
                'therapist': {
                    'id': req.therapist.id,
                    'employee_id': req.therapist.employee_id,
                    'name': f"{req.therapist.first_name} {req.therapist.last_name}",
                },
                'attendance_log': {
                    'id': req.attendance_log.id,
                    'date': req.attendance_log.date.isoformat(),
                    'check_in_time': req.attendance_log.check_in_time.isoformat() if req.attendance_log.check_in_time else None,
                },
                'requested_checkout_time': req.requested_checkout_time.strftime('%H:%M'),
                'reason': req.reason,
                'status': req.status,
                'supervisor': {
                    'name': f"{req.supervisor.first_name} {req.supervisor.last_name}",
                    'employee_id': req.supervisor.employee_id
                } if req.supervisor else None,
                'supervisor_notes': req.supervisor_notes,
                'created_at': req.created_at.isoformat(),
                'processed_at': req.processed_at.isoformat() if req.processed_at else None,
            })
        
        return Response({
            'checkout_requests': requests_data,
            'count': len(requests_data)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_checkout_request(request, request_id):
    """
    Update checkout correction request status (Supervisor only)
    """
    try:
        user = request.user
        
        # Check permissions
        if user.role not in ['supervisor', 'hr', 'superadmin']:
            return Response({
                'error': 'Unauthorized'
            }, status=status.HTTP_403_FORBIDDEN)
        
        data = json.loads(request.body)
        new_status = data.get('status')
        supervisor_notes = data.get('supervisor_notes', '')
        
        if new_status not in ['approved', 'rejected']:
            return Response({
                'error': 'Status must be either "approved" or "rejected"'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        checkout_request = get_object_or_404(CheckoutRequest, id=request_id)
        
        # Supervisors can only update requests for their supervised therapists
        if user.role == 'supervisor' and checkout_request.supervisor != user:
            return Response({
                'error': 'Unauthorized'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if checkout_request.status != 'pending':
            return Response({
                'error': 'Can only update pending checkout requests'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        checkout_request.status = new_status
        checkout_request.supervisor_notes = supervisor_notes
        checkout_request.processed_at = timezone.now()
        checkout_request.save()
        
        # If approved, update the attendance log
        if new_status == 'approved':
            attendance_log = checkout_request.attendance_log
            checkout_datetime = datetime.combine(
                attendance_log.date, 
                checkout_request.requested_checkout_time
            )
            checkout_datetime = timezone.make_aware(checkout_datetime)
            
            attendance_log.check_out_time = checkout_datetime
            attendance_log.needs_checkout_correction = False
            
            # Recalculate total hours
            if attendance_log.check_in_time:
                duration = checkout_datetime - attendance_log.check_in_time
                attendance_log.total_hours = Decimal(str(round(duration.total_seconds() / 3600, 2)))
            
            attendance_log.save()
        
        return Response({
            'message': f'Checkout request {new_status} successfully',
            'checkout_request': {
                'id': checkout_request.id,
                'status': checkout_request.status,
                'supervisor_notes': checkout_request.supervisor_notes,
                'processed_at': checkout_request.processed_at.isoformat(),
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
