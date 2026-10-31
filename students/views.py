from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from .models import Student, Notification


@login_required
def notifications(request):
    if request.user.user_type != 'student' and not (request.user.is_staff or request.user.is_superuser):
        return redirect('home')

    student, _ = Student.objects.get_or_create(user=request.user)

    # Fetch notification list snapshot (preserving original read/unread state for UI presentation)
    notification_list = list(Notification.objects.filter(student=student).order_by('-created_at'))

    # Mark all unread notifications as read in the database
    Notification.objects.filter(student=student, is_read=False).update(is_read=True)

    return render(
        request,
        'students/notifications.html',
        {
            'notifications': notification_list,
            'student_profile': student
        }
    )