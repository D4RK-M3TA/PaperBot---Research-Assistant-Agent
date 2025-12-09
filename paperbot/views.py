"""
Root view for PaperBot API.
"""
from django.http import JsonResponse


def root(request):
    """
    Root endpoint that returns API information.
    """
    return JsonResponse({
        'name': 'PaperBot API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'admin': '/admin/',
            'api': '/api/',
            'auth': '/api/auth/',
            'documents': '/api/documents/',
            'query': '/api/query/',
            'summarize': '/api/summarize/',
            'chat': '/api/chat/',
        }
    })
