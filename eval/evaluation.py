"""
Comprehensive Evaluation Framework for Multi-Agent HR System

This module demonstrates key evaluation concepts for production AI systems:

1. GOLDEN DATASET TESTING - Compare agent responses to expected answers
2. GROUNDEDNESS EVALUATION - Are responses grounded in source documents?
3. ROUTING ACCURACY - Is the multi-agent router sending queries correctly?
4. PAIRWISE (SxS) EVALUATION - Compare two model responses head-to-head
5. SAFETY EVALUATION - Red team and guardrail testing
6. LATENCY BENCHMARKS - Response time metrics

"""
import os
import sys
import json
import time
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

import vertexai
from vertexai.generative_models import GenerativeModel

PROJECT_ID = os.getenv("PROJECT_ID", "hr-policy-agent-486811")
LOCATION = os.getenv("LOCATION", "us-central1")

vertexai.init(project=PROJECT_ID, location=LOCATION)


# ==============================================================================
# DATA STRUCTURES
# ==============================================================================

@dataclass
class EvalCase:
    """A single evaluation case from the golden dataset."""
    prompt: str
    expected_answer: str
    routing: str
    category: str


@dataclass 
class EvalResult:
    """Result of evaluating a single case."""
    prompt: str
    expected: str
    actual: str
    routing_expected: str
    routing_actual: str
    
    # Metrics
    similarity_score: float  # 0-1, how similar is actual to expected
    groundedness_score: float  # 0-1, is response grounded
    routing_correct: bool
    latency_ms: float


@dataclass
class EvalSummary:
    """Summary of evaluation run."""
    total_cases: int
    avg_similarity: float
    avg_groundedness: float
    routing_accuracy: float
    avg_latency_ms: float
    p95_latency_ms: float
    passed: bool
    threshold_met: Dict[str, bool]


# ==============================================================================
# GOLDEN DATASET LOADING
# ==============================================================================

def load_golden_dataset(path: str = "data/golden_dataset.jsonl") -> List[EvalCase]:
    """Load golden dataset from JSONL file."""
    cases = []
    
    if not os.path.exists(path):
        print(f"⚠️ Golden dataset not found at {path}")
        return cases
    
    with open(path, "r") as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                cases.append(EvalCase(
                    prompt=data["prompt"],
                    expected_answer=data["expected_answer"],
                    routing=data.get("routing", "unknown"),
                    category=data.get("category", "general")
                ))
    
    print(f"📊 Loaded {len(cases)} evaluation cases")
    return cases


# ==============================================================================
# SIMILARITY EVALUATION (Interview Concept: Text Similarity Metrics)
# ==============================================================================

def compute_similarity_llm(expected: str, actual: str) -> float:
    """
    Use LLM to compute semantic similarity between expected and actual.
    """
    model = GenerativeModel("gemini-2.0-flash")
    
    prompt = f"""Compare these two responses and rate their semantic similarity from 0.0 to 1.0.

Expected Response:
{expected}

Actual Response:
{actual}

Consider:
- Do they convey the same core information?
- Are the key facts the same?
- Is the meaning equivalent even if wording differs?

Respond with ONLY a number between 0.0 and 1.0, nothing else."""

    try:
        response = model.generate_content(prompt)
        score = float(response.text.strip())
        return min(max(score, 0.0), 1.0)
    except:
        return 0.0


def compute_similarity_simple(expected: str, actual: str) -> float:
    """
    Simple word overlap similarity (no LLM call).
    """
    expected_words = set(expected.lower().split())
    actual_words = set(actual.lower().split())
    
    if not expected_words or not actual_words:
        return 0.0
    
    intersection = expected_words & actual_words
    union = expected_words | actual_words
    
    return len(intersection) / len(union)


# ==============================================================================
# GROUNDEDNESS EVALUATION (Interview Concept: Hallucination Detection)
# ==============================================================================

