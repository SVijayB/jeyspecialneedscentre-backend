from django.db import models
from django.conf import settings
from django.core.validators import ValidationError
from django.utils import timezone
from datetime import datetime, time, timedelta
import json

class AttendanceLog(models.Model):
    """Attendance log for tracking check-in/check-out"""
    
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('did_not_checkout', 'Did Not Checkout'),
    ]
    
    CHECKIN_STATUS_CHOICES = [
        ('on_time', 'On Time'),
        ('late', 'Late'),
        ('very_late', 'Very Late'),
        ('no_data', 'No Data'),
    ]
    
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendance_logs'
    )
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    date = models.DateField(help_text="Attendance date (YYYY-MM-DD)")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='absent'
    )
    checkin_status = models.CharField(
        max_length=20,
        choices=CHECKIN_STATUS_CHOICES,
        default='no_data'
    )
    total_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0.00,
        help_text="Total working hours"
    )
    needs_checkout_correction = models.BooleanField(
        default=False,
        help_text="True if employee forgot to checkout"
    )
    auto_checkout = models.BooleanField(
        default=False,
        help_text="True if system performed auto-checkout"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Attendance Log"
        verbose_name_plural = "Attendance Logs"
        ordering = ['-date', 'employee']
        indexes = [
            models.Index(fields=['employee', 'date']),  # Most common query pattern
            models.Index(fields=['date']),              # Dashboard queries
            models.Index(fields=['status']),            # Status filtering
            models.Index(fields=['employee', '-date']), # Employee history
        ]
    
    def __str__(self):
        return f"{self.employee.employee_id} - {self.date} ({self.status})"
    
    def save(self, *args, **kwargs):
        # Calculate total hours if both check_in and check_out are present
        if self.check_in_time and self.check_out_time:
            time_diff = self.check_out_time - self.check_in_time
            self.total_hours = round(time_diff.total_seconds() / 3600, 2)
            self.status = 'present'
            self.needs_checkout_correction = False
        elif self.check_in_time and not self.check_out_time:
            # If checked in but not out, mark for correction
            self.status = 'did_not_checkout'
            self.needs_checkout_correction = True
        
        # Determine check-in status
        if self.check_in_time:
            self.checkin_status = self._calculate_checkin_status()
        
        super().save(*args, **kwargs)
    
    def _calculate_checkin_status(self):
        """Calculate if check-in was on time, late, or very late"""
        if not self.check_in_time:
            return 'no_data'
        
        # Get expected login time for this user
        expected_time = datetime.combine(
            self.date,
            self.employee.login_time
        )
        grace_time = expected_time + timedelta(minutes=self.employee.grace_time)
        very_late_time = expected_time + timedelta(minutes=30)  # 30 mins = very late
        
        checkin_time = self.check_in_time.replace(tzinfo=None)
        
        if checkin_time <= expected_time:
            return 'on_time'
        elif checkin_time <= grace_time:
            return 'on_time'  # Within grace period
        elif checkin_time <= very_late_time:
            return 'late'
        else:
            return 'very_late'
    
    def can_checkout_now(self):
        """Check if user can checkout now"""
        if not self.check_in_time:
            return False, "No check-in recorded for today"
        
        if self.check_out_time:
            return False, "Already checked out for today"
        
        # Check if it's past 6 PM
        now = timezone.now()
        cutoff_time = datetime.combine(self.date, time(18, 0))  # 6 PM
        
        if now.time() > time(18, 0) and now.date() == self.date:
            return False, "Cannot checkout after 6 PM. Please submit a checkout request."
        
        return True, "Can checkout"


class CheckoutRequest(models.Model):
    """Request for correcting missed checkout"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    therapist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='checkout_requests',
        limit_choices_to={'role': 'therapist'}
    )
    attendance_log = models.ForeignKey(
        AttendanceLog,
        on_delete=models.CASCADE,
        related_name='checkout_requests'
    )
    requested_checkout_time = models.TimeField(
        help_text="Time when employee claims they left"
    )
    reason = models.TextField(help_text="Reason for missing checkout")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='supervised_checkout_requests',
        limit_choices_to={'role': 'supervisor'}
    )
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    supervisor_notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Checkout Request"
        verbose_name_plural = "Checkout Requests"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.therapist.employee_id} - {self.attendance_log.date} ({self.status})"
    
    def clean(self):
        """Validate the checkout request"""
        # Check if requested time is after check-in time
        if (self.attendance_log.check_in_time and 
            self.requested_checkout_time <= self.attendance_log.check_in_time.time()):
            raise ValidationError("Checkout time must be after check-in time")
        
        # Check if requested time is before 6 PM
        if self.requested_checkout_time > time(18, 0):
            raise ValidationError("Checkout time cannot be after 6 PM")
        
        # Check if request is for past dates only
        if self.attendance_log.date >= timezone.now().date():
            raise ValidationError("Can only request checkout correction for past dates")
    
    def approve(self, supervisor, notes=""):
        """Approve the checkout request"""
        self.status = 'approved'
        self.processed_at = timezone.now()
        self.supervisor_notes = notes
        
        # Update the attendance log
        checkout_datetime = datetime.combine(
            self.attendance_log.date,
            self.requested_checkout_time
        )
        self.attendance_log.check_out_time = checkout_datetime
        self.attendance_log.save()
        
        self.save()
    
    def reject(self, supervisor, notes=""):
        """Reject the checkout request"""
        self.status = 'rejected'
        self.processed_at = timezone.now()
        self.supervisor_notes = notes
        self.save()


class LeaveApplication(models.Model):
    """Leave application model"""
    
    LEAVE_TYPE_CHOICES = [
        ('casual_leave', 'Casual Leave'),
        ('unpaid_leave', 'Unpaid Leave'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='leave_applications'
    )
    leave_type = models.CharField(
        max_length=20,
        choices=LEAVE_TYPE_CHOICES
    )
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    leave_days = models.IntegerField(help_text="Total number of leave days")
    applied_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_leaves',
        limit_choices_to={'role__in': ['supervisor', 'hr', 'superadmin']}
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    month_year = models.CharField(
        max_length=7,
        help_text="Month-Year for CL tracking (YYYY-MM)"
    )
    
    class Meta:
        verbose_name = "Leave Application"
        verbose_name_plural = "Leave Applications"
        ordering = ['-applied_at']
    
    def __str__(self):
        return f"{self.employee.employee_id} - {self.leave_type} ({self.start_date} to {self.end_date})"
    
    def save(self, *args, **kwargs):
        # Calculate leave days
        self.leave_days = (self.end_date - self.start_date).days + 1
        
        # Set month_year for CL tracking
        self.month_year = self.start_date.strftime('%Y-%m')
        
        super().save(*args, **kwargs)
    
    def clean(self):
        """Validate leave application"""
        if self.start_date > self.end_date:
            raise ValidationError("End date must be after start date")
        
        if self.start_date < timezone.now().date():
            raise ValidationError("Cannot apply for leave in the past")


class QRCodeLog(models.Model):
    """Log for tracking QR code generation"""
    
    QR_TYPE_CHOICES = [
        ('checkin', 'Check-in'),
    ]
    
    employee_id = models.CharField(max_length=20)
    issued_at = models.DateTimeField()
    qr_type = models.CharField(
        max_length=20,
        choices=QR_TYPE_CHOICES,
        default='checkin'
    )
    is_used = models.BooleanField(
        default=False,
        help_text="True if QR code was successfully used"
    )
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "QR Code Log"
        verbose_name_plural = "QR Code Logs"
        ordering = ['-issued_at']
    
    def __str__(self):
        return f"{self.employee_id} - {self.qr_type} - {self.issued_at}"
    
    def is_expired(self):
        """Check if QR code is expired (3 minutes)"""
        now = timezone.now()
        time_diff = (now - self.issued_at).total_seconds()
        return time_diff > 180  # 3 minutes
    
    def mark_as_used(self):
        """Mark QR code as used"""
        self.is_used = True
        self.used_at = timezone.now()
        self.save()
