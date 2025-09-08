from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from core.models import Branch

class CustomUser(AbstractUser):
    """Custom User model for the special needs center"""
    
    USER_ROLES = [
        ('therapist', 'Therapist'),
        ('supervisor', 'Supervisor'),
        ('hr', 'HR'),
        ('superadmin', 'Super Admin'),
    ]
    
    # Core fields
    employee_id = models.CharField(
        max_length=20, 
        unique=True,
        help_text="Unique employee identifier"
    )
    role = models.CharField(
        max_length=20, 
        choices=USER_ROLES, 
        default='therapist',
        help_text="User role in the system"
    )
    branch = models.ForeignKey(
        Branch, 
        on_delete=models.PROTECT,
        related_name='users',
        help_text="Branch assignment"
    )
    
    # Contact information
    mobile_number = models.CharField(
        max_length=15,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )],
        help_text="Contact mobile number"
    )
    
    # Attendance settings
    login_time = models.TimeField(
        default='09:30',
        help_text="Expected login time (HH:MM format)"
    )
    grace_time = models.IntegerField(
        default=10,
        help_text="Grace time in minutes after login_time"
    )
    
    # Verification
    is_verified = models.BooleanField(
        default=False,
        help_text="Email verification status"
    )
    verification_token = models.CharField(
        max_length=255, 
        blank=True,
        help_text="Token for email verification"
    )
    
    # Hierarchy (for therapists)
    supervisor = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'supervisor'},
        related_name='supervised_therapists',
        help_text="Assigned supervisor (for therapists only)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ['branch', 'role', 'employee_id']
        indexes = [
            models.Index(fields=['branch', 'role']),     # Role-based queries
            models.Index(fields=['employee_id']),        # Employee lookups
            models.Index(fields=['role']),               # Role filtering
        ]
    
    def __str__(self):
        return f"{self.employee_id} - {self.get_full_name()} ({self.get_role_display()})"
    
    def save(self, *args, **kwargs):
        # Auto-assign supervisor for therapists based on branch
        if self.role == 'therapist' and not self.supervisor:
            branch_supervisor = CustomUser.objects.filter(
                role='supervisor', 
                branch=self.branch
            ).first()
            if branch_supervisor:
                self.supervisor = branch_supervisor
        
        super().save(*args, **kwargs)
    
    @property
    def full_name(self):
        """Return full name"""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def branch_name(self):
        """Return branch name"""
        return self.branch.get_name_display() if self.branch else "No Branch"
    
    def can_manage_user(self, target_user):
        """Check if current user can manage target user"""
        if self.role == 'superadmin':
            return True
        elif self.role == 'hr':
            return target_user.branch == self.branch
        elif self.role == 'supervisor':
            return (target_user.branch == self.branch and 
                   target_user.role == 'therapist' and
                   target_user.supervisor == self)
        return False
    
    def can_view_attendance(self, target_user):
        """Check if current user can view target user's attendance"""
        if self.role == 'superadmin':
            return True
        elif self.role in ['hr', 'supervisor']:
            return target_user.branch == self.branch
        elif self.role == 'therapist':
            return self == target_user
        return False
