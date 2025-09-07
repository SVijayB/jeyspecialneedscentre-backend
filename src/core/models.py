from django.db import models

class Branch(models.Model):
    """Branch model for different locations"""
    
    name = models.CharField(
        max_length=50, 
        unique=True,
        help_text="Branch location (e.g., Chennai, Bengaluru, Mumbai, etc.)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Branch"
        verbose_name_plural = "Branches"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def active_users_count(self):
        """Return count of active users in this branch"""
        return self.users.filter(is_active=True).count()
    
    @property
    def therapists_count(self):
        """Return count of therapists in this branch"""
        return self.users.filter(role='therapist', is_active=True).count()
