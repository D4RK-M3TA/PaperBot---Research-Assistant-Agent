"""
Tests for API endpoints.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from core.models import Workspace, Document, EmbeddingModel, GenerationModel

User = get_user_model()


class DocumentUploadTestCase(TestCase):
    """Test document upload endpoint."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.workspace = Workspace.objects.create(
            name='Test Workspace',
            owner=self.user
        )
    
    def test_upload_document(self):
        """Test document upload."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        pdf_content = b'%PDF-1.4 fake pdf content'
        pdf_file = SimpleUploadedFile(
            "test.pdf",
            pdf_content,
            content_type="application/pdf"
        )
        
        response = self.client.post('/api/documents/upload/', {
            'workspace_id': self.workspace.id,
            'file': pdf_file,
            'title': 'Test Document'
        }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Document.objects.count(), 1)
        
        doc = Document.objects.first()
        self.assertEqual(doc.title, 'Test Document')
        self.assertEqual(doc.workspace, self.workspace)


class QueryTestCase(TestCase):
    """Test RAG query endpoint."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.workspace = Workspace.objects.create(
            name='Test Workspace',
            owner=self.user
        )
        
        # Create embedding model
        self.embedding_model = EmbeddingModel.objects.create(
            name='test-model',
            version='1.0',
            model_path='sentence-transformers/all-MiniLM-L6-v2',
            dimension=384,
            is_active=True
        )
    
    def test_query_endpoint(self):
        """Test query endpoint structure."""
        response = self.client.post('/api/query/', {
            'workspace_id': self.workspace.id,
            'query': 'What is machine learning?',
            'top_k': 5
        }, format='json')
        
        # Should return 404 if no documents, or 200 if documents exist
        self.assertIn(
            response.status_code,
            [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
        )


class SummarizeTestCase(TestCase):
    """Test summarization endpoint."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.workspace = Workspace.objects.create(
            name='Test Workspace',
            owner=self.user
        )
    
    def test_summarize_endpoint(self):
        """Test summarize endpoint structure."""
        response = self.client.post('/api/summarize/', {
            'workspace_id': self.workspace.id,
            'document_ids': [1, 2],
            'summary_type': 'short'
        }, format='json')
        
        # Should return 404 if no documents, or 200 if documents exist
        self.assertIn(
            response.status_code,
            [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
        )


class AuthenticationTestCase(TestCase):
    """Test authentication."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_token_obtain(self):
        """Test JWT token obtain."""
        response = self.client.post('/api/auth/token/', {
            'username': 'testuser',
            'password': 'testpass123'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_protected_endpoint(self):
        """Test that protected endpoints require authentication."""
        response = self.client.get('/api/documents/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)



