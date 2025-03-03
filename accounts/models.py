from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    
    full_name = models.CharField(max_length=150, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_employee = models.BooleanField(default=False)
    is_hr = models.BooleanField(default=False)
    POSITION_CHOICES = [
        ('Specialist', 'Specialist'),
        ('Project Manager', 'Project Manager'),
        ('Software Designer', 'Software Designer'),
    ]
    position = models.CharField(max_length=50, choices=POSITION_CHOICES, blank=True)

    def __str__(self):
        return self.username



class LeaveRequest(models.Model):
    LEAVE_TYPES = [
        ('Casual Leave', 'Casual Leave'),
        ('Medical Leave', 'Medical Leave'),
        ('Earned Leave', 'Earned Leave (EL) or Privileged Leave (PL)'),
        ('Leave Without Pay', 'Leave Without Pay (LWP)'),
    ]

    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    hr = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='hr_leave_requests')
    start_date = models.DateField()
    end_date = models.DateField()
    leave_type = models.CharField(max_length=30, choices=LEAVE_TYPES)
    description = models.TextField(null=True, blank=True)
    is_approved = models.BooleanField(null=True)
    approved_by = models.ForeignKey(User, null=True, blank=True, related_name='approved_by', on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.employee.username} - {self.start_date} to {self.end_date}"