from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = 'MAS tour — Administración'
admin.site.site_title = 'MAS tour Admin'
admin.site.index_title = 'Panel de gestión'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tours.urls')),
    path('chatbot/', include('chatbot.urls')),
]

if settings.DEBUG:
    from django.views.generic import TemplateView

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [path('404-preview/', TemplateView.as_view(template_name='404.html'))]
