from django.db import models
from django.conf import settings
from accounts.models import KERALA_DISTRICTS, Place

class Student(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )
    full_name = models.CharField(max_length=255, blank=True)
    mobile = models.CharField(max_length=20, blank=True)
    college = models.CharField(max_length=255, blank=True)
    course = models.CharField(max_length=255, blank=True)
    semester = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    profile_photo = models.FileField(upload_to='profile_photos/', blank=True, null=True)
    district = models.CharField(max_length=50, choices=KERALA_DISTRICTS, blank=True)
    place = models.ForeignKey(Place, on_delete=models.SET_NULL, null=True, blank=True)

    # Profile fields
    skills = models.CharField(max_length=500, blank=True)
    education = models.TextField(blank=True)
    experience = models.TextField(blank=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    about_me = models.TextField(blank=True)

    # Verification fields
    college_id = models.FileField(upload_to='college_ids/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)

    def __str__(self):
        return self.full_name or self.user.username

    @property
    def unread_notifications_count(self):
        return self.notifications.filter(is_read=False).count()


class Notification(models.Model):


    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    message = models.TextField()

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.full_name} - {self.message[:50]}"