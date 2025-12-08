#!/usr/bin/env python3
"""
Test Query and Summarization endpoints after documents are indexed.
"""
import os
import sys
import django
import requests
import json

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'paperbot.settings')
os.environ.setdefault('USE_SQLITE', 'True')
django.setup()

from core.models import Document, Workspace
from django.contrib.auth import get_user_model

User = get_user_model()

API_BASE = "http://localhost:8000/api"
AUTH_BASE = "http://localhost:8000/api/auth"

def get_auth_token():
    """Get authentication token."""
    try:
        # Try to login as admin
        response = requests.post(
            f"{AUTH_BASE}/token/",
            json={"username": "admin", "password": "admin123"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("access")
    except:
        pass
    return None

def test_query(workspace_id, token):
    """Test query endpoint."""
    print("\n" + "=" * 70)
    print("Testing Query Endpoint")
    print("=" * 70)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    test_queries = [
        "What is this document about?",
        "What is the main topic?",
        "Summarize the content"
    ]
    
    for query_text in test_queries:
        try:
            print(f"\nQuery: {query_text}")
            response = requests.post(
                f"{API_BASE}/query/",
                json={
                    "workspace_id": workspace_id,
                    "query": query_text,
                    "top_k": 5
                },
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get("answer", "")
                citations = result.get("citations", [])
                print(f"✅ SUCCESS")
                print(f"   Answer length: {len(answer)} characters")
                print(f"   Citations: {len(citations)}")
                if answer:
                    print(f"   Answer preview: {answer[:200]}...")
                if citations:
                    print(f"   First citation: {citations[0].get('document_title', 'N/A')}")
                return True
            elif response.status_code == 404:
                print(f"⚠️  No relevant documents found")
                print(f"   Response: {response.text}")
            else:
                print(f"❌ FAILED - Status {response.status_code}")
                print(f"   Response: {response.text[:500]}")
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
    
    return False

def test_summarize(workspace_id, document_ids, token):
    """Test summarization endpoint."""
    print("\n" + "=" * 70)
    print("Testing Summarization Endpoint")
    print("=" * 70)
    
    if not document_ids:
        print("❌ No indexed documents available for summarization")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    summary_types = ["short", "detailed", "related_work"]
    
    for summary_type in summary_types:
        try:
            print(f"\nSummary Type: {summary_type}")
            response = requests.post(
                f"{API_BASE}/summarize/",
                json={
                    "workspace_id": workspace_id,
                    "document_ids": document_ids,
                    "summary_type": summary_type
                },
                headers=headers,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                summary = result.get("summary", "")
                related_work = result.get("related_work")
                citations = result.get("citations", [])
                print(f"✅ SUCCESS")
                print(f"   Summary length: {len(summary)} characters")
                if summary:
                    print(f"   Summary preview: {summary[:200]}...")
                if related_work:
                    print(f"   Related work length: {len(related_work)} characters")
                print(f"   Citations: {len(citations)}")
                return True
            elif response.status_code == 404:
                print(f"⚠️  No valid indexed documents found")
                print(f"   Response: {response.text}")
            else:
                print(f"❌ FAILED - Status {response.status_code}")
                print(f"   Response: {response.text[:500]}")
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
    
    return False

def main():
    """Main test function."""
    print("=" * 70)
    print("Query and Summarization Re-Testing")
    print("=" * 70)
    
    # Check if backend is running
    try:
        response = requests.get("http://localhost:8000/admin/", timeout=5)
    except:
        print("\n❌ Backend server is not running!")
        print("Please start the backend server first:")
        print("  python manage.py runserver")
        sys.exit(1)
    
    # Get auth token
    print("\nAuthenticating...")
    token = get_auth_token()
    if not token:
        print("❌ Failed to authenticate")
        sys.exit(1)
    print("✅ Authenticated")
    
    # Get workspace and documents
    user = User.objects.filter(username="admin").first()
    if not user:
        print("❌ Admin user not found")
        sys.exit(1)
    
    # Find workspace with indexed documents
    indexed_docs = Document.objects.filter(status='indexed', workspace__owner=user)
    if indexed_docs.exists():
        workspace = indexed_docs.first().workspace
    else:
        workspace = Workspace.objects.filter(owner=user).first()
    
    if not workspace:
        print("❌ No workspace found")
        sys.exit(1)
    
    print(f"\nWorkspace: {workspace.name} (ID: {workspace.id})")
    
    # Check document status
    documents = Document.objects.filter(workspace=workspace)
    indexed_docs = documents.filter(status='indexed')
    processing_docs = documents.filter(status__in=['processing', 'extracted', 'chunked', 'embedded'])
    
    print(f"\nDocument Status:")
    print(f"  Total: {documents.count()}")
    print(f"  Indexed: {indexed_docs.count()}")
    print(f"  Processing: {processing_docs.count()}")
    
    if indexed_docs.count() == 0:
        print("\n⚠️  No indexed documents found!")
        print("   Documents may still be processing. Please wait and try again.")
        print(f"   Processing documents: {processing_docs.count()}")
        sys.exit(1)
    
    document_ids = list(indexed_docs.values_list('id', flat=True))
    print(f"  Using document IDs: {document_ids}")
    
    # Test Query
    query_success = test_query(workspace.id, token)
    
    # Test Summarization
    summarize_success = test_summarize(workspace.id, document_ids, token)
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Query Test: {'✅ PASSED' if query_success else '❌ FAILED'}")
    print(f"Summarization Test: {'✅ PASSED' if summarize_success else '❌ FAILED'}")
    
    if query_success and summarize_success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed or returned warnings")
        sys.exit(1)

if __name__ == "__main__":
    main()

