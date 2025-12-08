"""
Utility functions for PDF processing, embeddings, and LLM interactions.
"""
import os
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    faiss = None

from django.conf import settings
from core.models import EmbeddingModel, GenerationModel, Chunk, ChunkEmbedding

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    Anthropic = None


class PDFProcessor:
    """Handle PDF text extraction."""
    
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> Tuple[str, Dict]:
        """Extract text and metadata from PDF."""
        try:
            text = extract_text(
                file_path,
                laparams=LAParams(
                    line_margin=0.5,
                    word_margin=0.1,
                    char_margin=2.0,
                    boxes_flow=0.5
                )
            )
            
            # Basic metadata extraction
            metadata = {
                'pages': PDFProcessor._count_pages(file_path),
                'char_count': len(text),
            }
            
            return text, metadata
        except Exception as e:
            raise Exception(f"PDF extraction failed: {str(e)}")
    
    @staticmethod
    def _count_pages(file_path: str) -> int:
        """Count pages in PDF."""
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            return len(reader.pages)
        except:
            return 0
    
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk_text.rfind('.')
                last_newline = chunk_text.rfind('\n')
                break_point = max(last_period, last_newline)
                if break_point > chunk_size * 0.5:  # Only break if we're past halfway
                    end = start + break_point + 1
                    chunk_text = text[start:end]
            
            chunks.append({
                'text': chunk_text.strip(),
                'start_char': start,
                'end_char': end,
                'chunk_index': chunk_index,
            })
            
            start = end - overlap
            chunk_index += 1
        
        return chunks


class EmbeddingService:
    """Handle embeddings and vector search."""
    
    _model = None
    _index = None
    
    @classmethod
    def get_model(cls):
        """Get or load embedding model."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise Exception("sentence-transformers not installed. Install with: pip install sentence-transformers")
        if cls._model is None:
            model_name = settings.EMBEDDING_MODEL
            cls._model = SentenceTransformer(model_name)
        return cls._model
    
    @classmethod
    def get_active_embedding_model(cls) -> Optional[EmbeddingModel]:
        """Get active embedding model from database."""
        return EmbeddingModel.objects.filter(is_active=True).first()
    
    @classmethod
    def create_embedding(cls, text: str) -> np.ndarray:
        """Create embedding for text."""
        model = cls.get_model()
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding
    
    @classmethod
    def get_or_create_index(cls, dimension: int):
        """Get or create FAISS index."""
        if not FAISS_AVAILABLE:
            raise Exception("faiss not installed. Install with: pip install faiss-cpu")
        if cls._index is None:
            index_path = Path(settings.VECTOR_DB_PATH) / 'faiss.index'
            if index_path.exists():
                cls._index = faiss.read_index(str(index_path))
            else:
                cls._index = faiss.IndexFlatL2(dimension)
        return cls._index
    
    @classmethod
    def save_index(cls, index_path: Optional[str] = None):
        """Save FAISS index to disk."""
        if cls._index is not None:
            if index_path is None:
                index_path = Path(settings.VECTOR_DB_PATH) / 'faiss.index'
            Path(index_path).parent.mkdir(parents=True, exist_ok=True)
            faiss.write_index(cls._index, str(index_path))
    
    @classmethod
    def search_similar_chunks(cls, query_embedding: np.ndarray, top_k: int = 5, workspace_id: Optional[int] = None) -> List[Tuple[Chunk, float]]:
        """Search for similar chunks using FAISS."""
        # Get active embedding model
        embedding_model = cls.get_active_embedding_model()
        if not embedding_model:
            raise Exception("No active embedding model found")
        
        # Get all embeddings for the model (and optionally workspace)
        embedding_query = ChunkEmbedding.objects.filter(embedding_model=embedding_model)
        if workspace_id:
            embedding_query = embedding_query.filter(chunk__document__workspace_id=workspace_id)
        
        embeddings_list = list(embedding_query.select_related('chunk'))
        
        if not embeddings_list:
            return []
        
        # Build FAISS index from current embeddings
        dimension = embedding_model.dimension
        index = faiss.IndexFlatL2(dimension)
        
        # Add all embeddings to index
        vectors = []
        chunk_mapping = {}  # Map FAISS index position to ChunkEmbedding
        for i, embedding_obj in enumerate(embeddings_list):
            vector = np.array(embedding_obj.vector).astype('float32').reshape(1, -1)
            vectors.append(vector)
            chunk_mapping[i] = embedding_obj
        
        if vectors:
            all_vectors = np.vstack(vectors)
            index.add(all_vectors)
        
        # Search
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        distances, indices = index.search(query_embedding, min(top_k, len(embeddings_list)))
        
        # Get chunks from database
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < 0 or idx >= len(embeddings_list):  # FAISS returns -1 for empty slots
                continue
            try:
                embedding_obj = chunk_mapping[idx]
                chunk = embedding_obj.chunk
                results.append((chunk, float(distance)))
            except (IndexError, KeyError):
                continue
        
        return results


class LLMService:
    """Handle LLM interactions."""
    
    @staticmethod
    def get_active_generation_model() -> Optional[GenerationModel]:
        """Get active generation model from database."""
        return GenerationModel.objects.filter(is_active=True).first()
    
    @classmethod
    def generate_answer(cls, query: str, context_chunks: List[Chunk], 
                        conversation_history: Optional[List[Dict]] = None) -> Tuple[str, List[Dict]]:
        """Generate answer using LLM with RAG context."""
        model = cls.get_active_generation_model()
        if not model:
            raise Exception("No active generation model found")
        
        # Build context from chunks
        context_text = "\n\n".join([
            f"[Document: {chunk.document.title}, Page: {chunk.page_number or 'N/A'}]\n{chunk.text}"
            for chunk in context_chunks
        ])
        
        # Build prompt
        prompt = cls._build_qa_prompt(query, context_text, conversation_history)
        
        # Call LLM
        if model.provider == 'openai':
            response = cls._call_openai(model.model_id, prompt)
        elif model.provider == 'anthropic':
            response = cls._call_anthropic(model.model_id, prompt)
        else:
            raise Exception(f"Unsupported LLM provider: {model.provider}")
        
        # Extract answer and citations
        answer, citations = cls._parse_response(response, context_chunks)
        
        return answer, citations
    
    @staticmethod
    def _build_qa_prompt(query: str, context: str, history: Optional[List[Dict]] = None) -> str:
        """Build prompt for Q/A."""
        system_prompt = """You are a research assistant that answers questions based on provided document excerpts. 
