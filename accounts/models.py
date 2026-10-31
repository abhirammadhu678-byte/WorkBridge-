from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.conf import settings


class CustomUserManager(UserManager):
    def create_user(self, username=None, email=None, password=None, **extra_fields):
        extra_fields.setdefault('user_type', 'student')

        if extra_fields.get('is_staff') or extra_fields.get('is_superuser') or extra_fields.get('user_type') == 'admin':
            extra_fields['user_type'] = 'admin'
            extra_fields.setdefault('is_staff', True)

        return super().create_user(username, email, password, **extra_fields)

    def create_superuser(self, username=None, email=None, password=None, **extra_fields):
        extra_fields.setdefault('user_type', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)

KERALA_DISTRICTS = [
    ('Alappuzha', 'Alappuzha'),
    ('Ernakulam', 'Ernakulam'),
    ('Idukki', 'Idukki'),
    ('Kannur', 'Kannur'),
    ('Kasaragod', 'Kasaragod'),
    ('Kollam', 'Kollam'),
    ('Kottayam', 'Kottayam'),
    ('Kozhikode', 'Kozhikode'),
    ('Malappuram', 'Malappuram'),
    ('Palakkad', 'Palakkad'),
    ('Pathanamthitta', 'Pathanamthitta'),
    ('Thiruvananthapuram', 'Thiruvananthapuram'),
    ('Thrissur', 'Thrissur'),
    ('Wayanad', 'Wayanad'),
]


class Place(models.Model):
    name = models.CharField(max_length=255)
    district = models.CharField(max_length=50, choices=KERALA_DISTRICTS)

    class Meta:
        unique_together = ('name', 'district')
        ordering = ['district', 'name']

    def __str__(self):
        return f"{self.name}, {self.district}"


class CustomUser(AbstractUser):
    USER_TYPE = (
        ('student', 'Student'),
        ('customer', 'Customer'),
        ('admin', 'Admin'),
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPE, default='student')
    objects = CustomUserManager()


# accounts/models.py


class Portfolio(models.Model):
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='portfolios'
    )

    work_title = models.CharField(max_length=200)
    description = models.TextField()

    photo = models.ImageField(
        upload_to='portfolio/photos/',
        blank=True,
        null=True
    )

    reel = models.FileField(
        upload_to='portfolio/reels/',
        blank=True,
        null=True
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.work_title


class Report(models.Model):
    REPORT_TYPES = [
        ('student', 'Student Profile'),
        ('customer', 'Customer Profile'),
        ('job', 'Job Posting'),
        ('application', 'Job Application'),
        ('review', 'Review / Rating'),
        ('general', 'General Platform Issue'),
    ]

    REASON_CHOICES = [
        ('spam', 'Spam or Advertising'),
        ('fraud', 'Scam, Fraud or Fake Information'),
        ('inappropriate', 'Inappropriate or Offensive Content'),
        ('harassment', 'Harassment or Abusive Behavior'),
        ('dispute', 'Work or Payment Dispute'),
        ('fake_id', 'Fake or Misleading College ID'),
        ('other', 'Other Issue'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending Review'),
        ('Investigating', 'Under Investigation'),
        ('Resolved', 'Resolved'),
        ('Dismissed', 'Dismissed'),
    ]

    ACTION_CHOICES = [
        ('None', 'No Action Needed'),
        ('Warning Sent', 'Warning Sent to User'),
        ('User Deactivated', 'User Account Deactivated'),
        ('Job Removed', 'Job Posting Removed'),
        ('Review Removed', 'Review Removed'),
        ('Dismissed', 'Dismissed as Invalid'),
    ]

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submitted_reports'
    )
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES, default='general')
    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reports_received'
    )
    reported_job = models.ForeignKey(
        'jobs.Job',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reports'
    )
    reported_review = models.ForeignKey(
        'customers.Review',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reports'
    )
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    admin_notes = models.TextField(blank=True)
    action_taken = models.CharField(max_length=50, choices=ACTION_CHOICES, blank=True, default='None')
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='resolved_reports'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Report #{self.id} ({self.get_report_type_display()}) - {self.get_reason_display()}"