from django.test import TestCase
from django.urls import reverse
from accounts.models import CustomUser
from students.models import Student, Notification


class NotificationTests(TestCase):
    def setUp(self):
        # Create student 1
        self.user1 = CustomUser.objects.create_user(
            username='student1',
            email='student1@example.com',
            password='password123',
            user_type='student'
        )
        self.student1 = Student.objects.create(
            user=self.user1,
            full_name='Student One'
        )

        # Create student 2
        self.user2 = CustomUser.objects.create_user(
            username='student2',
            email='student2@example.com',
            password='password123',
            user_type='student'
        )
        self.student2 = Student.objects.create(
            user=self.user2,
            full_name='Student Two'
        )

        # Create notifications for student 1
        self.notif_read = Notification.objects.create(
            student=self.student1,
            message='Read Notification',
            is_read=True
        )
        self.notif_unread = Notification.objects.create(
            student=self.student1,
            message='Unread Notification',
            is_read=False
        )

    def test_anonymous_user_redirected_to_login(self):
        response = self.client.get(reverse('notifications'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_notifications_page_loads_for_student(self):
        self.client.login(username='student1', password='password123')
        response = self.client.get(reverse('notifications'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'students/notifications.html')
        # Check that notifications are passed to context
        self.assertIn('notifications', response.context)
        self.assertEqual(len(response.context['notifications']), 2)

    def test_unread_notifications_marked_as_read_on_view(self):
        # Double check initially database state
        self.assertFalse(self.notif_unread.is_read)

        # View notifications page
        self.client.login(username='student1', password='password123')
        response = self.client.get(reverse('notifications'))
        self.assertEqual(response.status_code, 200)

        # Verify that they are marked read in db
        self.notif_unread.refresh_from_db()
        self.assertTrue(self.notif_unread.is_read)

        # Verify in memory that the context has the list before marking read so badge/status can be displayed
        context_notifs = response.context['notifications']
        unread_in_context = [n for n in context_notifs if n.message == 'Unread Notification'][0]
        self.assertFalse(unread_in_context.is_read)

    def test_notifications_isolation_between_students(self):
        # View notifications page as Student Two (should see 0 notifications)
        self.client.login(username='student2', password='password123')
        response = self.client.get(reverse('notifications'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['notifications']), 0)

