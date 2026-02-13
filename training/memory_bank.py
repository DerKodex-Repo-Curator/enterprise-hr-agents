"""
Memory Bank Manager - Agent Contextual Learning

This module provides persistent memory storage for agent learning without retraining.
Memories are facts/corrections that the agent can retrieve at runtime.

"""

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
import hashlib


@dataclass
class Memory:
    """A single memory/fact for the agent."""
    id: str
    content: str
    scope: str  # "global", "user:{id}", "session:{id}"
    source: str  # Where this memory came from
    category: str
    created_at: str
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "Memory":
        return cls(**data)


class MemoryBankManager:
    """
    Manage agent memories for contextual learning.
    
    Usage:
        bank = MemoryBankManager("training/exports/memories.json")
        
        # Add a memory (fact the agent should remember)
        bank.create_memory(
            content="Section 4.2 clarifies that remote work requires manager approval.",
            scope="global",
            source="human_feedback",
            category="policy"
        )
        
        # Retrieve relevant memories
        memories = bank.retrieve_memories("Can I work from home?", scope="global")
        
        # Export for production
        bank.export_all("prod_memories.json")
    """
    
    def __init__(self, storage_path: str = "training/exports/memories.json"):
        self.storage_path = storage_path
        self.memories: List[Memory] = []
        self._load()
    
    def _load(self):
        """Load memories from storage."""
        if os.path.exists(self.storage_path):
            with open(self.storage_path, "r") as f:
                data = json.load(f)
                self.memories = [Memory.from_dict(m) for m in data.get("memories", [])]
            print(f"🧠 Loaded {len(self.memories)} memories from {self.storage_path}")
        else:
            self.memories = []
            print(f"🧠 Created new MemoryBank at {self.storage_path}")
    
    def _save(self):
        """Save memories to storage."""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, "w") as f:
            json.dump({
                "version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "count": len(self.memories),
                "memories": [m.to_dict() for m in self.memories]
            }, f, indent=2)
        print(f"💾 Saved {len(self.memories)} memories to {self.storage_path}")
    
    def _generate_id(self, content: str) -> str:
        """Generate unique ID for a memory."""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(f"{content}{timestamp}".encode()).hexdigest()[:12]
    
    def create_memory(
        self,
        content: str,
        scope: str = "global",
        source: str = "human_feedback",
        category: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Memory:
        """
        Create a new memory.
        
        Args:
            content: The fact/information to remember
            scope: "global", "user:{id}", or "session:{id}"
            source: Where this memory came from (human_feedback, simulation, etc.)
            category: Category of memory (policy, benefits, compliance, etc.)
            metadata: Optional additional metadata
        """
        memory = Memory(
            id=self._generate_id(content),
            content=content,
            scope=scope,
            source=source,
            category=category,
            created_at=datetime.now().isoformat(),
            metadata=metadata or {}
        )
        self.memories.append(memory)
        self._save()
        print(f"✅ Created memory: {memory.id}")
        return memory
    
    def retrieve_memories(
        self,
        query: str,
        scope: Optional[str] = None,
        category: Optional[str] = None,
        k: int = 5
    ) -> List[Memory]:
        """
        Retrieve relevant memories for a query.
        
        For V1, uses simple keyword matching.
        For production, integrate with Vertex AI Vector Search.
        """
        candidates = self.memories
        
        # Filter by scope
        if scope:
            candidates = [m for m in candidates if m.scope == scope or m.scope == "global"]
        
        # Filter by category
        if category:
            candidates = [m for m in candidates if m.category == category]
        
        # Simple keyword matching
        query_words = set(query.lower().split())
        scored = []
        for memory in candidates:
            memory_words = set(memory.content.lower().split())
            overlap = len(query_words & memory_words)
            scored.append((overlap, memory))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored[:k] if _ > 0]  # Only return memories with some overlap
    
    def format_for_prompt(self, memories: List[Memory]) -> str:
        """Format memories as context for the agent prompt."""
        if not memories:
            return ""
        
        lines = ["Relevant information from memory:\n"]
        for m in memories:
            lines.append(f"• {m.content}")
            if m.source:
                lines.append(f"  (Source: {m.source})")
        
        return "\n".join(lines)
    
    def export_all(self, path: str):
        """Export all memories to a JSON file."""
        with open(path, "w") as f:
            json.dump({
                "version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "source": self.storage_path,
                "count": len(self.memories),
                "memories": [m.to_dict() for m in self.memories]
            }, f, indent=2)
        print(f"📤 Exported {len(self.memories)} memories to {path}")
    
    def import_memories(self, path: str, merge: bool = True):
        """
        Import memories from a JSON file.
        
        Args:
            path: Path to JSON file
            merge: If True, merge with existing. If False, replace.
        """
        with open(path, "r") as f:
            data = json.load(f)
            new_memories = [Memory.from_dict(m) for m in data.get("memories", [])]
        
        if merge:
            existing_ids = {m.id for m in self.memories}
            for m in new_memories:
                if m.id not in existing_ids:
                    self.memories.append(m)
        else:
            self.memories = new_memories
        
        self._save()
        print(f"📥 Imported {len(new_memories)} memories (merge={merge})")
    
    def export_to_gcs(self, bucket: str, prefix: str = "training/"):
        """Export memories to Google Cloud Storage."""
        try:
            from google.cloud import storage
            
            client = storage.Client()
            bucket_obj = client.bucket(bucket)
            blob = bucket_obj.blob(f"{prefix}memories.json")
            
            data = json.dumps({
                "version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "count": len(self.memories),
                "memories": [m.to_dict() for m in self.memories]
            })
            
            blob.upload_from_string(data, content_type="application/json")
            print(f"☁️ Exported to gs://{bucket}/{prefix}memories.json")
            
        except ImportError:
            print("❌ google-cloud-storage not installed")
    
    def get_by_scope(self, scope: str) -> List[Memory]:
        """Get all memories for a specific scope."""
        return [m for m in self.memories if m.scope == scope]
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        for i, m in enumerate(self.memories):
            if m.id == memory_id:
                del self.memories[i]
                self._save()
                print(f"🗑️ Deleted memory: {memory_id}")
                return True
        return False
    
    def stats(self) -> dict:
        """Get statistics about the memory bank."""
        scopes: Dict[str, int] = {}
        categories: Dict[str, int] = {}
        sources: Dict[str, int] = {}
        
        for m in self.memories:
            scopes[m.scope] = scopes.get(m.scope, 0) + 1
            categories[m.category] = categories.get(m.category, 0) + 1
            sources[m.source] = sources.get(m.source, 0) + 1
        
        return {
            "total_memories": len(self.memories),
            "scopes": scopes,
            "categories": categories,
            "sources": sources
        }


