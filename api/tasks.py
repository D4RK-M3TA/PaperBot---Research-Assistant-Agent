"""
Celery tasks for async document processing.
"""
import os
import numpy as np
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.core.files.storage import default_storage
from core.models import Document, Chunk, ChunkEmbedding, EmbeddingModel, PipelineRun
from api.utils import PDFProcessor, EmbeddingService


@shared_task(bind=True, max_retries=3)
def process_document(self, document_id: int):
    """Process document: extract text, chunk, embed, and index."""
    document = Document.objects.get(id=document_id)
    pipeline_run = PipelineRun.objects.create(
        document=document,
        status='running',
        stage='extract'
    )
    
    try:
        # Stage 1: Extract text
        document.status = 'processing'
        document.save()
        
        file_path = document.file_path
        if not os.path.exists(file_path):
            # Try to get from storage
            if hasattr(default_storage, 'url'):
                file_path = default_storage.path(document.file_path)
            else:
                raise FileNotFoundError(f"Document file not found: {document.file_path}")
        
        text, metadata = PDFProcessor.extract_text_from_pdf(file_path)
        document.extracted_text = text
        document.page_count = metadata.get('pages', 0)
        document.metadata = metadata
        document.status = 'extracted'
        document.save()
        
        pipeline_run.stage = 'chunk'
        pipeline_run.save()
        
        # Stage 2: Chunk text
        # Delete existing chunks if any (for reprocessing)
        Chunk.objects.filter(document=document).delete()
        
        chunks_data = PDFProcessor.chunk_text(text)
        chunks = []
        for chunk_data in chunks_data:
            chunk = Chunk.objects.create(
                document=document,
                chunk_index=chunk_data['chunk_index'],
                text=chunk_data['text'],
                start_char=chunk_data['start_char'],
                end_char=chunk_data['end_char'],
                page_number=None  # Will be estimated if needed
            )
            chunks.append(chunk)
        
        document.status = 'chunked'
        document.save()
        
        pipeline_run.stage = 'embed'
        pipeline_run.save()
        
        # Stage 3: Create embeddings
        embedding_model = EmbeddingService.get_active_embedding_model()
        if not embedding_model:
            # Create default embedding model if none exists
            embedding_model = EmbeddingModel.objects.create(
                name='default',
                version='1.0',
                model_path=settings.EMBEDDING_MODEL,
                dimension=384,  # Default for all-MiniLM-L6-v2
                is_active=True
            )
        
        embedding_service = EmbeddingService()
        model = embedding_service.get_model()
        
        for chunk in chunks:
            embedding_vector = embedding_service.create_embedding(chunk.text)
            
            # Store embedding
            ChunkEmbedding.objects.create(
                chunk=chunk,
                embedding_model=embedding_model,
                vector=embedding_vector.tolist()
            )
        
        document.status = 'embedded'
        document.save()
        
        pipeline_run.stage = 'index'
        pipeline_run.save()
        
        # Stage 4: Index in vector DB
        index = embedding_service.get_or_create_index(embedding_model.dimension)
        
        # Add embeddings to index
        for chunk in chunks:
            embedding = chunk.embedding
            vector = np.array(embedding.vector).astype('float32').reshape(1, -1)
            index.add(vector)
        
        # Save index
        embedding_service.save_index()
        
        document.status = 'indexed'
        document.save()
        
        pipeline_run.status = 'completed'
        pipeline_run.completed_at = timezone.now()
        pipeline_run.save()
        
        return f"Document {document_id} processed successfully"
    
    except Exception as e:
        document.status = 'failed'
        document.error_message = str(e)
        document.save()
        
        pipeline_run.status = 'failed'
        pipeline_run.error_message = str(e)
        pipeline_run.completed_at = timezone.now()
        pipeline_run.save()
        
        # Retry if not max retries
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        
        raise


@shared_task
def reindex_workspace(workspace_id: int):
    """Reindex all documents in a workspace."""
    from core.models import Workspace
    
    workspace = Workspace.objects.get(id=workspace_id)
    documents = workspace.documents.filter(status='indexed')
    
    embedding_model = EmbeddingService.get_active_embedding_model()
    if not embedding_model:
        return "No active embedding model found"
    
    embedding_service = EmbeddingService()
    index = embedding_service.get_or_create_index(embedding_model.dimension)
    
    # Clear and rebuild index
    index.reset()
    
    for document in documents:
        chunks = document.chunks.all()
        for chunk in chunks:
            try:
                embedding = chunk.embedding
                vector = np.array(embedding.vector).astype('float32').reshape(1, -1)
                index.add(vector)
            except ChunkEmbedding.DoesNotExist:
                continue
    
    embedding_service.save_index()
    return f"Reindexed {documents.count()} documents"

