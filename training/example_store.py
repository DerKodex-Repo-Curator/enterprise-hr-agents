"""
Example Store - Few-Shot Learning for Agent Training

This module provides a way to store corrections and examples that can be:
1. Used for few-shot prompting during inference
2. Exported to production for consistent agent behavior

"""

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional
import hashlib


@dataclass
class Example:
    """A single training example with correction."""
    id: str
    query: str
    bad_response: Optional[str]
    corrected_response: str
    reason: str
    category: str  # e.g., "policy", "benefits", "compliance"
    created_at: str
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "Example":
        return cls(**data)


class ExampleStore:
    """
    Store and retrieve few-shot examples for agent training.
    
    Usage:
        store = ExampleStore("training/exports/examples.json")
        
        # Add a correction
        store.add_correction(
            query="What's the CEO's salary?",
            bad_response="The CEO earns $5M annually...",
            corrected_response="I cannot disclose individual salary information.",
            reason="Privacy violation - salary is confidential",
            category="compliance"
        )
        
        # Get few-shot examples for a query
        examples = store.get_examples("Tell me about salaries", k=3)
        
        # Export for production
        store.export_to_json("prod_examples.json")
    """
    
    def __init__(self, storage_path: str = "training/exports/examples.json"):
        self.storage_path = storage_path
        self.examples: List[Example] = []
        self._load()
    
    def _load(self):
        """Load examples from storage."""
        if os.path.exists(self.storage_path):
            with open(self.storage_path, "r") as f:
                data = json.load(f)
                self.examples = [Example.from_dict(e) for e in data.get("examples", [])]
            print(f"📦 Loaded {len(self.examples)} examples from {self.storage_path}")
        else:
            self.examples = []
            print(f"📦 Created new ExampleStore at {self.storage_path}")
    
    def _save(self):
        """Save examples to storage."""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, "w") as f:
            json.dump({
                "version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "count": len(self.examples),
                "examples": [e.to_dict() for e in self.examples]
            }, f, indent=2)
        print(f"💾 Saved {len(self.examples)} examples to {self.storage_path}")
    
    def _generate_id(self, query: str) -> str:
        """Generate unique ID for an example."""
        timestamp = datetime.now().isoformat()
        content = f"{query}{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def add_correction(
        self,
        query: str,
        corrected_response: str,
        reason: str,
        category: str = "general",
        bad_response: Optional[str] = None
    ) -> Example:
        """
        Add a correction example to the store.
        
        Args:
            query: The user query that triggered the bad response
            corrected_response: The correct response the agent should give
            reason: Why this correction was needed
            category: Category of the query (policy, benefits, etc.)
            bad_response: Optional - the original bad response
        """
        example = Example(
            id=self._generate_id(query),
            query=query,
            bad_response=bad_response,
            corrected_response=corrected_response,
            reason=reason,
            category=category,
            created_at=datetime.now().isoformat()
        )
        self.examples.append(example)
        self._save()
        print(f"✅ Added example: {example.id}")
        return example
    
    def get_examples(self, query: str, k: int = 3, category: Optional[str] = None) -> List[Example]:
        """
        Retrieve relevant examples for a query.
        
        For V1, uses simple keyword matching. 
        For production, integrate with Vertex AI Vector Search.
        
        Args:
            query: The user query to find similar examples for
            k: Number of examples to return
            category: Optional - filter by category
        """
        # Filter by category if specified
        candidates = self.examples
        if category:
            candidates = [e for e in candidates if e.category == category]
        
        # Simple keyword matching (replace with embeddings for production)
        query_words = set(query.lower().split())
        scored = []
        for example in candidates:
            example_words = set(example.query.lower().split())
            overlap = len(query_words & example_words)
            scored.append((overlap, example))
        
        # Sort by overlap score (descending)
        scored.sort(key=lambda x: x[0], reverse=True)
        
        return [e for _, e in scored[:k]]
    
    def format_for_prompt(self, examples: List[Example]) -> str:
        """Format examples as few-shot prompt context."""
        if not examples:
            return ""
        
        lines = ["Here are some examples of how to handle similar queries:\n"]
        for i, ex in enumerate(examples, 1):
            lines.append(f"Example {i}:")
            lines.append(f"  User: {ex.query}")
            lines.append(f"  Correct Response: {ex.corrected_response}")
            if ex.reason:
                lines.append(f"  (Reasoning: {ex.reason})")
            lines.append("")
        
        return "\n".join(lines)
    
    def export_to_json(self, path: str):
        """Export examples to a JSON file for production deployment."""
        with open(path, "w") as f:
            json.dump({
                "version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "source": self.storage_path,
                "count": len(self.examples),
                "examples": [e.to_dict() for e in self.examples]
            }, f, indent=2)
        print(f"📤 Exported {len(self.examples)} examples to {path}")
    
    def export_to_gcs(self, bucket: str, prefix: str = "training/"):
        """
        Export examples to Google Cloud Storage.
        
        Requires: google-cloud-storage
        """
        try:
            from google.cloud import storage
            
            client = storage.Client()
            bucket_obj = client.bucket(bucket)
            blob = bucket_obj.blob(f"{prefix}examples.json")
            
            data = json.dumps({
                "version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "source": self.storage_path,
                "count": len(self.examples),
                "examples": [e.to_dict() for e in self.examples]
            })
            
            blob.upload_from_string(data, content_type="application/json")
            print(f"☁️ Exported to gs://{bucket}/{prefix}examples.json")
            
        except ImportError:
            print("❌ google-cloud-storage not installed. Run: pip install google-cloud-storage")
    
    @classmethod
    def load_from_json(cls, path: str) -> "ExampleStore":
        """Load an ExampleStore from an exported JSON file."""
        store = cls(storage_path=path)
        return store
    
    def stats(self) -> dict:
        """Get statistics about the example store."""
        categories = {}
        for ex in self.examples:
            categories[ex.category] = categories.get(ex.category, 0) + 1
        
        return {
            "total_examples": len(self.examples),
            "categories": categories,
            "storage_path": self.storage_path
        }


