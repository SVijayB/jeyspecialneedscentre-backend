from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import datetime, date, timedelta
import django
from django.db import connection
import json

from .models import Branch
from attendance.models import AttendanceLog, LeaveApplication, CheckoutRequest

User = get_user_model()


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint to verify system status
    """
    try:
        # Test database connection
        connection.ensure_connection()
        
        health_status = {
            'status': 'healthy',
            'timestamp': django.utils.timezone.now().isoformat(),
            'django_version': django.get_version(),
            'debug_mode': settings.DEBUG,
            'database': 'connected',
            'environment': getattr(settings, 'DJANGO_ENVIRONMENT', 'unknown')
        }
        
        return Response(health_status, status=status.HTTP_200_OK)
        
    except Exception as e:
        health_status = {
            'status': 'unhealthy',
            'timestamp': django.utils.timezone.now().isoformat(),
            'error': str(e),
            'django_version': django.get_version(),
        }
        
        return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
@permission_classes([AllowAny])
def api_info(request):
    """
    Basic API information endpoint
    """
    api_info = {
        'name': 'Jey Special Needs Centre API',
        'version': '1.0.0',
        'description': 'Backend API for attendance and user management',
        'endpoints': {
            'health': '/api/health/',
            'info': '/api/info/',
            'auth': '/api/auth/',
            'users': '/api/users/',
            'attendance': '/api/attendance/',
        },
        'user_roles': [
            'Therapist',
            'Supervisor', 
            'HR',
            'Super Admin'
        ]
    }
    
    return Response(api_info, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    Get dashboard statistics based on user role
    """
    try:
        user = request.user
        today = timezone.now().date()
        
        # Base statistics
        stats = {
            'user_role': user.role,
            'current_date': today.isoformat(),
        }
        
        if user.role == 'therapist':
            # Therapist dashboard stats
            # Today's attendance
            today_attendance = AttendanceLog.objects.filter(employee=user, date=today).first()
            
            # This month's attendance
            month_start = today.replace(day=1)
            month_attendance = AttendanceLog.objects.filter(
                employee=user,
                date__gte=month_start,
                date__lte=today
            )
            
            # Pending requests
            pending_checkout_requests = CheckoutRequest.objects.filter(
                therapist=user,
                status='pending'
            ).count()
            
            pending_leave_requests = LeaveApplication.objects.filter(
                employee=user,
                status='pending'
            ).count()
            
            stats.update({
                'today_attendance': {
                    'checked_in': today_attendance.check_in_time.isoformat() if today_attendance and today_attendance.check_in_time else None,
                    'checked_out': today_attendance.check_out_time.isoformat() if today_attendance and today_attendance.check_out_time else None,
                    'status': today_attendance.status if today_attendance else 'not_marked',
                    'total_hours': str(today_attendance.total_hours) if today_attendance else '0.00',
                },
                'month_summary': {
                    'total_days': month_attendance.count(),
                    'present_days': month_attendance.filter(status='present').count(),
                    'late_days': month_attendance.filter(checkin_status__in=['late', 'very_late']).count(),
                    'absent_days': month_attendance.filter(status='absent').count(),
                    'avg_hours': month_attendance.filter(status='present').aggregate(
                        avg_hours=Avg('total_hours')
                    )['avg_hours'] or 0,
                },
                'pending_requests': {
                    'checkout_corrections': pending_checkout_requests,
                    'leave_applications': pending_leave_requests,
                }
            })
            
        elif user.role == 'supervisor':
            # Supervisor dashboard stats
            # Team members
            team_members = User.objects.filter(branch=user.branch, role='therapist')
            
            # Today's team attendance
            today_attendance = AttendanceLog.objects.filter(
                employee__in=team_members,
                date=today
            )
            
            # Pending requests to review
            pending_checkout_requests = CheckoutRequest.objects.filter(
                supervisor=user,
                status='pending'
            ).count()
            
            pending_leave_requests = LeaveApplication.objects.filter(
                employee__in=team_members,
                status='pending'
            ).count()
            
            stats.update({
                'team_summary': {
                    'total_members': team_members.count(),
                    'present_today': today_attendance.filter(status='present').count(),
                    'late_today': today_attendance.filter(checkin_status__in=['late', 'very_late']).count(),
                    'absent_today': today_attendance.filter(status='absent').count(),
                    'not_marked': team_members.count() - today_attendance.count(),
                },
                'pending_requests': {
                    'checkout_corrections': pending_checkout_requests,
                    'leave_applications': pending_leave_requests,
                },
                'branch': user.branch.name if user.branch else None,
            })
            
        elif user.role in ['hr', 'superadmin']:
            # HR/Admin dashboard stats
            # All users
            all_employees = User.objects.filter(role='therapist')
            all_supervisors = User.objects.filter(role='supervisor')
            
            # Today's overall attendance
            today_attendance = AttendanceLog.objects.filter(
                employee__in=all_employees,
                date=today
            )
            
            # Pending requests
            pending_checkout_requests = CheckoutRequest.objects.filter(status='pending').count()
            pending_leave_requests = LeaveApplication.objects.filter(status='pending').count()
            
            # Branch-wise summary
            branches = Branch.objects.filter(is_active=True)
            branch_stats = []
            
            for branch in branches:
                branch_employees = all_employees.filter(branch=branch)
                branch_attendance = today_attendance.filter(employee__in=branch_employees)
                
                branch_stats.append({
                    'branch_name': branch.name,
                    'total_employees': branch_employees.count(),
                    'present_today': branch_attendance.filter(status='present').count(),
                    'late_today': branch_attendance.filter(checkin_status__in=['late', 'very_late']).count(),
                    'absent_today': branch_attendance.filter(status='absent').count(),
                    'not_marked': branch_employees.count() - branch_attendance.count(),
                })
            
            stats.update({
                'overall_summary': {
                    'total_employees': all_employees.count(),
                    'total_supervisors': all_supervisors.count(),
                    'total_branches': branches.count(),
                    'present_today': today_attendance.filter(status='present').count(),
                    'late_today': today_attendance.filter(checkin_status__in=['late', 'very_late']).count(),
                    'absent_today': today_attendance.filter(status='absent').count(),
                    'not_marked': all_employees.count() - today_attendance.count(),
                },
                'pending_requests': {
                    'checkout_corrections': pending_checkout_requests,
                    'leave_applications': pending_leave_requests,
                },
                'branch_wise_stats': branch_stats,
            })
        
        return Response(stats, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def attendance_report(request):
    """
    Get attendance report for a date range
    """
    try:
        user = request.user
        
        # Get query parameters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        branch_id = request.GET.get('branch_id')
        employee_id = request.GET.get('employee_id')
        
        # Default to current month if no dates provided
        if not start_date or not end_date:
            today = date.today()
            start_date = today.replace(day=1).isoformat()
            end_date = today.isoformat()
        
        # Convert to date objects
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Base queryset based on user role
        if user.role == 'therapist':
            employees = User.objects.filter(id=user.id)
        elif user.role == 'supervisor':
            employees = User.objects.filter(branch=user.branch, role='therapist')
        elif user.role in ['hr', 'superadmin']:
            employees = User.objects.filter(role='therapist')
            
            # Apply filters for HR/Admin
            if branch_id:
                employees = employees.filter(branch_id=branch_id)
            if employee_id:
                employees = employees.filter(employee_id=employee_id)
        else:
            return Response({
                'error': 'Unauthorized'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get attendance data
        attendance_data = AttendanceLog.objects.filter(
            employee__in=employees,
            date__gte=start_date,
            date__lte=end_date
        ).select_related('employee', 'employee__branch').order_by('employee__employee_id', '-date')
        
        # Organize data by employee
        report_data = {}
        for attendance in attendance_data:
            emp_id = attendance.employee.employee_id
            
            if emp_id not in report_data:
                report_data[emp_id] = {
                    'employee': {
                        'id': attendance.employee.id,
                        'employee_id': attendance.employee.employee_id,
                        'name': f"{attendance.employee.first_name} {attendance.employee.last_name}",
                        'branch': attendance.employee.branch.name if attendance.employee.branch else None,
                    },
                    'summary': {
                        'total_days': 0,
                        'present_days': 0,
                        'late_days': 0,
                        'absent_days': 0,
                        'total_hours': 0,
                        'avg_hours': 0,
                    },
                    'attendance_records': []
                }
            
            # Add attendance record
            report_data[emp_id]['attendance_records'].append({
                'date': attendance.date.isoformat(),
                'check_in_time': attendance.check_in_time.isoformat() if attendance.check_in_time else None,
                'check_out_time': attendance.check_out_time.isoformat() if attendance.check_out_time else None,
                'status': attendance.status,
                'checkin_status': attendance.checkin_status,
                'total_hours': str(attendance.total_hours),
                'needs_checkout_correction': attendance.needs_checkout_correction,
            })
            
            # Update summary
            summary = report_data[emp_id]['summary']
            summary['total_days'] += 1
            
            if attendance.status == 'present':
                summary['present_days'] += 1
                summary['total_hours'] += float(attendance.total_hours)
            elif attendance.status == 'absent':
                summary['absent_days'] += 1
            
            if attendance.checkin_status in ['late', 'very_late']:
                summary['late_days'] += 1
        
        # Calculate averages
        for emp_data in report_data.values():
            summary = emp_data['summary']
            if summary['present_days'] > 0:
                summary['avg_hours'] = round(summary['total_hours'] / summary['present_days'], 2)
        
        return Response({
            'report': list(report_data.values()),
            'date_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'total_employees': len(report_data),
        }, status=status.HTTP_200_OK)
        
    except ValueError:
        return Response({
            'error': 'Invalid date format. Use YYYY-MM-DD'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