Always cite your sources using the format [Document: title, Page: X] when referencing information from the context.
If the answer cannot be found in the context, say so clearly."""
        
        if history:
            history_text = "\n".join([
                f"User: {msg.get('content', '')}\nAssistant: {msg.get('response', '')}"
                for msg in history[-5:]  # Last 5 exchanges
            ])
            prompt = f"""{system_prompt}

Previous conversation:
{history_text}

Context from documents:
{context}

Question: {query}

Answer:"""
        else:
            prompt = f"""{system_prompt}

Context from documents:
{context}

Question: {query}

Answer:"""
        
        return prompt
    
    @staticmethod
    def _call_openai(model_id: str, prompt: str) -> str:
        """Call OpenAI API."""
        if not settings.OPENAI_API_KEY:
            raise Exception("OpenAI API key not configured")
        
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": "You are a helpful research assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content
    
    @staticmethod
    def _call_anthropic(model_id: str, prompt: str) -> str:
        """Call Anthropic API."""
        if not settings.ANTHROPIC_API_KEY:
            raise Exception("Anthropic API key not configured")
        
        client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=model_id,
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text
    
    @staticmethod
    def _parse_response(response: str, chunks: List[Chunk]) -> Tuple[str, List[Dict]]:
        """Parse LLM response and extract citations."""
        citations = []
        answer = response
        
        # Simple citation extraction (in production, use more sophisticated parsing)
        for chunk in chunks:
            if chunk.document.title in answer or any(word in answer for word in chunk.text[:50].split()[:5]):
                citations.append({
                    'document_id': chunk.document.id,
                    'document_title': chunk.document.title,
                    'chunk_id': chunk.id,
                    'page_number': chunk.page_number,
                    'snippet': chunk.text[:200],
                    'score': None
                })
        
        return answer, citations
    
    @classmethod
    def generate_summary(cls, document_chunks: List[Chunk], summary_type: str = 'short') -> Tuple[str, str, List[Dict]]:
        """Generate multi-document summary."""
        model = cls.get_active_generation_model()
        if not model:
            raise Exception("No active generation model found")
        
        # Combine all chunks
        context_text = "\n\n".join([
            f"[Document: {chunk.document.title}, Page: {chunk.page_number or 'N/A'}]\n{chunk.text}"
            for chunk in document_chunks
        ])
        
        # Build prompt based on type
        if summary_type == 'related_work':
            prompt = f"""Summarize the following research documents, focusing on related work and methodology.

Documents:
{context_text}

Provide:
1. A brief summary (2-3 sentences)
2. A detailed "Related Work" section with inline citations in the format [Document: title, Page: X]

Summary:"""
        else:
            prompt = f"""Provide a {'brief' if summary_type == 'short' else 'detailed'} summary of the following research documents.

Documents:
{context_text}

Summary:"""
        
        # Call LLM
        if model.provider == 'openai':
            response = cls._call_openai(model.model_id, prompt)
        elif model.provider == 'anthropic':
            response = cls._call_anthropic(model.model_id, prompt)
        else:
            raise Exception(f"Unsupported LLM provider: {model.provider}")
        
        # Extract summary and related work
        if summary_type == 'related_work':
            parts = response.split('Related Work:', 1)
            summary = parts[0].strip()
            related_work = parts[1].strip() if len(parts) > 1 else ""
        else:
            summary = response
            related_work = ""
        
        # Build citations
        citations = []
        seen_docs = set()
        for chunk in document_chunks:
            if chunk.document.id not in seen_docs:
                citations.append({
                    'document_id': chunk.document.id,
                    'document_title': chunk.document.title,
                    'chunk_id': chunk.id,
                    'page_number': chunk.page_number,
                    'snippet': chunk.text[:200],
                    'score': None
                })
                seen_docs.add(chunk.document.id)
        
        return summary, related_work, citations