# ==============================================================================
# CLI Interface
# ==============================================================================

def main():
    """CLI for managing the Example Store."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Example Store CLI")
    parser.add_argument("--store", default="training/exports/examples.json", 
                       help="Path to example store")
    parser.add_argument("--add-correction", action="store_true",
                       help="Add a new correction interactively")
    parser.add_argument("--export", type=str, help="Export to JSON path")
    parser.add_argument("--export-gcs", type=str, help="Export to GCS bucket")
    parser.add_argument("--stats", action="store_true", help="Show store statistics")
    parser.add_argument("--self-test", action="store_true", help="Run self-test")
    
    args = parser.parse_args()
    
    store = ExampleStore(args.store)
    
    if args.stats:
        stats = store.stats()
        print(f"\n📊 Example Store Statistics:")
        print(f"   Total examples: {stats['total_examples']}")
        print(f"   Categories: {stats['categories']}")
        print(f"   Storage: {stats['storage_path']}")
    
    elif args.add_correction:
        print("\n📝 Add New Correction")
        query = input("Query: ")
        bad_response = input("Bad response (optional, press Enter to skip): ") or None
        corrected_response = input("Correct response: ")
        reason = input("Reason for correction: ")
        category = input("Category (policy/benefits/compliance/general): ") or "general"
        
        store.add_correction(
            query=query,
            bad_response=bad_response,
            corrected_response=corrected_response,
            reason=reason,
            category=category
        )
    
    elif args.export:
        store.export_to_json(args.export)
    
    elif args.export_gcs:
        store.export_to_gcs(args.export_gcs)
    
    elif args.self_test:
        print("\n🧪 Running self-test...")
        
        # Create test store
        test_store = ExampleStore("training/exports/test_examples.json")
        
        # Add test examples
        test_store.add_correction(
            query="What is the CEO salary?",
            corrected_response="I cannot disclose individual salary information.",
            reason="Privacy - salary is confidential",
            category="compliance"
        )
        
        test_store.add_correction(
            query="How much vacation do I get?",
            corrected_response="Full-time employees receive 15 days of PTO annually.",
            reason="Standard policy answer",
            category="policy"
        )
        
        # Test retrieval
        examples = test_store.get_examples("Tell me about CEO compensation", k=2)
        assert len(examples) >= 1, "Should retrieve at least 1 example"
        
        # Test formatting
        prompt = test_store.format_for_prompt(examples)
        assert "CEO" in prompt or "salary" in prompt, "Prompt should contain relevant content"
        
        print("✅ All self-tests passed!")
        
        # Cleanup
        os.remove("training/exports/test_examples.json")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
