"""
Core models for PaperBot.
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    """Custom user model."""
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'


class Workspace(models.Model):
    """User workspace for organizing documents."""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workspaces')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'workspaces'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.owner.username})"


class Document(models.Model):
    """PDF document metadata."""
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('extracted', 'Text Extracted'),
        ('chunked', 'Chunked'),
        ('embedded', 'Embedded'),
        ('indexed', 'Indexed'),
        ('failed', 'Failed'),
    ]

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=500)
    filename = models.CharField(max_length=500)
    file_path = models.CharField(max_length=1000)  # S3 path or local path
    file_size = models.BigIntegerField()
    mime_type = models.CharField(max_length=100, default='application/pdf')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    page_count = models.IntegerField(null=True, blank=True)
    extracted_text = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)  # PDF metadata
    error_message = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_documents')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'documents'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.workspace.name})"


class Chunk(models.Model):
    """Text chunk from a document."""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    chunk_index = models.IntegerField()  # Order within document
    text = models.TextField()
    page_number = models.IntegerField(null=True, blank=True)
    start_char = models.IntegerField(null=True, blank=True)
    end_char = models.IntegerField(null=True, blank=True)
    token_count = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chunks'
        ordering = ['document', 'chunk_index']
        unique_together = ['document', 'chunk_index']

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.document.title}"


class EmbeddingModel(models.Model):
    """Versioned embedding model metadata."""
    name = models.CharField(max_length=255)
    version = models.CharField(max_length=50)
    model_path = models.CharField(max_length=1000)
    dimension = models.IntegerField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'embedding_models'
        unique_together = ['name', 'version']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} v{self.version}"


class ChunkEmbedding(models.Model):
    """Embedding vector for a chunk."""
    chunk = models.OneToOneField(Chunk, on_delete=models.CASCADE, related_name='embedding')
    embedding_model = models.ForeignKey(EmbeddingModel, on_delete=models.PROTECT, related_name='embeddings')
    vector = models.JSONField()  # Store as JSON array
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chunk_embeddings'

    def __str__(self):
        return f"Embedding for {self.chunk}"


class GenerationModel(models.Model):
    """Versioned LLM generation model metadata."""
    name = models.CharField(max_length=255)
    version = models.CharField(max_length=50)
    provider = models.CharField(max_length=50)  # openai, anthropic, local
    model_id = models.CharField(max_length=255)  # e.g., gpt-4, claude-3-opus
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'generation_models'
        unique_together = ['name', 'version']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} v{self.version} ({self.provider})"


class ChatSession(models.Model):
    """Chat session for iterative Q/A."""
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='chat_sessions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chat_sessions'
        ordering = ['-updated_at']

    def __str__(self):
        return f"Session {self.id} - {self.workspace.name}"


class ChatMessage(models.Model):
    """Message in a chat session."""
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    citations = models.JSONField(default=list, blank=True)  # List of chunk references
    retrieved_chunks = models.ManyToManyField(Chunk, blank=True, related_name='messages')
    generation_model = models.ForeignKey(GenerationModel, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_messages'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


class PipelineRun(models.Model):
    """Track pipeline execution runs."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='pipeline_runs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    stage = models.CharField(max_length=50, blank=True)  # extract, chunk, embed, index
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'pipeline_runs'
        ordering = ['-started_at']

    def __str__(self):
        return f"Run {self.id} - {self.document.title} ({self.status})"


class AuditLog(models.Model):
    """Audit log for all user actions."""
    ACTION_CHOICES = [
        ('document_upload', 'Document Upload'),
        ('document_delete', 'Document Delete'),
        ('query', 'Query'),
        ('summarize', 'Summarize'),
        ('chat', 'Chat'),
        ('workspace_create', 'Workspace Create'),
        ('workspace_delete', 'Workspace Delete'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    resource_type = models.CharField(max_length=50, blank=True)  # document, workspace, etc.
    resource_id = models.IntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action', 'created_at']),
        ]

    def __str__(self):
        return f"{self.action} by {self.user} at {self.created_at}"





