"""
Medical Knowledge Base (RAG Context Provider)
Loads medical markdown files and provides relevant context to the doctor agent.

This module enables the doctor feature by:
1. Loading all medical .md files from the medical_data folder
2. Building a searchable TF-IDF index for fast retrieval
3. Returning the most relevant medical content for each patient query
4. That relevant content is injected as context into the LLM messages
"""
import logging
import re
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Default path to medical data
_DEFAULT_MEDICAL_DATA_DIR = Path(__file__).parent / "medical_data" / "medical_data"


@dataclass
class MedicalChunk:
    """A single chunk of medical information from a document."""
    topic: str           # e.g. "Abdominal pain"
    section: str         # e.g. "What causes abdominal pain?"
    content: str         # The actual text content
    source_file: str     # Original filename for reference


@dataclass
class SearchResult:
    """A search result with relevance score."""
    chunk: MedicalChunk
    score: float


class MedicalKnowledgeBase:
    """
    Loads medical markdown files and provides relevant context for patient queries.

    Uses TF-IDF vectorization + cosine similarity for fast, accurate retrieval.
    No external vector database needed - runs entirely in memory.

    Flow:
        Patient says "my stomach hurts" ->
        Search finds "abdominal_pain.md" sections ->
        Top sections injected as context into LLM ->
        Doctor agent gives informed response
    """

    def __init__(self, data_dir: str | Path | None = None, max_chunks: int = 5000):
        """
        Initialize the medical knowledge base.

        Args:
            data_dir: Path to the medical_data directory containing .md files.
                      Defaults to ./medical_data/medical_data/
            max_chunks: Maximum number of chunks to index (prevents memory issues).
        """
        self.data_dir = Path(data_dir) if data_dir else _DEFAULT_MEDICAL_DATA_DIR
        self.max_chunks = max_chunks
        self.chunks: list[MedicalChunk] = []
        self._tfidf_matrix = None
        self._vectorizer = None
        self._is_loaded = False

    def load(self):
        """
        Load all medical markdown files and build the search index.
        Call this once at startup.
        """
        if self._is_loaded:
            logger.info("Medical knowledge base already loaded.")
            return

        if not self.data_dir.exists():
            logger.warning(
                f"Medical data directory not found: {self.data_dir}. "
                "Doctor agent will work without medical context."
            )
            self._is_loaded = True
            return

        # Step 1: Load and chunk all markdown files
        logger.info(f"Loading medical data from: {self.data_dir}")
        md_files = sorted(self.data_dir.glob("*.md"))
        logger.info(f"Found {len(md_files)} medical documents.")

        for md_file in md_files:
            try:
                content = md_file.read_text(encoding="utf-8")
                topic = self._extract_topic(content, md_file.stem)
                file_chunks = self._split_into_sections(content, topic, md_file.stem)
                self.chunks.extend(file_chunks)
            except Exception as e:
                logger.warning(f"Error loading {md_file.name}: {e}")

            if len(self.chunks) >= self.max_chunks:
                logger.warning(
                    f"Reached max_chunks limit ({self.max_chunks}). Stopping load."
                )
                self.chunks = self.chunks[:self.max_chunks]
                break

        logger.info(f"Loaded {len(self.chunks)} medical knowledge chunks.")

        # Step 2: Build TF-IDF search index
        if self.chunks:
            self._build_index()

        self._is_loaded = True
        logger.info("Medical knowledge base loaded and ready.")

    def search(self, query: str, top_k: int = 3) -> list[SearchResult]:
        """
        Search the medical knowledge base for content relevant to the query.

        Args:
            query: The patient's message or symptoms description.
            top_k: Number of top results to return.

        Returns:
            List of SearchResult objects, sorted by relevance (highest first).
        """
        if not self._is_loaded or not self.chunks or self._tfidf_matrix is None:
            return []

        try:
            from sklearn.metrics.pairwise import cosine_similarity

            # Transform query into TF-IDF vector
            query_vector = self._vectorizer.transform([query])

            # Compute cosine similarity against all chunks
            similarities = cosine_similarity(
                query_vector, self._tfidf_matrix
            ).flatten()

            # Get top-k indices
            top_indices = similarities.argsort()[::-1][:top_k]

            results = []
            for idx in top_indices:
                score = float(similarities[idx])
                if score > 0.01:  # Minimum relevance threshold
                    results.append(SearchResult(
                        chunk=self.chunks[idx],
                        score=score,
                    ))

            return results

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def get_context_for_patient(
        self, patient_message: str, max_tokens: int = 1500
    ) -> str:
        """
        Get formatted medical context to inject into the LLM system message.

        This is the main method called by the doctor agent before each LLM call.
        It searches for relevant medical info and formats it for the LLM.

        Args:
            patient_message: What the patient said.
            max_tokens: Approximate max tokens for the context
                        (to avoid exceeding LLM limits).

        Returns:
            Formatted string with relevant medical information,
            or empty string if nothing found.
        """
        results = self.search(patient_message, top_k=3)

        if not results:
            return ""

        context_parts = []
        current_length = 0
        # Rough estimate: 1 token ~ 4 characters
        max_chars = max_tokens * 4

        for result in results:
            chunk = result.chunk
            section_text = f"### {chunk.topic} - {chunk.section}\n{chunk.content}"

            if current_length + len(section_text) > max_chars:
                break

            context_parts.append(section_text)
            current_length += len(section_text)

        if not context_parts:
            return ""

        header = (
            "## Medical Reference Context (from verified medical sources)\n"
            "Use the following medical information to provide more accurate and "
            "informed guidance to the patient. Reference this knowledge when "
            "explaining symptoms, causes, treatments, or when to see a doctor.\n\n"
        )
        return header + "\n\n---\n\n".join(context_parts)

    # -- Private helpers ------------------------------------------------

    def _extract_topic(self, content: str, filename: str) -> str:
        """Extract the main topic from a markdown file."""
        # Try to get the first H1 heading
        match = re.match(r"^#\s+(.+)", content)
        if match:
            return match.group(1).strip()
        # Fallback: use filename
        return filename.replace("_", " ").title()

    def _split_into_sections(
        self, content: str, topic: str, filename: str
    ) -> list[MedicalChunk]:
        """
        Split a markdown document into sections by H2 headings.
        Each section becomes a searchable chunk.
        """
        chunks = []

        # Split by ## headings
        sections = re.split(r"\n(?=## )", content)

        for section in sections:
            section = section.strip()
            if not section or len(section) < 30:
                continue

            # Extract section heading
            heading_match = re.match(r"##\s+(.+)", section)
            section_name = (
                heading_match.group(1).strip() if heading_match else "General"
            )

            # Skip very short sections
            if len(section.strip()) < 30:
                continue

            chunks.append(MedicalChunk(
                topic=topic,
                section=section_name,
                content=section.strip(),
                source_file=filename,
            ))

        # If no sections found, treat the whole document as one chunk
        if not chunks and len(content.strip()) > 30:
            chunks.append(MedicalChunk(
                topic=topic,
                section="Overview",
                content=content.strip()[:2000],  # Limit size
                source_file=filename,
            ))

        return chunks

    def _build_index(self):
        """Build the TF-IDF vector index from all loaded chunks."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer

            # Create text representations of each chunk
            texts = [
                f"{chunk.topic} {chunk.section} {chunk.content}"
                for chunk in self.chunks
            ]

            # Build TF-IDF matrix
            self._vectorizer = TfidfVectorizer(
                max_features=10000,
                stop_words="english",
                ngram_range=(1, 2),    # Unigrams + bigrams for better matching
                max_df=0.95,           # Ignore terms in >95% of docs
                min_df=2,              # Ignore terms in <2 docs
            )
            self._tfidf_matrix = self._vectorizer.fit_transform(texts)

            logger.info(
                f"TF-IDF index built: {self._tfidf_matrix.shape[0]} docs x "
                f"{self._tfidf_matrix.shape[1]} features"
            )

        except ImportError:
            logger.error(
                "scikit-learn not installed. Install with: pip install scikit-learn\n"
                "Medical knowledge search will be disabled."
            )
            self._tfidf_matrix = None
            self._vectorizer = None

    def get_stats(self) -> dict:
        """Get statistics about the loaded knowledge base."""
        return {
            "loaded": self._is_loaded,
            "data_dir": str(self.data_dir),
            "total_chunks": len(self.chunks),
            "index_built": self._tfidf_matrix is not None,
        }
