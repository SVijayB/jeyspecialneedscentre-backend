from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # Display fields in the admin list view
    list_display = ['username', 'employee_id', 'first_name', 'last_name', 'role', 'branch', 'is_active', 'is_verified']
    list_filter = ['role', 'branch', 'is_active', 'is_verified', 'date_joined']
    search_fields = ['username', 'employee_id', 'first_name', 'last_name', 'email']
    ordering = ['username']
    
    # Simplified fieldsets without permission management
    fieldsets = (
        ('Basic Information', {
            'fields': ('username', 'password', 'first_name', 'last_name', 'email')
        }),
        ('Employee Information', {
            'fields': ('employee_id', 'role', 'mobile_number', 'branch', 'supervisor')
        }),
        ('Work Schedule', {
            'fields': ('login_time', 'grace_time')
        }),
        ('Account Status', {
            'fields': ('is_active', 'is_staff', 'is_verified')
        }),
        ('Verification', {
            'fields': ('verification_token',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('date_joined', 'last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Fields to display when adding a new user
    add_fieldsets = (
        ('Basic Information', {
            'fields': ('username', 'password1', 'password2', 'first_name', 'last_name', 'email')
        }),
        ('Employee Information', {
            'fields': ('employee_id', 'role', 'mobile_number', 'branch', 'supervisor')
        }),
        ('Work Schedule', {
            'fields': ('login_time', 'grace_time')
        }),
        ('Account Status', {
            'fields': ('is_active', 'is_staff')
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login', 'created_at', 'updated_at']
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('branch', 'supervisor')
