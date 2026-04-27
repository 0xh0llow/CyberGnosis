"""
Vector Search Engine - Chroma Integration
==========================================

Ricerca semantica su alert, snippet, knowledge base usando embeddings.
"""

import chromadb
from chromadb.config import Settings
import logging
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import os
from threading import Lock

logger = logging.getLogger(__name__)


class VectorSearchEngine:
    """
    Motore ricerca semantica con Chroma DB.
    """
    
    def __init__(
        self,
        chroma_host: str = None,
        chroma_port: int = None,
        embedding_model: str = None
    ):
        """
        Inizializza vector search engine.
        
        Args:
            chroma_host: Host Chroma DB (default: env CHROMA_HOST)
            chroma_port: Porta Chroma DB (default: env CHROMA_PORT)
            embedding_model: Modello embedding (default: all-MiniLM-L6-v2)
        """
        self.chroma_host = chroma_host or os.getenv("CHROMA_HOST", "localhost")
        self.chroma_port = int(chroma_port or os.getenv("CHROMA_PORT", "8001"))
        self.embedding_model_name = embedding_model or os.getenv(
            "EMBEDDING_MODEL",
            "sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Client Chroma (HTTP)
        self.client: Optional[chromadb.HttpClient] = None
        
        # Embedding model
        self.embedding_model = None
        self._embedding_lock = Lock()
        
        # Collections
        self.alerts_collection = None
        self.snippets_collection = None
        self.knowledge_collection = None

    def _ensure_embedding_model(self) -> bool:
        """Carica il modello embeddings solo quando serve davvero."""
        if self.embedding_model is not None:
            return True

        with self._embedding_lock:
            if self.embedding_model is not None:
                return True

            try:
                logger.info(f"Loading embedding model: {self.embedding_model_name}")
                self.embedding_model = SentenceTransformer(self.embedding_model_name)
                logger.info("✓ Embedding model loaded")
                return True
            except Exception as e:
                logger.error(f"Failed to load embedding model {self.embedding_model_name}: {e}")
                self.embedding_model = None
                return False
    
    def initialize(self):
        """Inizializza connessione Chroma e collezioni."""
        try:
            # Connetti a Chroma
            self.client = chromadb.HttpClient(
                host=self.chroma_host,
                port=self.chroma_port
            )
            
            # Test connessione
            self.client.heartbeat()
            logger.info(f"✓ Connected to Chroma DB at {self.chroma_host}:{self.chroma_port}")
            
            # Crea/ottieni collezioni
            self.alerts_collection = self.client.get_or_create_collection(
                name="security_alerts",
                metadata={"description": "Security alerts with embeddings"}
            )
            
            self.snippets_collection = self.client.get_or_create_collection(
                name="code_snippets",
                metadata={"description": "Code snippets with vulnerabilities"}
            )
            
            self.knowledge_collection = self.client.get_or_create_collection(
                name="knowledge_base",
                metadata={"description": "Security documentation and playbooks"}
            )
            
            logger.info("✓ Vector collections initialized")
        
        except Exception as e:
            logger.error(f"Failed to initialize Chroma DB: {e}")
            raise
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Genera embedding per testo.
        
        Args:
            text: Testo da embedare
            
        Returns:
            Lista float (embedding vector)
        """
        if not self._ensure_embedding_model():
            raise RuntimeError("Embedding model unavailable")

        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    # ============================================
    # ALERTS
    # ============================================
    
    def index_alert(
        self,
        alert_id: str,
        text: str,
        metadata: Dict[str, Any]
    ):
        """
        Indicizza alert nel vector DB.
        
        Args:
            alert_id: ID univoco alert
            text: Testo alert (title + description)
            metadata: Metadati (host_id, severity, etc.)
        """
        try:
            # Genera embedding
            embedding = self._generate_embedding(text)
            
            # Aggiungi a collection
            self.alerts_collection.add(
                ids=[alert_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata]
            )
            
            logger.debug(f"✓ Indexed alert {alert_id}")
        
        except Exception as e:
            logger.error(f"Failed to index alert {alert_id}: {e}")
    
    def search_alerts(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Ricerca semantica alert simili.
        
        Args:
            query: Query testuale
            top_k: Numero risultati
            filters: Filtri metadata (es: {"severity": "high"})
            
        Returns:
            Lista risultati con score
        """
        try:
            # Genera embedding query
            query_embedding = self._generate_embedding(query)
            
            # Ricerca
            results = self.alerts_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filters
            )
            
            # Formatta risultati
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'alert_id': results['ids'][0][i],
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })
            
            logger.info(f"Found {len(formatted_results)} similar alerts")
            return formatted_results
        
        except Exception as e:
            logger.error(f"Alert search failed: {e}")
            return []
    
    # ============================================
    # CODE SNIPPETS
    # ============================================
    
    def index_code_snippet(
        self,
        snippet_id: str,
        code: str,
        metadata: Dict[str, Any]
    ):
        """
        Indicizza snippet codice nel vector DB.
        
        Args:
            snippet_id: ID univoco snippet
            code: Codice sorgente
            metadata: Metadati (vulnerability_type, severity, etc.)
        """
        try:
            # Genera embedding
            embedding = self._generate_embedding(code)
            
            # Aggiungi a collection
            self.snippets_collection.add(
                ids=[snippet_id],
                embeddings=[embedding],
                documents=[code],
                metadatas=[metadata]
            )
            
            logger.debug(f"✓ Indexed code snippet {snippet_id}")
        
        except Exception as e:
            logger.error(f"Failed to index snippet {snippet_id}: {e}")
    
    def search_code_snippets(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Ricerca semantica snippet codice simili.
        
        Args:
            query: Query (testo o codice)
            top_k: Numero risultati
            filters: Filtri metadata
            
        Returns:
            Lista risultati
        """
        try:
            query_embedding = self._generate_embedding(query)
            
            results = self.snippets_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filters
            )
            
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'snippet_id': results['ids'][0][i],
                    'code': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })
            
            logger.info(f"Found {len(formatted_results)} similar code snippets")
            return formatted_results
        
        except Exception as e:
            logger.error(f"Snippet search failed: {e}")
            return []
    
    # ============================================
    # KNOWLEDGE BASE
    # ============================================
    
    def index_knowledge_document(
        self,
        doc_id: str,
        text: str,
        metadata: Dict[str, Any]
    ):
        """
        Indicizza documento knowledge base.
        
        Args:
            doc_id: ID documento
            text: Testo documento
            metadata: Metadati (title, category, etc.)
        """
        try:
            embedding = self._generate_embedding(text)
            
            self.knowledge_collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata]
            )
            
            logger.debug(f"✓ Indexed knowledge document {doc_id}")
        
        except Exception as e:
            logger.error(f"Failed to index knowledge doc {doc_id}: {e}")
    
    def search_knowledge(
        self,
        query: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Ricerca semantica in knowledge base.
        
        Args:
            query: Query domanda
            top_k: Numero risultati
            
        Returns:
            Lista documenti rilevanti
        """
        try:
            query_embedding = self._generate_embedding(query)
            
            results = self.knowledge_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'doc_id': results['ids'][0][i],
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })
            
            return formatted_results
        
        except Exception as e:
            logger.error(f"Knowledge search failed: {e}")
            return []
    
    def close(self):
        """Chiudi connessione."""
        logger.info("Closing vector search engine")


# ============================================
# TESTING
# ============================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Inizializza engine (usa Chroma locale in memoria per test)
    engine = VectorSearchEngine()
    
    # Per test, usa client in-memory
    engine.client = chromadb.Client()
    engine.alerts_collection = engine.client.get_or_create_collection("test_alerts")
    
    # Test indicizzazione
    engine.index_alert(
        alert_id="alert_001",
        text="High CPU usage detected on server",
        metadata={"severity": "high", "host_id": "server-01"}
    )
    
    engine.index_alert(
        alert_id="alert_002",
        text="Suspicious process consuming excessive memory",
        metadata={"severity": "medium", "host_id": "server-02"}
    )
    
    # Test ricerca
    results = engine.search_alerts(query="CPU spike on server", top_k=2)
    
    print(f"\n{'='*60}")
    print("Search Results:")
    print(f"{'='*60}")
    for result in results:
        print(f"Alert ID: {result['alert_id']}")
        print(f"Text: {result['text']}")
        print(f"Metadata: {result['metadata']}")
        print(f"Distance: {result['distance']:.4f}")
        print()
