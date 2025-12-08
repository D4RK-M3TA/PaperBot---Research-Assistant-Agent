"""
URLs for core app (auth and workspaces).
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import UserViewSet, WorkspaceViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'workspaces', WorkspaceViewSet, basename='workspace')

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
]

