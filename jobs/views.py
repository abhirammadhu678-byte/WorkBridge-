from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from .models import Job, JobApplication
from .forms import JobPostForm, JobApplicationForm
from customers.models import Review


def job_application(request):
    jobs = Job.objects.all().order_by('-id')
    return render(
        request,
        'jobs/job_application.html',
        {
            'jobs': jobs
        }
    )


@login_required
def job_post(request):
    if request.user.user_type != 'customer' and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Only employers/customers can post jobs.")
        return redirect('student_dashboard')

    if request.method == "POST":
        form = JobPostForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.customer = request.user
            job.save()
            messages.success(request, f"Job '{job.job_title}' posted successfully!")
            return redirect('customer_dashboard')
    else:
        form = JobPostForm()

    return render(
        request,
        'jobs/job_post.html',
        {
            'form': form
        }
    )


# =========================================================
# AVAILABLE JOBS (SEARCH & FILTERS)
# =========================================================

def available_jobs(request):
    from datetime import date
    today = date.today()

    jobs_qs = Job.objects.select_related('customer').all().order_by('-created_at')

    # Get distinct options for filter dropdowns / chips
    distinct_locations = sorted(list(set(filter(None, Job.objects.values_list('location', flat=True)))))
    distinct_durations = [
        '2 Hours', '4 Hours', 'Half Day', 'Full Day', '2 Days', '1 Week', 'Custom'
    ]

    # Search query
    q = request.GET.get('q', '').strip()
    if q:
        jobs_qs = jobs_qs.filter(
            Q(job_title__icontains=q) |
            Q(description__icontains=q) |
            Q(required_skills__icontains=q) |
            Q(location__icontains=q)
        )

    # Location filter
    selected_location = request.GET.get('location', '').strip()
    if selected_location and selected_location != 'all':
        jobs_qs = jobs_qs.filter(location__iexact=selected_location)

    # Duration filter
    selected_duration = request.GET.get('duration', '').strip()
    if selected_duration and selected_duration != 'all':
        jobs_qs = jobs_qs.filter(work_duration__iexact=selected_duration)

    # Skill filter
    selected_skill = request.GET.get('skill', '').strip()
    if selected_skill:
        jobs_qs = jobs_qs.filter(required_skills__icontains=selected_skill)

    # Date status filter (all, upcoming, expired)
    date_status = request.GET.get('date_status', 'all').strip()
    if date_status == 'upcoming':
        jobs_qs = jobs_qs.filter(work_date__gte=today)
    elif date_status == 'expired':
        jobs_qs = jobs_qs.filter(work_date__lt=today)

    # Map of user's applications
    applied_status_map = {}
    if request.user.is_authenticated and request.user.user_type == 'student':
        user_apps = JobApplication.objects.filter(student=request.user)
        for app in user_apps:
            applied_status_map[app.job_id] = app.status

    jobs_list = list(jobs_qs)
    # Sort upcoming jobs first, then past/expired jobs
    jobs_list.sort(key=lambda j: (j.is_expired, j.work_date if j.work_date else today))

    for j in jobs_list:
        j.applied_status = applied_status_map.get(j.id)

    total_jobs_count = len(jobs_list)
    upcoming_count = sum(1 for j in jobs_list if not j.is_expired)
    expired_count = sum(1 for j in jobs_list if j.is_expired)

    return render(
        request,
        "jobs/available_jobs.html",
        {
            "jobs": jobs_list,
            "total_jobs_count": total_jobs_count,
            "upcoming_count": upcoming_count,
            "expired_count": expired_count,
            "applied_status_map": applied_status_map,
            "distinct_locations": distinct_locations,
            "distinct_durations": distinct_durations,
            "search_query": q,
            "selected_location": selected_location,
            "selected_duration": selected_duration,
            "selected_skill": selected_skill,
            "date_status": date_status,
            "today": today,
        }
    )


# =========================================================
# APPLIED JOBS (APPLICATION STATUS & TRACKING)
# =========================================================

@login_required
def applied_jobs(request):
    if request.user.user_type != 'student' and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Access restricted to student accounts.")
        return redirect('customer_dashboard' if request.user.user_type == 'customer' else 'home')

    apps_qs = JobApplication.objects.filter(
        student=request.user
    ).select_related("job", "job__customer").order_by('-applied_at')

    # Status counts for tabs
    total_count = apps_qs.count()
    pending_count = apps_qs.filter(status='Pending').count()
    shortlisted_count = apps_qs.filter(status='Shortlisted').count()
    accepted_count = apps_qs.filter(status='Accepted').count()
    completed_count = apps_qs.filter(status='Completed').count()
    rejected_count = apps_qs.filter(status='Rejected').count()

    # Filter by status
    status_filter = request.GET.get('status', 'all').strip()
    if status_filter and status_filter != 'all':
        apps_qs = apps_qs.filter(status__iexact=status_filter)

    # Attach reviews for completed applications
    applications_with_reviews = []
    for app in apps_qs:
        review = None
        if app.status == 'Completed':
            review = Review.objects.filter(application=app).first()
        applications_with_reviews.append({
            'application': app,
            'review': review
        })

    return render(
        request,
        "jobs/applied_jobs.html",
        {
            "applications_with_reviews": applications_with_reviews,
            "status_filter": status_filter,
            "total_count": total_count,
            "pending_count": pending_count,
            "shortlisted_count": shortlisted_count,
            "accepted_count": accepted_count,
            "completed_count": completed_count,
            "rejected_count": rejected_count,
        }
    )


# =========================================================
# APPLY FOR A JOB
# =========================================================

@login_required
def apply_job(request, job_id):
    if request.user.user_type != 'student':
        messages.error(request, "Only student accounts can apply for jobs.")
        return redirect('available_jobs')

    job = get_object_or_404(Job.objects.select_related('customer'), id=job_id)

    # Check if student already applied
    existing_application = JobApplication.objects.filter(
        student=request.user,
        job=job
    ).first()

    if existing_application:
        messages.info(request, f"You have already applied for this job. Current status: '{existing_application.status}'.")
        return redirect("applied_jobs")

    # Check if job work date has passed
    if job.is_expired:
        messages.error(request, f"Applications are closed: The scheduled work date for '{job.job_title}' ({job.work_date.strftime('%b %d, %Y')}) has already passed.")
        return redirect("available_jobs")

    if request.method == "POST":
        form = JobApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.student = request.user
            application.job = job
            application.status = 'Pending'
            application.save()
            messages.success(request, f"Application for '{job.job_title}' submitted successfully!")
            return redirect("applied_jobs")
        else:
            messages.error(request, "Please fix the errors in your application form below.")
    else:
        form = JobApplicationForm()

    return render(
        request,
        "jobs/apply_job.html",
        {
            "form": form,
            "job": job
        }
    )