"""
Serializers for core models.
"""
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import (
    User, Workspace, Document, Chunk, EmbeddingModel,
    GenerationModel, ChatSession, ChatMessage
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class WorkspaceSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    document_count = serializers.SerializerMethodField()

    class Meta:
        model = Workspace
        fields = ['id', 'name', 'description', 'owner', 'is_active', 
                  'created_at', 'updated_at', 'document_count']
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

    def get_document_count(self, obj):
        return obj.documents.count()


class DocumentSerializer(serializers.ModelSerializer):
    workspace_name = serializers.CharField(source='workspace.name', read_only=True)
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)
    chunk_count = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ['id', 'workspace', 'workspace_name', 'title', 'filename',
                  'file_size', 'status', 'page_count', 'metadata',
                  'uploaded_by_username', 'chunk_count', 'error_message',
                  'created_at', 'updated_at', 'processed_at']
        read_only_fields = ['id', 'status', 'page_count', 'metadata',
                           'error_message', 'created_at', 'updated_at', 'processed_at']

    def get_chunk_count(self, obj):
        return obj.chunks.count()


class ChunkSerializer(serializers.ModelSerializer):
    document_title = serializers.CharField(source='document.title', read_only=True)

    class Meta:
        model = Chunk
        fields = ['id', 'document', 'document_title', 'chunk_index',
                  'text', 'page_number', 'start_char', 'end_char',
                  'token_count', 'created_at']
        read_only_fields = ['id', 'created_at']


class EmbeddingModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmbeddingModel
        fields = ['id', 'name', 'version', 'dimension', 'description',
                  'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class GenerationModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = GenerationModel
        fields = ['id', 'name', 'version', 'provider', 'model_id',
                  'description', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'content', 'citations', 'created_at']
        read_only_fields = ['id', 'created_at']


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)
    workspace_name = serializers.CharField(source='workspace.name', read_only=True)
    workspace_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = ChatSession
        fields = ['id', 'workspace', 'workspace_id', 'workspace_name', 'title', 'messages',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'workspace', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        # workspace_id is handled in perform_create, remove it from attrs to avoid validation error
        # It's write_only so it won't be validated against the model field
        if 'workspace_id' in attrs:
            attrs.pop('workspace_id')
        return attrs





