#!/usr/bin/env python3
"""
Comprehensive test script for PaperBot components.
Tests all functionality: authentication, workspaces, file uploads, queries, chat, and summarization.
"""

import requests
import json
import time
import os
import sys
from pathlib import Path

# Configuration
API_BASE = "http://localhost:8000/api"
AUTH_BASE = "http://localhost:8000/api/auth"

# Test results
test_results = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def log_test(name, status, message=""):
    """Log test result."""
    if status == "PASS":
        test_results["passed"].append(f"✅ {name}: {message}")
        print(f"✅ {name}: {message}")
    elif status == "FAIL":
        test_results["failed"].append(f"❌ {name}: {message}")
        print(f"❌ {name}: {message}")
    elif status == "WARN":
        test_results["warnings"].append(f"⚠️  {name}: {message}")
        print(f"⚠️  {name}: {message}")

def check_server():
    """Check if servers are running."""
    try:
        response = requests.get(f"{API_BASE.replace('/api', '')}/admin/", timeout=5)
        log_test("Backend Server", "PASS", "Backend is running")
        return True
    except requests.exceptions.RequestException:
        log_test("Backend Server", "FAIL", "Backend is not running. Please start it first.")
        return False

class TestClient:
    """Test client for API testing."""
    
    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.user = None
        self.workspace_id = None
        self.document_ids = []
        self.chat_session_id = None
    
    def register(self, username="testuser", email="test@example.com", password="testpass123"):
        """Test user registration."""
        try:
            response = requests.post(
                f"{AUTH_BASE}/users/register/",
                json={
                    "username": username,
                    "email": email,
                    "password": password,
                    "password_confirm": password
                },
                timeout=10
            )
            if response.status_code == 201:
                data = response.json()
                self.access_token = data.get("access")
                self.refresh_token = data.get("refresh")
                self.user = data.get("user")
                log_test("User Registration", "PASS", f"User '{username}' registered successfully")
                return True
            else:
                log_test("User Registration", "FAIL", f"Status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            log_test("User Registration", "FAIL", str(e))
            return False
    
    def login(self, username="admin", password="admin123"):
        """Test user login."""
        try:
            response = requests.post(
                f"{AUTH_BASE}/token/",
                json={"username": username, "password": password},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access")
                self.refresh_token = data.get("refresh")
                log_test("User Login", "PASS", f"User '{username}' logged in successfully")
                return True
            else:
                log_test("User Login", "FAIL", f"Status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            log_test("User Login", "FAIL", str(e))
            return False
    
    def get_headers(self):
        """Get request headers with auth token."""
        if not self.access_token:
            return {}
        return {"Authorization": f"Bearer {self.access_token}"}
    
    def get_current_user(self):
        """Get current user info."""
        try:
            response = requests.get(
                f"{AUTH_BASE}/users/me/",
                headers=self.get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                self.user = response.json()
                log_test("Get Current User", "PASS", f"Retrieved user: {self.user.get('username')}")
                return True
            else:
                log_test("Get Current User", "FAIL", f"Status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            log_test("Get Current User", "FAIL", str(e))
            return False
    
    def create_workspace(self, name="Test Workspace", description="Test workspace for testing"):
        """Test workspace creation."""
        try:
            response = requests.post(
                f"{AUTH_BASE}/workspaces/",
                json={"name": name, "description": description},
                headers=self.get_headers(),
                timeout=10
            )
            if response.status_code == 201:
                workspace = response.json()
                self.workspace_id = workspace.get("id")
                log_test("Create Workspace", "PASS", f"Workspace '{name}' created (ID: {self.workspace_id})")
                return True
            else:
                log_test("Create Workspace", "FAIL", f"Status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            log_test("Create Workspace", "FAIL", str(e))
            return False
    
    def list_workspaces(self):
        """Test listing workspaces."""
        try:
            response = requests.get(
                f"{AUTH_BASE}/workspaces/",
                headers=self.get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                workspaces = response.json()
                if isinstance(workspaces, dict) and "results" in workspaces:
                    workspaces = workspaces["results"]
                if workspaces and len(workspaces) > 0:
                    if not self.workspace_id:
                        self.workspace_id = workspaces[0].get("id")
                    log_test("List Workspaces", "PASS", f"Found {len(workspaces)} workspace(s)")
                    return True
                else:
                    log_test("List Workspaces", "WARN", "No workspaces found")
                    return False
            else:
                log_test("List Workspaces", "FAIL", f"Status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            log_test("List Workspaces", "FAIL", str(e))
            return False
    
    def upload_document(self, file_path=None):
        """Test document upload."""
        if not self.workspace_id:
            log_test("Upload Document", "FAIL", "No workspace selected")
            return False
        
        # Create a test PDF file if none provided
        if not file_path or not os.path.exists(file_path):
            # Try to use the test PDF we created
            test_pdf_path = "/tmp/test_document.pdf"
            if os.path.exists(test_pdf_path):
                file_path = test_pdf_path
            else:
                # Try to create a minimal PDF for testing
                try:
                    from reportlab.pdfgen import canvas
                    from reportlab.lib.pagesizes import letter
                    c = canvas.Canvas(test_pdf_path, pagesize=letter)
                    c.drawString(100, 750, "Test Document for PaperBot")
                    c.drawString(100, 730, "This is a test document to verify upload functionality.")
                    c.drawString(100, 710, "It contains sample text for testing purposes.")
                    c.drawString(100, 690, "This document will be used to test the RAG query and chat features.")
                    c.drawString(100, 670, "The system should be able to extract text, create embeddings, and answer questions.")
                    c.save()
                    file_path = test_pdf_path
                except ImportError:
                    log_test("Upload Document", "WARN", "reportlab not installed, skipping PDF creation")
                    # Try to use an existing PDF if available
                    if os.path.exists("test.pdf"):
                        file_path = "test.pdf"
                    else:
                        log_test("Upload Document", "FAIL", "No test PDF available and cannot create one")
                        return False
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f, 'application/pdf')}
                data = {'workspace_id': self.workspace_id, 'title': 'Test Document'}
                response = requests.post(
                    f"{API_BASE}/documents/upload/",
                    files=files,
                    data=data,
                    headers=self.get_headers(),
                    timeout=30
                )
            
            if response.status_code == 201:
                document = response.json()
                doc_id = document.get("id")
                self.document_ids.append(doc_id)
                log_test("Upload Document", "PASS", f"Document uploaded (ID: {doc_id}, Status: {document.get('status')})")
                return True
            else:
                log_test("Upload Document", "FAIL", f"Status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            log_test("Upload Document", "FAIL", str(e))
            return False
    
    def list_documents(self):
        """Test listing documents."""
        try:
            response = requests.get(
                f"{API_BASE}/documents/",
                headers=self.get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                documents = response.json()
                if isinstance(documents, dict) and "results" in documents:
                    documents = documents["results"]
                log_test("List Documents", "PASS", f"Found {len(documents)} document(s)")
                # Update document IDs
                self.document_ids = [doc.get("id") for doc in documents]
                return True
            else:
                log_test("List Documents", "FAIL", f"Status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            log_test("List Documents", "FAIL", str(e))
            return False
    
    def query(self, query_text="What is this document about?"):
        """Test query functionality."""
        if not self.workspace_id:
            log_test("Query", "FAIL", "No workspace selected")
            return False
        
        try:
            response = requests.post(
                f"{API_BASE}/query/",
                json={
                    "workspace_id": self.workspace_id,
                    "query": query_text,
                    "top_k": 5
                },
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                result = response.json()
                answer = result.get("answer", "")
                citations = result.get("citations", [])
                log_test("Query", "PASS", f"Query successful. Answer length: {len(answer)} chars, Citations: {len(citations)}")
                return True
            elif response.status_code == 404:
                log_test("Query", "WARN", "No relevant documents found (documents may not be indexed yet)")
                return False
            else:
                log_test("Query", "FAIL", f"Status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            log_test("Query", "FAIL", str(e))
            return False
    
    def create_chat_session(self):
        """Test chat session creation."""
        if not self.workspace_id:
            log_test("Create Chat Session", "FAIL", "No workspace selected")
            return False
        
        try:
            # The serializer expects 'workspace' field (which is the model field)
            # The perform_create method extracts 'workspace_id' from request.data
            response = requests.post(
                f"{API_BASE}/chat/",
                json={
                    "workspace": self.workspace_id,
                    "workspace_id": self.workspace_id,  # Also send this for perform_create
                    "title": "Test Chat Session"
                },
                headers=self.get_headers(),
                timeout=10
            )
            if response.status_code == 201:
                session = response.json()
                self.chat_session_id = session.get("id")
                log_test("Create Chat Session", "PASS", f"Chat session created (ID: {self.chat_session_id})")
                return True
            else:
                log_test("Create Chat Session", "FAIL", f"Status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            log_test("Create Chat Session", "FAIL", str(e))
            return False
    
    def send_chat_message(self, message="Hello, can you help me understand the documents?"):
        """Test sending chat message."""
        if not self.chat_session_id:
            log_test("Send Chat Message", "FAIL", "No chat session created")
            return False
        
        try:
            response = requests.post(
                f"{API_BASE}/chat/{self.chat_session_id}/message/",
                json={
                    "message": message,
                    "workspace_id": self.workspace_id
                },
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                result = response.json()
                answer = result.get("answer", "")
                citations = result.get("citations", [])
                log_test("Send Chat Message", "PASS", f"Message sent. Answer length: {len(answer)} chars, Citations: {len(citations)}")
                return True
            elif response.status_code == 404:
                log_test("Send Chat Message", "WARN", "No relevant documents found (documents may not be indexed yet)")
                return False
            else:
                log_test("Send Chat Message", "FAIL", f"Status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            log_test("Send Chat Message", "FAIL", str(e))
            return False
    
    def summarize(self, document_ids=None, summary_type="short"):
        """Test summarization."""
        if not self.workspace_id:
            log_test("Summarize", "FAIL", "No workspace selected")
            return False
        
        if not document_ids:
            document_ids = self.document_ids
        
        if not document_ids:
            log_test("Summarize", "FAIL", "No documents available")
            return False
        
        try:
            response = requests.post(
                f"{API_BASE}/summarize/",
                json={
                    "workspace_id": self.workspace_id,
                    "document_ids": document_ids,
                    "summary_type": summary_type
                },
                headers=self.get_headers(),
                timeout=60
            )
            if response.status_code == 200:
                result = response.json()
                summary = result.get("summary", "")
                log_test("Summarize", "PASS", f"Summary generated. Length: {len(summary)} chars")
                return True
            elif response.status_code == 404:
                log_test("Summarize", "WARN", "No valid indexed documents found")
                return False
            else:
                log_test("Summarize", "FAIL", f"Status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            log_test("Summarize", "FAIL", str(e))
            return False

def main():
    """Run all tests."""
    print("=" * 70)
    print("PaperBot Component Testing")
    print("=" * 70)
    print()
    
    # Check if server is running
    if not check_server():
        print("\n❌ Backend server is not running!")
        print("Please start the backend server first:")
        print("  cd /home/d4rk_m3ta/Desktop/PaperBot")
        print("  ./start.sh")
        print("  OR")
        print("  python manage.py runserver")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("Starting Tests...")
    print("=" * 70)
    print()
    
    client = TestClient()
    
    # Test 1: Authentication
    print("\n--- Testing Authentication ---")
    # Try login first (in case test user exists)
    if not client.login():
        # If login fails, try registration
        if not client.register():
            print("❌ Cannot proceed without authentication")
            sys.exit(1)
    
    # Test 2: Get current user
    client.get_current_user()
    
    # Test 3: Workspace Management
    print("\n--- Testing Workspace Management ---")
    if not client.list_workspaces():
        # Create workspace if none exists
        client.create_workspace()
    else:
        # Try to create another workspace
        client.create_workspace(name="Test Workspace 2")
    
    # Test 4: Document Upload
    print("\n--- Testing Document Upload ---")
    client.upload_document()
    time.sleep(2)  # Wait a bit
    client.list_documents()
    
    # Test 5: Query/Search
    print("\n--- Testing Query/Search ---")
    print("Note: Query may fail if documents are not yet indexed. This is expected.")
    client.query("What is the main topic of the documents?")
    
    # Test 6: Chat
    print("\n--- Testing Chat Interface ---")
    client.create_chat_session()
    if client.chat_session_id:
        client.send_chat_message("Hello, can you summarize the documents?")
    
    # Test 7: Summarization
    print("\n--- Testing Summarization ---")
    print("Note: Summarization may fail if documents are not yet indexed. This is expected.")
    client.summarize()
    
    # Print summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"\n✅ Passed: {len(test_results['passed'])}")
    print(f"❌ Failed: {len(test_results['failed'])}")
    print(f"⚠️  Warnings: {len(test_results['warnings'])}")
    
    if test_results['failed']:
        print("\nFailed Tests:")
        for failure in test_results['failed']:
            print(f"  {failure}")
    
    if test_results['warnings']:
        print("\nWarnings:")
        for warning in test_results['warnings']:
            print(f"  {warning}")
    
    print("\n" + "=" * 70)
    
    # Save results to file
    results_file = Path("test_results.json")
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    print(f"\nDetailed results saved to: {results_file}")
    
    # Return exit code based on results
    if test_results['failed']:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()


