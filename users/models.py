"""
User models for the surveillance system.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User model with role-based permissions.
    """
    class Role(models.TextChoices):
        ADMIN = 'admin', _('Administrator')
        INSTRUCTOR = 'instructor', _('Instructor')
        STUDENT = 'student', _('Student')
        MONITOR = 'monitor', _('Monitor')

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        help_text=_('User role in the system')
    )
    
    email = models.EmailField(
        unique=True,
        help_text=_('User email address')
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text=_('Designates whether this user should be treated as active.')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Profile fields
    phone_number = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    student_id = models.CharField(max_length=50, blank=True)
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_instructor(self):
        return self.role == self.Role.INSTRUCTOR

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_monitor(self):
        return self.role == self.Role.MONITOR

    def can_view_violations(self):
        """Check if user can view violations."""
        return self.role in [self.Role.ADMIN, self.Role.INSTRUCTOR, self.Role.MONITOR]

    def can_manage_users(self):
        """Check if user can manage other users."""
        return self.role in [self.Role.ADMIN, self.Role.INSTRUCTOR]

    def can_view_analytics(self):
        """Check if user can view analytics."""
        return self.role in [self.Role.ADMIN, self.Role.INSTRUCTOR, self.Role.MONITOR] 