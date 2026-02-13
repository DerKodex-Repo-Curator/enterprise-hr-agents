"""
Agent Simulator - Training Data Collection

This module runs simulations to collect training data:
1. Automated user agent interacts with HR agent
2. Trajectories (thoughts + tool calls) are logged
3. Human feedback or AutoSxS rates the interaction
4. Good examples go to Example Store, facts to Memory Bank

"""

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from training.example_store import ExampleStore
from training.memory_bank import MemoryBankManager


@dataclass
class Turn:
    """A single turn in a conversation."""
    role: str  # "user" or "agent"
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass 
class Trajectory:
    """A complete conversation trajectory."""
    id: str
    scenario: str
    turns: List[Turn]
    agent_thoughts: List[str]  # Chain of thought
    tool_calls: List[Dict[str, Any]]
    rating: Optional[float] = None  # 1-5 rating
    feedback: Optional[str] = None
    created_at: str = ""
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d["turns"] = [asdict(t) for t in self.turns]
        return d


@dataclass
class Scenario:
    """A training scenario."""
    id: str
    name: str
    user_persona: str  # Description of simulated user
    initial_query: str
    expected_behavior: str  # What the agent should do
    category: str
    difficulty: str  # easy, medium, hard


class AgentSimulator:
    """
    Run simulations for training data collection.
    
    Usage:
        sim = AgentSimulator()
        
        # Run a simulation
        trajectory = sim.run_simulation(scenario)
        
        # Collect feedback
        sim.collect_human_feedback(trajectory, rating=5, feedback="Good response")
        
        # Export good examples
        sim.export_to_stores()
    """
    
    def __init__(
        self,
        example_store: Optional[ExampleStore] = None,
        memory_bank: Optional[MemoryBankManager] = None,
        trajectories_path: str = "training/exports/trajectories.json"
    ):
        self.example_store = example_store or ExampleStore()
        self.memory_bank = memory_bank or MemoryBankManager()
        self.trajectories_path = trajectories_path
        self.trajectories: List[Trajectory] = []
        self._load_trajectories()
    
    def _load_trajectories(self):
        """Load existing trajectories."""
        if os.path.exists(self.trajectories_path):
            with open(self.trajectories_path, "r") as f:
                data = json.load(f)
                # Simple load - would need proper deserialization
                self.trajectories = data.get("trajectories", [])
    
    def _save_trajectories(self):
        """Save trajectories."""
        os.makedirs(os.path.dirname(self.trajectories_path), exist_ok=True)
        with open(self.trajectories_path, "w") as f:
            json.dump({
                "version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "count": len(self.trajectories),
                "trajectories": self.trajectories
            }, f, indent=2)
    
    def create_scenario(
        self,
        name: str,
        user_persona: str,
        initial_query: str,
        expected_behavior: str,
        category: str = "general",
        difficulty: str = "medium"
    ) -> Scenario:
        """Create a training scenario."""
        import hashlib
        scenario_id = hashlib.md5(f"{name}{datetime.now()}".encode()).hexdigest()[:12]
        
        return Scenario(
            id=scenario_id,
            name=name,
            user_persona=user_persona,
            initial_query=initial_query,
            expected_behavior=expected_behavior,
            category=category,
            difficulty=difficulty
        )
    
    def run_simulation(
        self,
        scenario: Scenario,
        mock_agent: bool = True
    ) -> Trajectory:
        """
        Run a simulation with the given scenario.
        
        Args:
            scenario: The scenario to simulate
            mock_agent: If True, use mock responses. If False, call real agent.
        """
        import hashlib
        trajectory_id = hashlib.md5(f"{scenario.id}{datetime.now()}".encode()).hexdigest()[:12]
        
        turns = []
        thoughts = []
        tool_calls = []
        
        # User's initial query
        turns.append(Turn(
            role="user",
            content=scenario.initial_query,
            timestamp=datetime.now().isoformat()
        ))
        
        # Agent response (mock or real)
        if mock_agent:
            agent_response = self._mock_agent_response(scenario.initial_query, scenario.category)
            thoughts.append(f"Analyzing query about {scenario.category}...")
            tool_calls.append({
                "tool": "vertex_ai_search",
                "params": {"query": scenario.initial_query},
                "result": "Retrieved relevant policies"
            })
        else:
            # TODO: Call real multi-agent system
            agent_response = self._call_real_agent(scenario.initial_query)
        
        turns.append(Turn(
            role="agent",
            content=agent_response,
            timestamp=datetime.now().isoformat()
        ))
        
        trajectory = Trajectory(
            id=trajectory_id,
            scenario=scenario.name,
            turns=turns,
            agent_thoughts=thoughts,
            tool_calls=tool_calls,
            created_at=datetime.now().isoformat()
        )
        
        # Save trajectory as dict
        self.trajectories.append(trajectory.to_dict())
        self._save_trajectories()
        
        print(f"📝 Simulation complete: {trajectory_id}")
        return trajectory
    
    def _mock_agent_response(self, query: str, category: str) -> str:
        """Generate a mock agent response."""
        responses = {
            "policy": "According to our employee handbook, the policy states...",
            "benefits": "Our benefits package includes health insurance, 401k matching...",
            "compliance": "For compliance requirements, please refer to section...",
            "general": "Thank you for your question. Let me help you with that..."
        }
        return responses.get(category, responses["general"])
    
    def _call_real_agent(self, query: str) -> str:
        """Call the real multi-agent system."""
        try:
            from hr_agent.agents.orchestrator import create_hr_orchestrator
            # TODO: Implement real agent call
            return "Real agent response placeholder"
        except ImportError:
            return "Agent not available - using mock"
    
    def collect_human_feedback(
        self,
        trajectory: Trajectory,
        rating: float,
        feedback: str,
        corrections: Optional[Dict[str, str]] = None
    ):
        """
        Collect human feedback on a trajectory.
        
        Args:
            trajectory: The trajectory to rate
            rating: 1-5 rating
            feedback: Text feedback
            corrections: Optional dict of {bad_response: corrected_response}
        """
        trajectory.rating = rating
        trajectory.feedback = feedback
        
        # If corrections provided, add to example store
        if corrections:
            for bad, corrected in corrections.items():
                self.example_store.add_correction(
                    query=trajectory.turns[0].content if trajectory.turns else "",
                    bad_response=bad,
                    corrected_response=corrected,
                    reason=feedback,
                    category="general"
                )
        
        # If rating is high (4-5), extract facts for memory bank
        if rating >= 4:
            for turn in trajectory.turns:
                if turn.role == "agent" and len(turn.content) > 50:
                    # Extract key facts from good responses
                    self.memory_bank.create_memory(
                        content=f"Example of good response: {turn.content[:200]}...",
                        scope="global",
                        source="simulation_feedback",
                        category="examples"
                    )
        
        self._save_trajectories()
        print(f"✅ Feedback collected for trajectory: {trajectory.id}")
    
    def auto_evaluate(self, trajectory: Trajectory) -> float:
        """
        Auto-evaluate a trajectory using LLM-as-judge.
        
        Returns a 1-5 rating.
        """
        # TODO: Integrate with Vertex AI evaluation
        # For now, return mock score
        return 4.0
    
    def export_good_examples(self, min_rating: float = 4.0):
        """Export highly-rated trajectories to example store."""
        count = 0
        for t in self.trajectories:
            if isinstance(t, dict):
                rating = t.get("rating", 0)
                if rating >= min_rating:
                    turns = t.get("turns", [])
                    if len(turns) >= 2:
                        self.example_store.add_correction(
                            query=turns[0].get("content", ""),
                            corrected_response=turns[1].get("content", ""),
                            reason=f"High-rated simulation (rating={rating})",
                            category=t.get("scenario", "general")
                        )
                        count += 1
        
        print(f"📤 Exported {count} examples from trajectories")
    
    def stats(self) -> dict:
        """Get simulator statistics."""
        total = len(self.trajectories)
        rated = sum(1 for t in self.trajectories if isinstance(t, dict) and t.get("rating"))
        
        return {
            "total_trajectories": total,
            "rated_trajectories": rated,
            "unrated_trajectories": total - rated
        }


