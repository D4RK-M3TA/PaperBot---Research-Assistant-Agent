"""
Middleware for audit logging.
"""
import json
from django.utils import timezone
from .models import AuditLog


class AuditLogMiddleware:
    """Middleware to log all API requests."""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Log authenticated requests
        if request.user.is_authenticated:
            action = self._get_action(request.path, request.method)
            if action:
                AuditLog.objects.create(
                    user=request.user,
                    action=action,
                    resource_type=self._get_resource_type(request.path),
                    ip_address=self._get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                    metadata={
                        'path': request.path,
                        'method': request.method,
                    }
                )
        
        return response

    def _get_action(self, path, method):
        """Map path and method to action type."""
        if '/documents' in path and method == 'POST':
            return 'document_upload'
        elif '/documents' in path and method == 'DELETE':
            return 'document_delete'
        elif '/query' in path:
            return 'query'
        elif '/summarize' in path:
            return 'summarize'
        elif '/chat' in path:
            return 'chat'
        elif '/workspaces' in path and method == 'POST':
            return 'workspace_create'
        elif '/workspaces' in path and method == 'DELETE':
            return 'workspace_delete'
        return None

    def _get_resource_type(self, path):
        """Extract resource type from path."""
        if '/documents' in path:
            return 'document'
        elif '/workspaces' in path:
            return 'workspace'
        return ''

    def _get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

