"""
Root view for PaperBot API.
"""
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
import os


def root(request):
    """
    Serve the frontend landing page.
    """
    frontend_dist = os.path.join(settings.BASE_DIR, 'frontend', 'dist')
    index_path = os.path.join(frontend_dist, 'index.html')
    
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='text/html')
    else:
        # Fallback if frontend not built
        return HttpResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>PaperBot - Research Assistant</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                h1 { color: #333; }
                p { color: #666; }
            </style>
        </head>
        <body>
            <h1>PaperBot API</h1>
            <p>Frontend is being built. Please wait...</p>
            <p><a href="/api/">API Endpoints</a> | <a href="/admin/">Admin</a></p>
        </body>
        </html>
        """, content_type='text/html')
