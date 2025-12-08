"""
Admin configuration for core models.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Workspace, Document, Chunk, EmbeddingModel,
    ChunkEmbedding, GenerationModel, ChatSession, ChatMessage,
    PipelineRun, AuditLog
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'is_staff', 'created_at']
    list_filter = ['is_staff', 'is_superuser', 'created_at']


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'owner__username']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'workspace', 'status', 'page_count', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'filename']
    readonly_fields = ['created_at', 'updated_at', 'processed_at']


@admin.register(Chunk)
class ChunkAdmin(admin.ModelAdmin):
    list_display = ['document', 'chunk_index', 'page_number', 'token_count']
    list_filter = ['document__workspace']
    search_fields = ['text', 'document__title']


@admin.register(EmbeddingModel)
class EmbeddingModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'version', 'dimension', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']


@admin.register(GenerationModel)
class GenerationModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'version', 'provider', 'model_id', 'is_active']
    list_filter = ['provider', 'is_active', 'created_at']


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'workspace', 'user', 'title', 'updated_at']
    list_filter = ['created_at']
    search_fields = ['title', 'workspace__name']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['session', 'role', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['content']


@admin.register(PipelineRun)
class PipelineRunAdmin(admin.ModelAdmin):
    list_display = ['document', 'status', 'stage', 'started_at', 'completed_at']
    list_filter = ['status', 'stage', 'started_at']
    readonly_fields = ['started_at', 'completed_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'resource_type', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['user__username']
    readonly_fields = ['created_at']



