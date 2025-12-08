"""
URLs for API app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet, ChatSessionViewSet, query, summarize

router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'chat', ChatSessionViewSet, basename='chat')

urlpatterns = [
    path('query/', query, name='query'),
    path('summarize/', summarize, name='summarize'),
    path('', include(router.urls)),
]