# ==============================================================================
# CLI Interface
# ==============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Memory Bank CLI")
    parser.add_argument("--store", default="training/exports/memories.json")
    parser.add_argument("--add", action="store_true", help="Add a memory interactively")
    parser.add_argument("--export", type=str, help="Export to JSON path")
    parser.add_argument("--import-file", type=str, help="Import from JSON path")
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    
    args = parser.parse_args()
    bank = MemoryBankManager(args.store)
    
    if args.stats:
        stats = bank.stats()
        print(f"\n🧠 Memory Bank Statistics:")
        print(f"   Total: {stats['total_memories']}")
        print(f"   Scopes: {stats['scopes']}")
        print(f"   Categories: {stats['categories']}")
    
    elif args.add:
        print("\n📝 Add New Memory")
        content = input("Content (fact to remember): ")
        scope = input("Scope (global/user:id/session:id): ") or "global"
        source = input("Source: ") or "human_feedback"
        category = input("Category: ") or "general"
        
        bank.create_memory(content, scope, source, category)
    
    elif args.export:
        bank.export_all(args.export)
    
    elif args.import_file:
        bank.import_memories(args.import_file)
    
    elif args.self_test:
        print("\n🧪 Running self-test...")
        
        test_bank = MemoryBankManager("training/exports/test_memories.json")
        
        test_bank.create_memory(
            content="Remote work requires manager approval per Section 4.2",
            scope="global",
            source="human_feedback",
            category="policy"
        )
        
        memories = test_bank.retrieve_memories("Can I work remotely?")
        assert len(memories) >= 1, "Should retrieve memory"
        
        prompt = test_bank.format_for_prompt(memories)
        assert "remote" in prompt.lower(), "Prompt should contain memory"
        
        print("✅ All self-tests passed!")
        os.remove("training/exports/test_memories.json")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
