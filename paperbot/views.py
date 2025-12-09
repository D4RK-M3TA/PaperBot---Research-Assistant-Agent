"""
Root view for PaperBot API.
"""
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.conf import settings
import os


def health_check(request):
    """
    Lightweight health check endpoint that doesn't load any models.
    Used by Render to verify the service is running.
    """
    return JsonResponse({'status': 'ok', 'service': 'paperbot'})


def root(request):
    """
    Serve the frontend landing page.
    """
    frontend_dist = os.path.join(settings.BASE_DIR, 'frontend', 'dist')
    index_path = os.path.join(frontend_dist, 'index.html')
    
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Fix asset paths if needed (Vite builds with /assets/ prefix)
        return HttpResponse(content, content_type='text/html')
    else:
        # Fallback: Serve a nice landing page HTML
        return HttpResponse("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>PaperBot - Research Assistant</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #333;
                }
                .container {
                    background: white;
                    border-radius: 20px;
                    padding: 3rem;
                    max-width: 600px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    text-align: center;
                }
                h1 {
                    font-size: 2.5rem;
                    margin-bottom: 1rem;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                }
                .icon {
                    font-size: 4rem;
                    margin-bottom: 1rem;
                }
                p {
                    color: #666;
                    line-height: 1.6;
                    margin-bottom: 2rem;
                }
                .btn {
                    display: inline-block;
                    padding: 12px 24px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 600;
                    margin: 0.5rem;
                    transition: transform 0.2s;
                }
                .btn:hover {
                    transform: translateY(-2px);
                }
                .status {
                    margin-top: 2rem;
                    padding: 1rem;
                    background: #f0f0f0;
                    border-radius: 8px;
                    color: #666;
                    font-size: 0.9rem;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="icon">📚</div>
                <h1>PaperBot</h1>
                <h2 style="color: #667eea; margin-bottom: 1rem;">Research Assistant Agent</h2>
                <p>
                    Your intelligent research assistant for PDF document analysis, 
                    question answering, and multi-document summarization with AI-powered insights.
                </p>
                <div>
                    <a href="/api/" class="btn">View API</a>
                </div>
                <div class="status">
                    ⚠️ Frontend is being built. The full UI will be available shortly.
                </div>
            </div>
        </body>
        </html>
        """, content_type='text/html')
