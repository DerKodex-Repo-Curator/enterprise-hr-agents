"""
Multi-Agent HR System Runner

Runs the HR orchestrator with guardrails in interactive mode.
Supports loading training examples for few-shot learning.
"""
import sys
import os
import asyncio
import argparse

# Add src and training to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from hr_agent.agents.orchestrator import hr_orchestrator, get_agents
from hr_agent.guardrails.input_guardrails import validate_input
from hr_agent.guardrails.output_guardrails import validate_output

# Training module imports
try:
    from training.example_store import ExampleStore
    from training.memory_bank import MemoryBankManager
    TRAINING_AVAILABLE = True
except ImportError:
    TRAINING_AVAILABLE = False
    ExampleStore = None
    MemoryBankManager = None

PROJECT_ID = os.getenv("PROJECT_ID", "hr-policy-agent-486811")


async def run_multi_agent(example_store=None, memory_bank=None):
    """
    Run the multi-agent HR system interactively.
    
    Args:
        example_store: Optional ExampleStore for few-shot learning
        memory_bank: Optional MemoryBankManager for contextual memories
    """
    
    print("=" * 60)
    print("HR Multi-Agent System")
    if example_store:
        stats = example_store.stats()
        print(f"📦 Loaded {stats['total_examples']} training examples")
    if memory_bank:
        stats = memory_bank.stats()
        print(f"🧠 Loaded {stats['total_memories']} memories")
    print("=" * 60)
    print("\nAgents available:")
    for name, agent in get_agents().items():
        print(f"  - {name}: {agent.description[:50]}...")
    print("\n" + "=" * 60)
    print("Type 'quit' to exit, 'agents' to list agents")
    print("=" * 60 + "\n")
    
    # Create session service and runner
    session_service = InMemorySessionService()
    runner = Runner(
        agent=hr_orchestrator,
        app_name="hr-multi-agent",
        session_service=session_service,
    )
    
    # Create a session
    session = await session_service.create_session(
        app_name="hr-multi-agent",
        user_id="console_user",
    )
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["quit", "exit"]:
                print("Goodbye!")
                break
            
            if user_input.lower() == "agents":
                for name, agent in get_agents().items():
                    print(f"  {name}: {agent.description}")
                continue
            
            # Apply input guardrails
            is_safe, sanitized_input, metadata = validate_input(user_input)
            
            if not is_safe:
                print("Agent: I'm sorry, I cannot process that request.")
                continue
            
            if metadata.get("pii_detected"):
                print("[INFO] PII was detected and redacted from your message.")
            
            if metadata.get("escalation_required"):
                print("[INFO] This topic may require human HR involvement.")
            
            # Inject few-shot examples if available
            augmented_input = sanitized_input
            if example_store:
                examples = example_store.get_examples(sanitized_input, k=3)
                if examples:
                    few_shot_context = example_store.format_for_prompt(examples)
                    augmented_input = f"{few_shot_context}\n\nNow answer this query:\n{sanitized_input}"
                    print(f"[INFO] Loaded {len(examples)} relevant example(s)")
            
            # Inject memories if available
            if memory_bank:
                memories = memory_bank.retrieve_memories(sanitized_input, k=3)
                if memories:
                    memory_context = memory_bank.format_for_prompt(memories)
                    augmented_input = f"{memory_context}\n\n{augmented_input}"
                    print(f"[INFO] Loaded {len(memories)} relevant memory(ies)")
            
            # Run the multi-agent system
            print("Agent: ", end="", flush=True)
            
            async for event in runner.run_async(
                session_id=session.id,
                user_id="console_user",
                new_message=augmented_input,
            ):
                if hasattr(event, 'content') and event.content:
                    # Apply output guardrails
                    is_safe, sanitized_output, _ = validate_output(event.content)
                    print(sanitized_output)
            
            print()  # Newline after response
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Entry point with CLI argument support."""
    parser = argparse.ArgumentParser(description="HR Multi-Agent System with Training Support")
    parser.add_argument("--examples", type=str, 
                       help="Path to examples JSON file for few-shot learning")
    parser.add_argument("--memories", type=str,
                       help="Path to memories JSON file")
    parser.add_argument("--training-dir", type=str, default="training/exports",
                       help="Directory containing training data")
    
    args = parser.parse_args()
    
    if not PROJECT_ID:
        print("Please set PROJECT_ID environment variable.")
        return
    
    # Load training data if available
    example_store = None
    memory_bank = None
    
    if TRAINING_AVAILABLE:
        if args.examples:
            example_store = ExampleStore(args.examples)
        elif os.path.exists(f"{args.training_dir}/examples.json"):
            example_store = ExampleStore(f"{args.training_dir}/examples.json")
        
        if args.memories:
            memory_bank = MemoryBankManager(args.memories)
        elif os.path.exists(f"{args.training_dir}/memories.json"):
            memory_bank = MemoryBankManager(f"{args.training_dir}/memories.json")
    
    asyncio.run(run_multi_agent(example_store=example_store, memory_bank=memory_bank))


if __name__ == "__main__":
    main()

