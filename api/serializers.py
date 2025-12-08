"""
Serializers for API endpoints.
"""
from rest_framework import serializers
from core.models import Document, ChatSession, ChatMessage


class DocumentUploadSerializer(serializers.Serializer):
    """Serializer for document upload."""
    workspace_id = serializers.IntegerField()
    file = serializers.FileField()
    title = serializers.CharField(max_length=500, required=False)


class QuerySerializer(serializers.Serializer):
    """Serializer for RAG query."""
    workspace_id = serializers.IntegerField()
    query = serializers.CharField()
    top_k = serializers.IntegerField(default=5, min_value=1, max_value=20)
    include_citations = serializers.BooleanField(default=True)


class SummarizeSerializer(serializers.Serializer):
    """Serializer for multi-document summarization."""
    workspace_id = serializers.IntegerField()
    document_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    summary_type = serializers.ChoiceField(
        choices=['short', 'detailed', 'related_work'],
        default='short'
    )


class ChatMessageCreateSerializer(serializers.Serializer):
    """Serializer for creating chat messages."""
    session_id = serializers.IntegerField(required=False)
    workspace_id = serializers.IntegerField()
    message = serializers.CharField()
    top_k = serializers.IntegerField(default=5, min_value=1, max_value=20)


class CitationSerializer(serializers.Serializer):
    """Serializer for citation references."""
    document_id = serializers.IntegerField()
    document_title = serializers.CharField()
    chunk_id = serializers.IntegerField()
    page_number = serializers.IntegerField(allow_null=True)
    snippet = serializers.CharField()
    score = serializers.FloatField(allow_null=True)


class QueryResponseSerializer(serializers.Serializer):
    """Serializer for RAG query response."""
    answer = serializers.CharField()
    citations = CitationSerializer(many=True)
    retrieved_chunks = serializers.ListField(child=serializers.IntegerField())


class SummaryResponseSerializer(serializers.Serializer):
    """Serializer for summarization response."""
    summary = serializers.CharField()
    related_work = serializers.CharField(required=False)
    citations = CitationSerializer(many=True)
    document_ids = serializers.ListField(child=serializers.IntegerField())