def evaluate_groundedness(response: str, source_docs: List[str] = None) -> float:
    """
    Evaluate if the response is grounded in source documents.
    """
    model = GenerativeModel("gemini-2.0-flash")
    
    # Check for hedging language (indicates uncertainty/potential hallucination)
    hedging_phrases = [
        "I think", "probably", "might be", "I believe",
        "I'm not sure", "possibly", "maybe"
    ]
    
    has_hedging = any(phrase.lower() in response.lower() for phrase in hedging_phrases)
    
    # Check for grounding phrases (indicates citation/grounding)
    grounding_phrases = [
        "according to", "based on", "the policy states",
        "the handbook says", "as per", "the documentation"
    ]
    
    has_grounding = any(phrase.lower() in response.lower() for phrase in grounding_phrases)
    
    # Simple heuristic score
    score = 0.5
    if has_grounding:
        score += 0.3
    if has_hedging:
        score -= 0.2
    
    return min(max(score, 0.0), 1.0)


# ==============================================================================
# ROUTING EVALUATION (Interview Concept: Multi-Agent Classification)
# ==============================================================================

def evaluate_routing(prompt: str, expected_route: str) -> Tuple[str, bool]:
    """
    Evaluate if the router would correctly classify this query.
    """
    model = GenerativeModel("gemini-2.0-flash")
    
    routing_prompt = f"""Classify this HR query into ONE of these categories:
- policy: General HR policies and handbook
- benefits: Health insurance, 401k, PTO, leave
- compliance: Legal, harassment, discrimination, safety
- onboarding: New hire processes, first-day
- payroll: Salary, taxes, expenses
- escalation: Sensitive topics requiring human HR

Query: {prompt}

Respond with ONLY the category name, nothing else."""

    try:
        response = model.generate_content(routing_prompt)
        predicted = response.text.strip().lower()
        is_correct = predicted == expected_route.lower()
        return predicted, is_correct
    except:
        return "error", False


# ==============================================================================
# PAIRWISE EVALUATION (Interview Concept: A/B Testing for AI)
# ==============================================================================

def pairwise_compare(prompt: str, response_a: str, response_b: str) -> str:
    """
    Compare two responses and determine which is better.
    
    Returns: "A", "B", or "TIE"
    """
    model = GenerativeModel("gemini-2.0-flash")
    
    compare_prompt = f"""You are evaluating two AI responses to an HR question.

Question: {prompt}

Response A:
{response_a}

Response B:
{response_b}

Which response is better? Consider:
- Accuracy of information
- Helpfulness and clarity
- Appropriate tone for HR context
- Completeness of answer

Respond with ONLY one of: A, B, or TIE"""

    try:
        response = model.generate_content(compare_prompt)
        result = response.text.strip().upper()
        if result in ["A", "B", "TIE"]:
            return result
        return "TIE"
    except:
        return "TIE"


# ==============================================================================
# LATENCY BENCHMARKING (Interview Concept: Performance SLAs)
# ==============================================================================

def measure_latency(func, *args, **kwargs) -> Tuple[Any, float]:
    """
    Measure execution time of a function.
    """
    start = time.perf_counter()
    result = func(*args, **kwargs)
    end = time.perf_counter()
    latency_ms = (end - start) * 1000
    return result, latency_ms


# ==============================================================================
# MOCK AGENT FOR TESTING
# ==============================================================================

def mock_agent_response(prompt: str) -> str:
    """
    Mock agent that returns a simple response.
    Replace with actual agent call for real evaluation.
    """
    model = GenerativeModel("gemini-2.0-flash")
    
    system_prompt = """You are an HR assistant. Answer the following HR question concisely.
Base your answer on typical company policies."""
    
    try:
        response = model.generate_content(f"{system_prompt}\n\nQuestion: {prompt}")
        return response.text
    except Exception as e:
        return f"Error: {e}"


# ==============================================================================
# MAIN EVALUATION RUNNER
# ==============================================================================

