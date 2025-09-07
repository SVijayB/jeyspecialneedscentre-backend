"""
Shared utilities for attendance views
"""

from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal


def calculate_work_hours(check_in_time, check_out_time):
    """
    Calculate total work hours between check-in and check-out
    """
    if not check_in_time or not check_out_time:
        return Decimal('0.00')
    
    duration = check_out_time - check_in_time
    hours = round(duration.total_seconds() / 3600, 2)
    return Decimal(str(hours))


def get_checkin_status(check_in_time, expected_time, grace_time_minutes):
    """
    Determine check-in status based on timing
    """
    grace_deadline = expected_time + timedelta(minutes=grace_time_minutes)
    late_deadline = grace_deadline + timedelta(hours=1)
    
    if check_in_time <= grace_deadline:
        return 'on_time'
    elif check_in_time <= late_deadline:
        return 'late'
    else:
        return 'very_late'


def is_qr_code_valid(qr_timestamp, expiry_minutes=3):
    """
    Check if QR code is still valid based on timestamp
    """
    qr_time = datetime.fromisoformat(qr_timestamp.replace('Z', '+00:00'))
    current_time = timezone.now()
    
    time_diff = (current_time - qr_time).total_seconds()
    return time_diff <= (expiry_minutes * 60)


def format_attendance_response(attendance_log):
    """
    Format attendance log for API response
    """
    return {
        'id': attendance_log.id,
        'date': attendance_log.date.isoformat(),
        'check_in_time': attendance_log.check_in_time.isoformat() if attendance_log.check_in_time else None,
        'check_out_time': attendance_log.check_out_time.isoformat() if attendance_log.check_out_time else None,
        'status': attendance_log.status,
        'checkin_status': attendance_log.checkin_status,
        'total_hours': str(attendance_log.total_hours),
        'needs_checkout_correction': attendance_log.needs_checkout_correction,
    }
