"""
URL configuration for PaperBot project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from . import views
import os

urlpatterns = [
    path('health/', views.health_check, name='health'),
    path('', views.root, name='root'),
    # Admin is protected by Django's authentication - only staff/superuser can access
    path('admin/', admin.site.urls),
    path('api/auth/', include('core.urls')),
    path('api/', include('api.urls')),
]

# Customize admin site headers for security
admin.site.site_header = "PaperBot Administration"
admin.site.site_title = "PaperBot Admin"
admin.site.index_title = "Welcome to PaperBot Administration"

# Serve frontend static assets (JS, CSS from Vite build)
frontend_dist = os.path.join(settings.BASE_DIR, 'frontend', 'dist')
frontend_assets = os.path.join(frontend_dist, 'assets')

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # In development, serve frontend assets directly
    if os.path.exists(frontend_assets):
        urlpatterns += [
            re_path(r'^assets/(?P<path>.*)$', serve, {
                'document_root': frontend_assets,
            }),
        ]
else:
    # In production, serve frontend assets
    if os.path.exists(frontend_assets):
        urlpatterns += [
            re_path(r'^assets/(?P<path>.*)$', serve, {
                'document_root': frontend_assets,
            }),
        ]









