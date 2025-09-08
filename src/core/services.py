"""
Optimized service classes for batch database operations
This module provides optimized methods to replace individual query patterns
with efficient batch operations and aggregations.
"""

from django.db.models import Count, Q, Avg, Sum, Case, When, IntegerField
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, datetime
from typing import Dict, List, Any

from core.models import Branch
from attendance.models import AttendanceLog, LeaveApplication, CheckoutRequest

User = get_user_model()


class AttendanceAnalyticsService:
    """Optimized service for attendance analytics and dashboard data"""
    
    @staticmethod
    def get_dashboard_stats_optimized(user, today: date) -> Dict[str, Any]:
        """
        Get all dashboard statistics with optimized queries
        Replaces multiple individual queries with batch operations
        """
        
        if user.role == 'therapist':
            return AttendanceAnalyticsService._get_therapist_stats_optimized(user, today)
        elif user.role == 'supervisor':
            return AttendanceAnalyticsService._get_supervisor_stats_optimized(user, today)
        elif user.role in ['hr', 'superadmin']:
            return AttendanceAnalyticsService._get_admin_stats_optimized(user, today)
        
        return {}
    
    @staticmethod
    def _get_therapist_stats_optimized(user, today: date) -> Dict[str, Any]:
        """Optimized therapist dashboard stats"""
        
        # Single query for today's attendance
        today_attendance = AttendanceLog.objects.filter(
            employee=user, 
            date=today
        ).first()
        
        # Single query for month summary with aggregation
        month_start = today.replace(day=1)
        month_stats = AttendanceLog.objects.filter(
            employee=user,
            date__gte=month_start,
            date__lte=today
        ).aggregate(
            total_days=Count('id'),
            present_days=Count('id', filter=Q(status='present')),
            late_days=Count('id', filter=Q(checkin_status__in=['late', 'very_late'])),
            absent_days=Count('id', filter=Q(status='absent')),
            avg_hours=Avg('total_hours', filter=Q(status='present'))
        )
        
        # Single query for pending requests
        pending_stats = {
            'checkout_corrections': CheckoutRequest.objects.filter(
                therapist=user, status='pending'
            ).count(),
            'leave_applications': LeaveApplication.objects.filter(
                employee=user, status='pending'
            ).count()
        }
        
        return {
            'user_role': user.role,
            'current_date': today.isoformat(),
            'today_attendance': {
                'checked_in': today_attendance.check_in_time.isoformat() if today_attendance and today_attendance.check_in_time else None,
                'checked_out': today_attendance.check_out_time.isoformat() if today_attendance and today_attendance.check_out_time else None,
                'status': today_attendance.status if today_attendance else 'not_marked',
                'total_hours': str(today_attendance.total_hours) if today_attendance else '0.00',
            },
            'month_summary': {
                'total_days': month_stats['total_days'] or 0,
                'present_days': month_stats['present_days'] or 0,
                'late_days': month_stats['late_days'] or 0,
                'absent_days': month_stats['absent_days'] or 0,
                'avg_hours': float(month_stats['avg_hours']) if month_stats['avg_hours'] else 0.0,
            },
            'pending_requests': pending_stats
        }
    
    @staticmethod
    def _get_supervisor_stats_optimized(user, today: date) -> Dict[str, Any]:
        """Optimized supervisor dashboard stats"""
        
        # Single query for team members count
        team_count = User.objects.filter(
            branch=user.branch, 
            role='therapist'
        ).count()
        
        # Single aggregated query for team attendance today
        team_attendance_stats = AttendanceLog.objects.filter(
            employee__branch=user.branch,
            employee__role='therapist',
            date=today
        ).aggregate(
            present_today=Count('id', filter=Q(status='present')),
            late_today=Count('id', filter=Q(checkin_status__in=['late', 'very_late'])),
            absent_today=Count('id', filter=Q(status='absent')),
            total_marked=Count('id')
        )
        
        # Single query for pending requests
        pending_stats = {
            'checkout_corrections': CheckoutRequest.objects.filter(
                supervisor=user, status='pending'
            ).count(),
            'leave_applications': LeaveApplication.objects.filter(
                employee__branch=user.branch, status='pending'
            ).count()
        }
        
        return {
            'user_role': user.role,
            'current_date': today.isoformat(),
            'team_summary': {
                'total_members': team_count,
                'present_today': team_attendance_stats['present_today'] or 0,
                'late_today': team_attendance_stats['late_today'] or 0,
                'absent_today': team_attendance_stats['absent_today'] or 0,
                'not_marked': team_count - (team_attendance_stats['total_marked'] or 0),
            },
            'pending_requests': pending_stats,
            'branch': user.branch.name if user.branch else None,
        }
    
    @staticmethod
    def _get_admin_stats_optimized(user, today: date) -> Dict[str, Any]:
        """Optimized admin/HR dashboard stats with single query for branch statistics"""
        
        # Single query for user counts
        user_stats = User.objects.aggregate(
            total_employees=Count('id', filter=Q(role='therapist')),
            total_supervisors=Count('id', filter=Q(role='supervisor'))
        )
        
        # Single query for overall attendance today
        overall_attendance_stats = AttendanceLog.objects.filter(
            employee__role='therapist',
            date=today
        ).aggregate(
            present_today=Count('id', filter=Q(status='present')),
            late_today=Count('id', filter=Q(checkin_status__in=['late', 'very_late'])),
            absent_today=Count('id', filter=Q(status='absent')),
            total_marked=Count('id')
        )
        
        # Single query for pending requests
        pending_stats = {
            'checkout_corrections': CheckoutRequest.objects.filter(status='pending').count(),
            'leave_applications': LeaveApplication.objects.filter(status='pending').count()
        }
        
        # OPTIMIZED: Single query for all branch statistics
        branch_stats = AttendanceAnalyticsService.get_branch_statistics_batch(today)
        
        return {
            'user_role': user.role,
            'current_date': today.isoformat(),
            'overall_summary': {
                'total_employees': user_stats['total_employees'] or 0,
                'total_supervisors': user_stats['total_supervisors'] or 0,
                'total_branches': len(branch_stats),
                'present_today': overall_attendance_stats['present_today'] or 0,
                'late_today': overall_attendance_stats['late_today'] or 0,
                'absent_today': overall_attendance_stats['absent_today'] or 0,
                'not_marked': (user_stats['total_employees'] or 0) - (overall_attendance_stats['total_marked'] or 0),
            },
            'pending_requests': pending_stats,
            'branch_wise_stats': branch_stats,
        }
    
    @staticmethod
    def get_branch_statistics_batch(today: date) -> List[Dict[str, Any]]:
        """
        OPTIMIZED: Get all branch statistics in a single query instead of N queries
        This replaces the N+1 query problem in the original dashboard_stats view
        """
        
        # Single query with annotations to get all branch stats at once
        branch_stats = Branch.objects.annotate(
            # Count total employees per branch
            total_employees=Count(
                'users', 
                filter=Q(users__role='therapist'),
                distinct=True
            ),
            # Count today's attendance statistics per branch
            present_today=Count(
                'users__attendance_logs',
                filter=Q(
                    users__attendance_logs__date=today,
                    users__attendance_logs__status='present'
                ),
                distinct=True
            ),
            late_today=Count(
                'users__attendance_logs',
                filter=Q(
                    users__attendance_logs__date=today,
                    users__attendance_logs__checkin_status__in=['late', 'very_late']
                ),
                distinct=True
            ),
            absent_today=Count(
                'users__attendance_logs',
                filter=Q(
                    users__attendance_logs__date=today,
                    users__attendance_logs__status='absent'
                ),
                distinct=True
            ),
            total_marked=Count(
                'users__attendance_logs',
                filter=Q(users__attendance_logs__date=today),
                distinct=True
            )
        ).values(
            'name', 'total_employees', 'present_today', 
            'late_today', 'absent_today', 'total_marked'
        )
        
        # Convert to list of dictionaries with calculated not_marked
        return [
            {
                'branch_name': branch['name'],
                'total_employees': branch['total_employees'],
                'present_today': branch['present_today'],
                'late_today': branch['late_today'],
                'absent_today': branch['absent_today'],
                'not_marked': branch['total_employees'] - branch['total_marked'],
            }
            for branch in branch_stats
        ]
    
    @staticmethod
    def get_attendance_report_optimized(user, start_date: date, end_date: date, 
                                      branch_id: int = None, employee_id: str = None) -> Dict[str, Any]:
        """
        Optimized attendance report using database aggregation instead of Python loops
        """
        
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
            return {'error': 'Unauthorized'}
        
        # Optimized query with select_related and prefetch for all attendance data
        attendance_data = AttendanceLog.objects.filter(
            employee__in=employees,
            date__gte=start_date,
            date__lte=end_date
        ).select_related(
            'employee', 
            'employee__branch'
        ).order_by('employee__employee_id', '-date')
        
        # Use database aggregation for summary statistics instead of Python loops
        employee_summaries = AttendanceLog.objects.filter(
            employee__in=employees,
            date__gte=start_date,
            date__lte=end_date
        ).values(
            'employee__id', 
            'employee__employee_id',
            'employee__first_name',
            'employee__last_name',
            'employee__branch__name'
        ).annotate(
            total_days=Count('id'),
            present_days=Count('id', filter=Q(status='present')),
            late_days=Count('id', filter=Q(checkin_status__in=['late', 'very_late'])),
            absent_days=Count('id', filter=Q(status='absent')),
            total_hours=Sum('total_hours', filter=Q(status='present')),
            avg_hours=Avg('total_hours', filter=Q(status='present'))
        )
        
        # Organize data efficiently
        report_data = {}
        
        # Build employee summaries
        for emp_summary in employee_summaries:
            emp_id = emp_summary['employee__employee_id']
            report_data[emp_id] = {
                'employee': {
                    'id': emp_summary['employee__id'],
                    'employee_id': emp_summary['employee__employee_id'],
                    'name': f"{emp_summary['employee__first_name']} {emp_summary['employee__last_name']}",
                    'branch': emp_summary['employee__branch__name'],
                },
                'summary': {
                    'total_days': emp_summary['total_days'] or 0,
                    'present_days': emp_summary['present_days'] or 0,
                    'late_days': emp_summary['late_days'] or 0,
                    'absent_days': emp_summary['absent_days'] or 0,
                    'total_hours': float(emp_summary['total_hours']) if emp_summary['total_hours'] else 0.0,
                    'avg_hours': float(emp_summary['avg_hours']) if emp_summary['avg_hours'] else 0.0,
                },
                'attendance_records': []
            }
        
        # Add detailed attendance records
        for attendance in attendance_data:
            emp_id = attendance.employee.employee_id
            if emp_id in report_data:
                report_data[emp_id]['attendance_records'].append({
                    'date': attendance.date.isoformat(),
                    'check_in_time': attendance.check_in_time.isoformat() if attendance.check_in_time else None,
                    'check_out_time': attendance.check_out_time.isoformat() if attendance.check_out_time else None,
                    'status': attendance.status,
                    'checkin_status': attendance.checkin_status,
                    'total_hours': str(attendance.total_hours),
                    'needs_checkout_correction': attendance.needs_checkout_correction,
                })
        
        return {
            'report_data': list(report_data.values()),
            'total_employees': len(report_data),
            'date_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
        }


