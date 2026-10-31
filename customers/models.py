from django.db import models
from django.conf import settings


class Customer(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='customer_profile'
    )
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    mobile_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    password = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name or (self.user.username if self.user else "Customer")


class WorkCompletion(models.Model):
    application = models.ForeignKey(
        'jobs.JobApplication',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='work_completions'
    )
    job = models.ForeignKey(
        'jobs.Job',
        on_delete=models.CASCADE,
        related_name='work_completions'
    )
    completion_date = models.DateField()
    work_status = models.CharField(
        max_length=30,
        choices=[
            ('Completed', 'Completed'),
            ('Partially Completed', 'Partially Completed'),
            ('Not Completed', 'Not Completed'),
        ]
    )
    remarks = models.TextField(blank=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='completed_works'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.job.job_title} - {self.work_status}"


class Review(models.Model):
    application = models.ForeignKey(
        'jobs.JobApplication',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reviews'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_reviews',
        limit_choices_to={'user_type': 'student'}
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='given_reviews',
        limit_choices_to={'user_type': 'customer'}
    )
    job = models.ForeignKey(
        'jobs.Job',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    rating = models.PositiveSmallIntegerField()
    review_comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        student_profile = getattr(self.student, 'student_profile', None)
        student_name = student_profile.full_name if (student_profile and student_profile.full_name) else self.student.username
        return f"{student_name} - {self.rating}⭐"