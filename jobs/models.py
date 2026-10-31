from django.db import models
from django.conf import settings


class Job(models.Model):

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        related_name='posted_jobs',
        limit_choices_to={'user_type': 'customer'}
    )

    job_title = models.CharField(max_length=255)

    description = models.TextField()

    location = models.CharField(max_length=255)

    required_skills = models.CharField(
        max_length=255,
        blank=True
    )

    work_date = models.DateField()

    work_duration = models.CharField(
        max_length=20,
        choices=[
            ('2 Hours', '2 Hours'),
            ('4 Hours', '4 Hours'),
            ('Half Day', 'Half Day'),
            ('Full Day', 'Full Day'),
            ('2 Days', '2 Days'),
            ('1 Week', '1 Week'),
            ('Custom', 'Custom'),
        ],
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    @property
    def is_expired(self):
        """Returns True if the job's work_date has already passed."""
        if not self.work_date:
            return False
        from datetime import date
        return self.work_date < date.today()

    @property
    def is_today(self):
        """Returns True if the job's work_date is today."""
        if not self.work_date:
            return False
        from datetime import date
        return self.work_date == date.today()

    @property
    def days_until_work(self):
        """Returns days difference from today: negative if passed, 0 if today, positive if upcoming."""
        if not self.work_date:
            return None
        from datetime import date
        return (self.work_date - date.today()).days

    def __str__(self):
        return self.job_title


class JobApplication(models.Model):

    STATUS = [
        ('Pending', 'Pending'),
        ('Shortlisted', 'Shortlisted'),
        ('Accepted', 'Accepted'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Completed', 'Completed'),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='job_applications',
        limit_choices_to={'user_type': 'student'}
    )

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='applications'
    )

    cover_message = models.TextField()

    availability = models.CharField(max_length=100)

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default='Pending'
    )

    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'job')

    def __str__(self):
        student_profile = getattr(self.student, 'student_profile', None)
        student_name = student_profile.full_name if (student_profile and student_profile.full_name) else self.student.username
        return f"{student_name} - {self.job.job_title}"