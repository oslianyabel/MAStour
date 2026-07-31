from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView

from tours.admin_views import delete_image

admin.site.site_header = 'MAS tour — Administración'
admin.site.site_title = 'MAS tour Admin'
admin.site.index_title = 'Panel de gestión'

urlpatterns = [
    # Must be declared before the admin so it is not swallowed by its catch-all patterns.
    path('admin/tools/delete-image/', delete_image, name='admin_delete_image'),
    path('admin/', admin.site.urls),
    path(
        'favicon.ico',
        RedirectView.as_view(url=f'{settings.STATIC_URL}img/logo.png', permanent=True),
    ),
    path('', include('tours.urls')),
    path('chatbot/', include('chatbot.urls')),
]

if settings.DEBUG:
    from django.views.generic import TemplateView

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [path('404-preview/', TemplateView.as_view(template_name='404.html'))]
