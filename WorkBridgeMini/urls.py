from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('customers/', include('customers.urls')),
    path('jobs/', include('jobs.urls')),
    path(
        'students/',
        include('students.urls')
    ),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'accounts.views.custom_page_not_found_view'
handler403 = 'accounts.views.custom_permission_denied_view'
handler500 = 'accounts.views.custom_server_error_view'