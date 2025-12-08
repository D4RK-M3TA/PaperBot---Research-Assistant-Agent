"""
API views for document processing, RAG Q/A, and chat.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle, ScopedRateThrottle
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from core.models import (
    Document, Workspace, ChatSession, ChatMessage, GenerationModel
)
from core.serializers import DocumentSerializer, ChatSessionSerializer
from .serializers import (
    DocumentUploadSerializer, QuerySerializer, QueryResponseSerializer,
    SummarizeSerializer, SummaryResponseSerializer, ChatMessageCreateSerializer
)
from .utils import EmbeddingService, LLMService
from .tasks import process_document


class DocumentViewSet(viewsets.ModelViewSet):
    """Document management viewset."""
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'ingestion'

    def get_queryset(self):
        """Return documents in user's workspaces."""
        user_workspaces = Workspace.objects.filter(owner=self.request.user)
        return Document.objects.filter(workspace__in=user_workspaces)

    @action(detail=False, methods=['post'])
    def upload(self, request):
        """Upload and process a PDF document."""
        serializer = DocumentUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        workspace_id = serializer.validated_data['workspace_id']
        file = serializer.validated_data['file']
        title = serializer.validated_data.get('title', file.name)
        
        # Verify workspace ownership
        try:
            workspace = Workspace.objects.get(id=workspace_id, owner=request.user)
        except Workspace.DoesNotExist:
            return Response(
                {'error': 'Workspace not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Save file
        file_path = default_storage.save(
            f'workspaces/{workspace_id}/{file.name}',
            ContentFile(file.read())
        )
        
        # Create document record
        document = Document.objects.create(
            workspace=workspace,
            title=title,
            filename=file.name,
            file_path=file_path,
            file_size=file.size,
            uploaded_by=request.user,
            status='uploaded'
        )
        
        # Trigger async processing
        process_document.delay(document.id)
        
        return Response(
            DocumentSerializer(document).data,
            status=status.HTTP_201_CREATED
        )


class ChatSessionViewSet(viewsets.ModelViewSet):
    """Chat session management viewset."""
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return chat sessions for user's workspaces."""
        user_workspaces = Workspace.objects.filter(owner=self.request.user)
        return ChatSession.objects.filter(workspace__in=user_workspaces)

    def perform_create(self, serializer):
        """Set the user to the current user."""
        workspace_id = self.request.data.get('workspace_id')
        workspace = Workspace.objects.get(id=workspace_id, owner=self.request.user)
        serializer.save(user=self.request.user, workspace=workspace)

    @action(detail=True, methods=['post'])
    def message(self, request, pk=None):
        """Send a message in a chat session."""
        session = self.get_object()
        serializer = ChatMessageCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        message_text = serializer.validated_data['message']
        top_k = serializer.validated_data.get('top_k', 5)
        
        # Create user message
        user_message = ChatMessage.objects.create(
            session=session,
            role='user',
            content=message_text
        )
        
        # Get conversation history
        history = [
            {
                'content': msg.content,
                'response': '' if msg.role == 'user' else msg.content
            }
            for msg in session.messages.all().order_by('created_at')[:-1]  # Exclude current message
        ]
        
        # Perform RAG query
        try:
            # Get query embedding
            embedding_service = EmbeddingService()
            query_embedding = embedding_service.create_embedding(message_text)
            
            # Search similar chunks
            similar_chunks = embedding_service.search_similar_chunks(
                query_embedding,
                top_k=top_k,
                workspace_id=workspace_id
            )
            
            chunks = [chunk for chunk, _ in similar_chunks]
            
            # Generate answer
            llm_service = LLMService()
            answer, citations = llm_service.generate_answer(
                message_text,
                chunks,
                conversation_history=history
            )
            
            # Get active generation model
            generation_model = llm_service.get_active_generation_model()
            
            # Create assistant message
            assistant_message = ChatMessage.objects.create(
                session=session,
                role='assistant',
                content=answer,
                citations=citations,
                generation_model=generation_model
            )
            assistant_message.retrieved_chunks.set(chunks)
            
            return Response({
                'message_id': assistant_message.id,
                'answer': answer,
                'citations': citations
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def query(request):
    """RAG-based Q/A endpoint."""
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'generation'
    
    serializer = QuerySerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    workspace_id = serializer.validated_data['workspace_id']
    query_text = serializer.validated_data['query']
    top_k = serializer.validated_data.get('top_k', 5)
    include_citations = serializer.validated_data.get('include_citations', True)
    
    # Verify workspace access
    try:
        workspace = Workspace.objects.get(id=workspace_id, owner=request.user)
    except Workspace.DoesNotExist:
        return Response(
            {'error': 'Workspace not found or access denied'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        # Get query embedding
        embedding_service = EmbeddingService()
        query_embedding = embedding_service.create_embedding(query_text)
        
        # Search similar chunks
        similar_chunks = embedding_service.search_similar_chunks(
            query_embedding,
            top_k=top_k,
            workspace_id=workspace_id
        )
        
        chunks = [chunk for chunk, _ in similar_chunks]
        
        if not chunks:
            return Response(
                {'error': 'No relevant documents found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Generate answer
        llm_service = LLMService()
        answer, citations = llm_service.generate_answer(query_text, chunks)
        
        # Format citations
        formatted_citations = []
        if include_citations:
            for citation in citations:
                formatted_citations.append({
                    'document_id': citation['document_id'],
                    'document_title': citation['document_title'],
                    'chunk_id': citation['chunk_id'],
                    'page_number': citation['page_number'],
                    'snippet': citation['snippet'],
                    'score': citation.get('score')
                })
        
        return Response({
            'answer': answer,
            'citations': formatted_citations,
            'retrieved_chunks': [chunk.id for chunk in chunks]
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def summarize(request):
    """Multi-document summarization endpoint."""
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'generation'
    
    serializer = SummarizeSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    workspace_id = serializer.validated_data['workspace_id']
    document_ids = serializer.validated_data['document_ids']
    summary_type = serializer.validated_data.get('summary_type', 'short')
    
    # Verify workspace access
    try:
        workspace = Workspace.objects.get(id=workspace_id, owner=request.user)
    except Workspace.DoesNotExist:
        return Response(
            {'error': 'Workspace not found or access denied'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get documents
    documents = Document.objects.filter(
        id__in=document_ids,
        workspace=workspace,
        status='indexed'
    )
    
    if not documents.exists():
        return Response(
            {'error': 'No valid documents found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        # Get all chunks from documents
        from core.models import Chunk
        chunks = Chunk.objects.filter(document__in=documents).order_by('document', 'chunk_index')
        
        if not chunks.exists():
            return Response(
                {'error': 'No chunks found in documents'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Generate summary
        llm_service = LLMService()
        summary, related_work, citations = llm_service.generate_summary(
            list(chunks),
            summary_type=summary_type
        )
        
        return Response({
            'summary': summary,
            'related_work': related_work if summary_type == 'related_work' else None,
            'citations': citations,
            'document_ids': list(documents.values_list('id', flat=True))
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

