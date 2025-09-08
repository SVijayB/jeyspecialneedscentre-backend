"""
Attendance views package

Contains:
- QR code generation and scanning functionality
- Utility functions for attendance calculations
"""

# QR Code Management
from .qr_views import generate_qr_code, scan_qr_code

# Utility functions
from .utils import calculate_work_hours, get_checkin_status, is_qr_code_valid, format_attendance_response
# - update_leave_status -> POST /api/attendance/leaves/{id}/approve/ or /reject/
# - request_checkout_correction -> POST /api/attendance/checkout-requests/
# - get_checkout_requests -> GET /api/attendance/checkout-requests/
# - update_checkout_request -> POST /api/attendance/checkout-requests/{id}/approve/ or /reject/
