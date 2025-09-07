"""
QR Code generation and scanning views
"""

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json
import qrcode
import io
import base64
from ..models import AttendanceLog, QRCodeLog

User = get_user_model()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_qr_code(request):
    """
    Generate QR code for check-in ONLY (checkout is button-based)
    """
    try:
        user = request.user
        current_time = timezone.now()
        today = current_time.date()
        
        # Check if user already checked in today and hasn't checked out
        existing_attendance = AttendanceLog.objects.filter(
            employee=user,
            date=today,
            check_in_time__isnull=False,
            check_out_time__isnull=True
        ).first()
        
        if existing_attendance:
            return Response({
                'error': 'Already checked in today. Please checkout first before generating new QR.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create QR code data for check-in only
        qr_data = {
            'employee_id': user.employee_id,
            'type': 'checkin',
            'timestamp': current_time.isoformat(),
            'branch_id': user.branch.id if user.branch else None
        }
        
        # Generate QR code image
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(json.dumps(qr_data))
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        # Log QR code generation
        QRCodeLog.objects.create(
            employee_id=user.employee_id,
            issued_at=current_time,
            qr_type='checkin',
            is_used=False
        )
        
        return Response({
            'qr_code': f"data:image/png;base64,{img_str}",
            'qr_data': qr_data,
            'expires_at': (current_time + timedelta(minutes=3)).isoformat(),
            'message': 'QR code generated for check-in'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def scan_qr_code(request):
    """
    Process QR code scan for CHECK-IN only (checkout is button-based)
    """
    try:
        data = json.loads(request.body)
        qr_data = data.get('qr_data')
        
        if not qr_data:
            return Response({
                'error': 'QR data is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Parse QR data
        if isinstance(qr_data, str):
            qr_data = json.loads(qr_data)
        
        employee_id = qr_data.get('employee_id')
        qr_type = qr_data.get('type')
        qr_timestamp = qr_data.get('timestamp')
        
        # Only allow check-in QR codes
        if qr_type != 'checkin':
            return Response({
                'error': 'Invalid QR type. Only check-in QR codes are supported.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify QR code validity (3 minute expiry as per spec)
        qr_time = datetime.fromisoformat(qr_timestamp.replace('Z', '+00:00'))
        current_time = timezone.now()
        
        if (current_time - qr_time).total_seconds() > 180:  # 3 minutes
            return Response({
                'error': 'QR code has expired'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get employee
        try:
            employee = User.objects.get(employee_id=employee_id)
        except User.DoesNotExist:
            return Response({
                'error': 'Invalid employee ID'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Mark QR code as used
        qr_log = QRCodeLog.objects.filter(
            employee_id=employee_id,
            issued_at__gte=qr_time - timedelta(seconds=5),
            issued_at__lte=qr_time + timedelta(seconds=5),
            is_used=False
        ).first()
        
        if qr_log:
            qr_log.is_used = True
            qr_log.used_at = current_time
            qr_log.save()
        
        today = current_time.date()
        
        # Check if already checked in today without checkout
        existing_attendance = AttendanceLog.objects.filter(
            employee=employee,
            date=today,
            check_in_time__isnull=False,
            check_out_time__isnull=True
        ).first()
        
        if existing_attendance:
            return Response({
                'error': 'Already checked in today. Please checkout first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # CREATE A NEW attendance log for each check-in (don't reuse existing completed ones)
        attendance_log = AttendanceLog.objects.create(
            employee=employee,
            date=today,
            check_in_time=current_time,
            check_out_time=None,
            status='present',
            checkin_status='on_time',  # Will be updated below
            total_hours=Decimal('0.00'),
            needs_checkout_correction=False,
            auto_checkout=False,
        )
        
        # Determine check-in status
        expected_time = datetime.combine(today, employee.login_time) + timedelta(minutes=employee.grace_time)
        expected_time = timezone.make_aware(expected_time)
        
        if current_time <= expected_time:
            attendance_log.checkin_status = 'on_time'
        elif current_time <= expected_time + timedelta(hours=1):
            attendance_log.checkin_status = 'late'
        else:
            attendance_log.checkin_status = 'very_late'
        
        attendance_log.save()  # Save the updated attendance log
        
        return Response({
            'message': f'Successfully checked in at {current_time.strftime("%H:%M")}',
            'attendance': {
                'id': attendance_log.id,
                'date': attendance_log.date.isoformat(),
                'check_in_time': attendance_log.check_in_time.isoformat(),
                'checkin_status': attendance_log.checkin_status,
                'status': attendance_log.status,
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