class AttendanceQueryService:
    """Optimized service for attendance queries"""
    
    @staticmethod
    def get_attendance_optimized(user, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimized attendance retrieval with proper select_related
        """
        
        # Base queryset with optimized joins
        base_queryset = AttendanceLog.objects.select_related(
            'employee', 
            'employee__branch',
            'employee__supervisor'
        ).prefetch_related('checkout_requests')
        
        # Apply role-based filtering
        if user.role == 'therapist':
            queryset = base_queryset.filter(employee=user)
        elif user.role == 'supervisor':
            queryset = base_queryset.filter(employee__branch=user.branch)
        elif user.role in ['hr', 'superadmin']:
            queryset = base_queryset.all()
        else:
            return {'error': 'Insufficient permissions'}
        
        # Apply date filters
        if filters.get('start_date'):
            queryset = queryset.filter(date__gte=filters['start_date'])
        if filters.get('end_date'):
            queryset = queryset.filter(date__lte=filters['end_date'])
        if filters.get('employee_id'):
            queryset = queryset.filter(employee__employee_id=filters['employee_id'])
        if filters.get('branch_id'):
            queryset = queryset.filter(employee__branch_id=filters['branch_id'])
        if filters.get('status'):
            queryset = queryset.filter(status=filters['status'])
        
        # Order and execute query
        queryset = queryset.order_by('-date')
        
        # Optimized serialization
        attendance_data = [
            {
                'id': log.id,
                'employee': {
                    'id': log.employee.id,
                    'name': f"{log.employee.first_name} {log.employee.last_name}",
                    'employee_id': log.employee.employee_id,
                    'branch': log.employee.branch.name if log.employee.branch else None,
                },
                'date': log.date.isoformat(),
                'check_in_time': log.check_in_time.isoformat() if log.check_in_time else None,
                'check_out_time': log.check_out_time.isoformat() if log.check_out_time else None,
                'status': log.status,
                'checkin_status': log.checkin_status,
                'total_hours': str(log.total_hours),
                'needs_checkout_correction': log.needs_checkout_correction,
            }
            for log in queryset
        ]
        
        return {
            'attendance_records': attendance_data,
            'total_records': len(attendance_data)
        }


class LeaveQueryService:
    """Optimized service for leave application queries"""
    
    @staticmethod
    def get_leave_applications_optimized(user, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimized leave applications retrieval
        """
        
        # Base queryset with optimized joins
        base_queryset = LeaveApplication.objects.select_related(
            'employee', 
            'employee__branch',
            'approved_by'
        )
        
        # Apply role-based filtering
        if user.role == 'therapist':
            queryset = base_queryset.filter(employee=user)
        elif user.role == 'supervisor':
            queryset = base_queryset.filter(employee__branch=user.branch)
        elif user.role in ['hr', 'superadmin']:
            queryset = base_queryset.all()
        else:
            return {'error': 'Unauthorized'}
        
        # Apply filters
        if filters.get('status'):
            queryset = queryset.filter(status=filters['status'])
        if filters.get('employee_id'):
            queryset = queryset.filter(employee__employee_id=filters['employee_id'])
        
        queryset = queryset.order_by('-applied_at')
        
        # Optimized serialization
        applications_data = [
            {
                'id': app.id,
                'employee': {
                    'id': app.employee.id,
                    'employee_id': app.employee.employee_id,
                    'name': f"{app.employee.first_name} {app.employee.last_name}",
                    'branch': app.employee.branch.name if app.employee.branch else None,
                },
                'leave_type': app.leave_type,
                'start_date': app.start_date.isoformat(),
                'end_date': app.end_date.isoformat(),
                'reason': app.reason,
                'status': app.status,
                'leave_days': app.leave_days,
                'applied_at': app.applied_at.isoformat(),
                'approved_by': {
                    'name': f"{app.approved_by.first_name} {app.approved_by.last_name}",
                    'employee_id': app.approved_by.employee_id
                } if app.approved_by else None,
                'approved_at': app.approved_at.isoformat() if app.approved_at else None,
            }
            for app in queryset
        ]
        
        return {
            'leave_applications': applications_data,
            'count': len(applications_data)
        }
