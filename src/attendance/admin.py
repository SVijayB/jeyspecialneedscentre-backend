from django.contrib import admin
from .models import AttendanceLog, CheckoutRequest, LeaveApplication, QRCodeLog

@admin.register(AttendanceLog)
class AttendanceLogAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'check_in_time', 'check_out_time', 'status', 'total_hours', 'needs_checkout_correction']
    list_filter = ['status', 'date', 'needs_checkout_correction', 'auto_checkout', 'employee__branch']
    search_fields = ['employee__username', 'employee__employee_id', 'employee__first_name', 'employee__last_name']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('employee', 'employee__branch')

@admin.register(CheckoutRequest)
class CheckoutRequestAdmin(admin.ModelAdmin):
    list_display = ['therapist', 'attendance_log', 'requested_checkout_time', 'status', 'supervisor', 'created_at']
    list_filter = ['status', 'created_at', 'therapist__branch']
    search_fields = ['therapist__username', 'therapist__employee_id', 'supervisor__username', 'reason']
    readonly_fields = ['created_at', 'processed_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('therapist', 'supervisor', 'attendance_log')

@admin.register(LeaveApplication)
class LeaveApplicationAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'start_date', 'end_date', 'leave_days', 'status', 'applied_at']
    list_filter = ['leave_type', 'status', 'start_date', 'employee__branch']
    search_fields = ['employee__username', 'employee__employee_id', 'reason']
    date_hierarchy = 'start_date'
    readonly_fields = ['leave_days', 'applied_at', 'approved_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('employee', 'approved_by')

@admin.register(QRCodeLog)
class QRCodeLogAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'qr_type', 'issued_at', 'is_used', 'used_at']
    list_filter = ['qr_type', 'is_used', 'issued_at']
    search_fields = ['employee_id']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False  # QR codes should only be generated programmatically
