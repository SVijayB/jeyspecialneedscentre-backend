"""
DRF Serializers for Attendance management
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import AttendanceLog, LeaveApplication, CheckoutRequest

User = get_user_model()


class AttendanceLogSerializer(serializers.ModelSerializer):
    """Serializer for AttendanceLog model"""
    
    employee_name = serializers.SerializerMethodField()
    employee_id = serializers.CharField(source='employee.employee_id', read_only=True)
    branch_name = serializers.CharField(source='employee.branch.name', read_only=True)
    
    class Meta:
        model = AttendanceLog
        fields = [
            'id', 'employee', 'employee_name', 'employee_id', 'branch_name',
            'check_in_time', 'check_out_time', 'date', 'status', 'checkin_status',
            'total_hours', 'needs_checkout_correction', 'auto_checkout',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'total_hours', 'status', 'checkin_status']
    
    def get_employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}"


class AttendanceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating attendance records"""
    
    employee_id = serializers.CharField(write_only=True)
    
    class Meta:
        model = AttendanceLog
        fields = ['employee_id', 'check_in_time', 'check_out_time', 'date']
    
    def validate_employee_id(self, value):
        """Validate employee exists"""
        try:
            employee = User.objects.get(employee_id=value)
            return employee
        except User.DoesNotExist:
            raise serializers.ValidationError("Employee not found")
    
    def validate(self, attrs):
        """Validate attendance data"""
        employee = attrs['employee_id']  # This is now a User instance
        date = attrs['date']
        
        # Check for duplicate attendance
        if AttendanceLog.objects.filter(employee=employee, date=date).exists():
            raise serializers.ValidationError("Attendance already exists for this date")
        
        # Validate check-in/check-out times
        check_in = attrs.get('check_in_time')
        check_out = attrs.get('check_out_time')
        
        if check_out and not check_in:
            raise serializers.ValidationError("Cannot have check-out without check-in")
        
        if check_in and check_out and check_out <= check_in:
            raise serializers.ValidationError("Check-out time must be after check-in time")
        
        return attrs
    
    def create(self, validated_data):
        """Create attendance record"""
        employee = validated_data.pop('employee_id')  # Remove and use as employee
        validated_data['employee'] = employee
        return super().create(validated_data)


class LeaveApplicationSerializer(serializers.ModelSerializer):
    """Serializer for LeaveApplication model"""
    
    employee_name = serializers.SerializerMethodField()
    employee_id = serializers.CharField(source='employee.employee_id', read_only=True)
    branch_name = serializers.CharField(source='employee.branch.name', read_only=True)
    approved_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = LeaveApplication
        fields = [
            'id', 'employee', 'employee_name', 'employee_id', 'branch_name',
            'leave_type', 'start_date', 'end_date', 'reason', 'status',
            'leave_days', 'month_year', 'applied_at', 'approved_by',
            'approved_by_name', 'approved_at'
        ]
        read_only_fields = [
            'employee', 'leave_days', 'month_year', 'applied_at', 
            'approved_by', 'approved_at'
        ]
    
    def get_employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}"
    
    def get_approved_by_name(self, obj):
        if obj.approved_by:
            return f"{obj.approved_by.first_name} {obj.approved_by.last_name}"
        return None


class LeaveApplicationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating leave applications"""
    
    class Meta:
        model = LeaveApplication
        fields = ['leave_type', 'start_date', 'end_date', 'reason']
    
    def validate(self, attrs):
        """Validate leave application"""
        start_date = attrs['start_date']
        end_date = attrs['end_date']
        
        if start_date > end_date:
            raise serializers.ValidationError("Start date cannot be after end date")
        
        # Check for overlapping leaves
        employee = self.context['request'].user
        overlapping = LeaveApplication.objects.filter(
            employee=employee,
            status__in=['pending', 'approved'],
            start_date__lte=end_date,
            end_date__gte=start_date
        )
        
        if overlapping.exists():
            raise serializers.ValidationError("You already have a leave application for this period")
        
        return attrs
    
    def create(self, validated_data):
        """Create leave application"""
        validated_data['employee'] = self.context['request'].user
        
        # Calculate leave days
        start_date = validated_data['start_date']
        end_date = validated_data['end_date']
        validated_data['leave_days'] = (end_date - start_date).days + 1
        validated_data['month_year'] = start_date.strftime('%Y-%m')
        
        return super().create(validated_data)


class CheckoutRequestSerializer(serializers.ModelSerializer):
    """Serializer for CheckoutRequest model"""
    
    therapist_name = serializers.SerializerMethodField()
    therapist_id = serializers.CharField(source='therapist.employee_id', read_only=True)
    supervisor_name = serializers.SerializerMethodField()
    attendance_date = serializers.DateField(source='attendance_log.date', read_only=True)
    
    class Meta:
        model = CheckoutRequest
        fields = [
            'id', 'therapist', 'therapist_name', 'therapist_id',
            'attendance_log', 'attendance_date', 'requested_checkout_time',
            'reason', 'status', 'supervisor', 'supervisor_name',
            'created_at', 'processed_at', 'supervisor_notes'
        ]
        read_only_fields = [
            'therapist', 'supervisor', 'created_at', 'processed_at'
        ]
    
    def get_therapist_name(self, obj):
        return f"{obj.therapist.first_name} {obj.therapist.last_name}"
    
    def get_supervisor_name(self, obj):
        if obj.supervisor:
            return f"{obj.supervisor.first_name} {obj.supervisor.last_name}"
        return None


class CheckoutRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating checkout requests"""
    
    class Meta:
        model = CheckoutRequest
        fields = ['attendance_log', 'requested_checkout_time', 'reason']
    
    def validate_attendance_log(self, value):
        """Validate attendance log belongs to requesting user"""
        if value.employee != self.context['request'].user:
            raise serializers.ValidationError("You can only request corrections for your own attendance")
        
        if value.check_out_time:
            raise serializers.ValidationError("This attendance already has a checkout time")
        
        return value
    
    def create(self, validated_data):
        """Create checkout request"""
        validated_data['therapist'] = self.context['request'].user
        validated_data['supervisor'] = self.context['request'].user.supervisor
        return super().create(validated_data)
