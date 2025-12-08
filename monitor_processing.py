#!/usr/bin/env python3
"""
Monitor document processing status and wait for indexing to complete.
"""
import os
import sys
import time
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'paperbot.settings')
os.environ.setdefault('USE_SQLITE', 'True')
django.setup()

from core.models import Document

def monitor_documents(max_wait_minutes=10, check_interval=10):
    """Monitor document processing status."""
    print("=" * 70)
    print("Document Processing Monitor")
    print("=" * 70)
    print()
    
    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60
    
    while True:
        documents = Document.objects.all()
        total = documents.count()
        indexed = documents.filter(status='indexed').count()
        processing = documents.filter(status__in=['processing', 'extracted', 'chunked', 'embedded']).count()
        failed = documents.filter(status='failed').count()
        uploaded = documents.filter(status='uploaded').count()
        
        print(f"\r[{time.strftime('%H:%M:%S')}] Total: {total} | Indexed: {indexed} | Processing: {processing} | Uploaded: {uploaded} | Failed: {failed}", end='', flush=True)
        
        # Check if all documents are indexed
        if indexed > 0 and processing == 0 and uploaded == 0:
            print("\n\n✅ All documents have been processed!")
            print(f"   Indexed documents: {indexed}")
            if failed > 0:
                print(f"   ⚠️  Failed documents: {failed}")
            return True
        
        # Check timeout
        elapsed = time.time() - start_time
        if elapsed > max_wait_seconds:
            print(f"\n\n⏱️  Timeout reached ({max_wait_minutes} minutes)")
            print(f"   Indexed: {indexed}/{total}")
            print(f"   Still processing: {processing}")
            return False
        
        time.sleep(check_interval)
    
    return False

if __name__ == "__main__":
    success = monitor_documents(max_wait_minutes=15, check_interval=5)
    sys.exit(0 if success else 1)