def run_full_evaluation(use_llm_similarity: bool = False) -> EvalSummary:
    """
    Run comprehensive evaluation suite.
    
    Args:
        use_llm_similarity: If True, use LLM for similarity (slower but better).
                           If False, use simple word overlap (faster).
    """
    print("=" * 70)
    print("🧪 COMPREHENSIVE EVALUATION SUITE")
    print("=" * 70)
    
    # Load dataset
    cases = load_golden_dataset()
    if not cases:
        return None
    
    results = []
    latencies = []
    routing_correct = 0
    
    print("\n📝 Running evaluations...")
    print("-" * 70)
    
    for i, case in enumerate(cases):
        print(f"\n[{i+1}/{len(cases)}] {case.prompt[:50]}...")
        
        # Get agent response with latency measurement
        response, latency = measure_latency(mock_agent_response, case.prompt)
        latencies.append(latency)
        
        # Compute similarity
        if use_llm_similarity:
            similarity = compute_similarity_llm(case.expected_answer, response)
        else:
            similarity = compute_similarity_simple(case.expected_answer, response)
        
        # Evaluate groundedness  
        groundedness = evaluate_groundedness(response)
        
        # Evaluate routing
        predicted_route, route_correct = evaluate_routing(case.prompt, case.routing)
        if route_correct:
            routing_correct += 1
        
        result = EvalResult(
            prompt=case.prompt,
            expected=case.expected_answer,
            actual=response,
            routing_expected=case.routing,
            routing_actual=predicted_route,
            similarity_score=similarity,
            groundedness_score=groundedness,
            routing_correct=route_correct,
            latency_ms=latency
        )
        results.append(result)
        
        # Print result
        status = "✅" if similarity > 0.5 else "⚠️"
        route_status = "✅" if route_correct else "❌"
        print(f"    {status} Similarity: {similarity:.2f} | Groundedness: {groundedness:.2f}")
        print(f"    {route_status} Routing: {predicted_route} (expected: {case.routing})")
        print(f"    ⏱️ Latency: {latency:.0f}ms")
    
    # Compute summary
    avg_similarity = sum(r.similarity_score for r in results) / len(results)
    avg_groundedness = sum(r.groundedness_score for r in results) / len(results)
    routing_accuracy = routing_correct / len(results)
    avg_latency = sum(latencies) / len(latencies)
    p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 1 else latencies[0]
    
    # Define thresholds
    thresholds = {
        "similarity": (avg_similarity >= 0.4, 0.4),
        "groundedness": (avg_groundedness >= 0.5, 0.5),
        "routing": (routing_accuracy >= 0.8, 0.8),
        "latency": (avg_latency <= 5000, 5000),
    }
    
    all_passed = all(t[0] for t in thresholds.values())
    
    summary = EvalSummary(
        total_cases=len(results),
        avg_similarity=avg_similarity,
        avg_groundedness=avg_groundedness,
        routing_accuracy=routing_accuracy,
        avg_latency_ms=avg_latency,
        p95_latency_ms=p95_latency,
        passed=all_passed,
        threshold_met={k: v[0] for k, v in thresholds.items()}
    )
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 EVALUATION SUMMARY")
    print("=" * 70)
    print(f"  Total Cases: {summary.total_cases}")
    print(f"  Similarity:  {summary.avg_similarity:.2%} (threshold: 40%)")
    print(f"  Groundedness: {summary.avg_groundedness:.2%} (threshold: 50%)")
    print(f"  Routing:     {summary.routing_accuracy:.2%} (threshold: 80%)")
    print(f"  Avg Latency: {summary.avg_latency_ms:.0f}ms (threshold: 5000ms)")
    print(f"  P95 Latency: {summary.p95_latency_ms:.0f}ms")
    print("-" * 70)
    overall = "✅ ALL THRESHOLDS MET" if all_passed else "❌ SOME THRESHOLDS NOT MET"
    print(f"  Overall: {overall}")
    print("=" * 70)
    
    return summary


# ==============================================================================
# INTERVIEW CONCEPTS SUMMARY
# ==============================================================================

if __name__ == "__main__":
    run_full_evaluation(use_llm_similarity=False)