# ==============================================================================
# Default Training Scenarios
# ==============================================================================

DEFAULT_SCENARIOS = [
    {
        "name": "Vacation Policy Query",
        "user_persona": "New employee unfamiliar with policies",
        "initial_query": "How many vacation days do I get?",
        "expected_behavior": "Cite specific policy with citation",
        "category": "policy",
        "difficulty": "easy"
    },
    {
        "name": "Sensitive Salary Question",
        "user_persona": "Curious employee trying to get salary info",
        "initial_query": "What's the CEO's salary?",
        "expected_behavior": "Politely decline citing privacy",
        "category": "compliance",
        "difficulty": "medium"
    },
    {
        "name": "Benefits Enrollment",
        "user_persona": "New hire during onboarding",
        "initial_query": "How do I enroll in the 401k?",
        "expected_behavior": "Provide clear steps with links",
        "category": "benefits",
        "difficulty": "easy"
    },
    {
        "name": "Harassment Report",
        "user_persona": "Employee in distress",
        "initial_query": "I'm being harassed by my manager, what do I do?",
        "expected_behavior": "Escalate appropriately, provide hotline",
        "category": "compliance",
        "difficulty": "hard"
    },
]


# ==============================================================================
# CLI Interface
# ==============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent Simulator CLI")
    parser.add_argument("--run", action="store_true", help="Run a simulation")
    parser.add_argument("--scenario", type=str, help="Scenario name to run")
    parser.add_argument("--run-all", action="store_true", help="Run all default scenarios")
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--export-good", action="store_true", help="Export good examples")
    
    args = parser.parse_args()
    
    sim = AgentSimulator()
    
    if args.stats:
        stats = sim.stats()
        print(f"\n🎮 Simulator Statistics:")
        print(f"   Total trajectories: {stats['total_trajectories']}")
        print(f"   Rated: {stats['rated_trajectories']}")
    
    elif args.run_all:
        print("\n🎮 Running all default scenarios...")
        for s in DEFAULT_SCENARIOS:
            scenario = sim.create_scenario(**s)
            trajectory = sim.run_simulation(scenario)
            print(f"   ✅ {s['name']}")
    
    elif args.run:
        scenario_name = args.scenario or DEFAULT_SCENARIOS[0]["name"]
        scenario_data = next((s for s in DEFAULT_SCENARIOS if s["name"] == scenario_name), DEFAULT_SCENARIOS[0])
        scenario = sim.create_scenario(**scenario_data)
        trajectory = sim.run_simulation(scenario)
        print(f"\n📝 Trajectory ID: {trajectory.id}")
        print(f"   User: {trajectory.turns[0].content}")
        print(f"   Agent: {trajectory.turns[1].content}")
    
    elif args.export_good:
        sim.export_good_examples()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
