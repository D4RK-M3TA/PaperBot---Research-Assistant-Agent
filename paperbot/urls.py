"""
URL configuration for PaperBot project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from .views import root
import os

urlpatterns = [
    path('', root, name='root'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('core.urls')),
    path('api/', include('api.urls')),
]

# Serve frontend static assets (JS, CSS from Vite build)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # In production, serve frontend assets
    frontend_dist = os.path.join(settings.BASE_DIR, 'frontend', 'dist')
    if os.path.exists(frontend_dist):
        urlpatterns += [
            re_path(r'^assets/(?P<path>.*)$', serve, {
                'document_root': os.path.join(frontend_dist, 'assets'),
            }),
        ]









