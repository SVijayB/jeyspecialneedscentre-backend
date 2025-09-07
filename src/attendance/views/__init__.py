"""
Attendance views package - organized by functionality

This package splits the large views.py file into manageable modules:
- qr_views.py: QR code generation and scanning
- attendance_views.py: Basic attendance operations (checkout, records)
- leave_views.py: Leave application management
- checkout_views.py: Checkout correction requests
- utils.py: Shared utility functions
"""

# QR Code Management
from .qr_views import generate_qr_code, scan_qr_code

# Basic Attendance Management  
from .attendance_views import checkout_button, get_attendance, get_today_attendance

# Leave Management
from .leave_views import apply_leave, get_leave_applications, update_leave_status

# Checkout Correction Management
from .checkout_views import request_checkout_correction, get_checkout_requests, update_checkout_request

# Utility functions (optional, for internal use)
from .utils import calculate_work_hours, get_checkin_status, is_qr_code_valid, format_attendance_response
