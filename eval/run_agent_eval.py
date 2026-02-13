"""
Live Evaluation of Deployed HR Agent
Uses the golden dataset to evaluate the live deployed Reasoning Engine.
"""
import os
import sys
import json
import time
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

import vertexai
from vertexai.preview import reasoning_engines
from vertexai.generative_models import GenerativeModel

# Configuration
PROJECT_ID = os.getenv("PROJECT_ID", "hr-policy-agent-486811")
LOCATION = os.getenv("LOCATION", "us-central1")
# Updated to debug agent with stdout logging
AGENT_RESOURCE = "projects/121452631372/locations/us-central1/reasoningEngines/8093499594500997120"

vertexai.init(project=PROJECT_ID, location=LOCATION)

@dataclass
class EvalCase:
    prompt: str
    expected_answer: str
    routing: str
    category: str

@dataclass
class EvalResult:
    prompt: str
    expected: str
    actual: str
    success: bool
    latency_ms: float

def load_golden_dataset(path: str = "data/golden_dataset.jsonl") -> List[EvalCase]:
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

def get_agent_response(agent, prompt: str) -> Tuple[str, float]:
    start = time.perf_counter()
    try:
        # Fallback to low-level API if direct method fails
        if not hasattr(agent, "query"):
            client = agent.execution_api_client
            request = {
                "name": agent.resource_name,
                "input": {"message": prompt, "user_id": "eval_user"},
                "class_method": "query"
            }
            response = client.query_reasoning_engine(request=request)
            if hasattr(response, "output"):
                # Clean up response if it's a dictionary or object
                if isinstance(response.output, dict):
                     # Try to extract text part if nested
                     return str(response.output), (time.perf_counter() - start) * 1000
                return str(response.output), (time.perf_counter() - start) * 1000
            else:
                return str(response), (time.perf_counter() - start) * 1000
        
        # Standard SDK call
        response = agent.query(message=prompt)
    except Exception as e:
        response = f"Error: {str(e)}"
    end = time.perf_counter()
    return response, (end - start) * 1000

def evaluate_response_quality(expected: str, actual: str) -> bool:
    """Uses Gemini to judge if the actual response matches the expected intent."""
    model = GenerativeModel("gemini-2.0-flash")
    prompt = f"""
    Compare the following expected answer and actual agent response.
    Determine if the actual response is factually consistent with the expected answer.
    The wording can be different, and the actual response can be more detailed, but it must not contradict the expected answer.
    
    Expected: {expected}
    Actual: {actual}
    
    Is the actual response consistent and correct? Respond with YES or NO.
    """
    try:
        res = model.generate_content(prompt).text.strip().upper()
        return "YES" in res
    except:
        return False

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run Agent Evaluation")
    parser.add_argument("--resource-name", type=str, default=AGENT_RESOURCE, help="Agent Resource Name")
    args = parser.parse_args()
    
    agent_resource = args.resource_name
    print(f"🚀 Connecting to Agent: {agent_resource}")
    try:
        remote_agent = reasoning_engines.ReasoningEngine(agent_resource)
    except Exception as e:
        print(f"❌ Failed to load agent: {e}")
        return

    cases = load_golden_dataset()
    results = []
    
    print("\n📝 Starting Evaluation...")
    print("=" * 60)
    
    for i, case in enumerate(cases):
        print(f"\n[{i+1}/{len(cases)}] Query: {case.prompt}")
        
        actual_response, latency = get_agent_response(remote_agent, case.prompt)
        print(f"    ⏱️ Latency: {latency:.0f}ms")
        print(f"    🤖 Response: {actual_response[:100]}...")
        
        success = evaluate_response_quality(case.expected_answer, actual_response)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"    {status}")
        
        results.append(EvalResult(
            prompt=case.prompt,
            expected=case.expected_answer,
            actual=actual_response,
            success=success,
            latency_ms=latency
        ))
        
    # Create results DataFrame for Vertex AI Experiments
    eval_df = pd.DataFrame([{
        "prompt": r.prompt,
        "response": r.actual, 
        "expected": r.expected,
        "is_correct": 1.0 if r.success else 0.0,
        "latency_ms": r.latency_ms
    } for r in results])

    # Log to Vertex AI Experiments
    try:
        from vertexai.evaluation import EvalTask, MetricPromptTemplateExamples, PointwiseMetric
        
        print("\n📊 Logging to Vertex AI Experiments...")
        experiment_name = "hr-agent-golden-eval"
        
        # Define a custom metric for correctness (using our logic or Model-based)
        # For simplicity, we'll log our pre-calculated correctness as a metric
        # But EvalTask usually runs the eval itself. 
        # Let's use EvalTask to RE-RUN the evaluation using the official SDK for visibility
        
        correctness_metric = PointwiseMetric(
            metric="question_answering_quality",
            metric_prompt_template=MetricPromptTemplateExamples.get_prompt_template("question_answering_quality")
        )
        
        eval_task = EvalTask(
            dataset=eval_df,
            metrics=[correctness_metric],
            experiment=experiment_name
        )
        
        # We already have responses, so we evaluate the 'response' column against 'prompt' and 'reference' (expected)
        experiment_run = eval_task.evaluate(
            experiment_run_name=f"eval-run-{int(time.time())}",
        )
        
        print(f"✅ Results logged to Experiment: {experiment_name}")
        print(f"🔗 View in Console: https://console.cloud.google.com/vertex-ai/experiments/experiments?project={PROJECT_ID}")
        
    except Exception as e:
        print(f"⚠️ Could not log to Experiments: {e}")

    # Console Summary
    print("\n" + "=" * 60)
    print("📊 LOCAL SUMMARY")
    print("=" * 60)
    
    total = len(results)
    passed = sum(1 for r in results if r.success)
    avg_latency = sum(r.latency_ms for r in results) / total if total > 0 else 0
    
    print(f"Total Cases: {total}")
    print(f"Passed:      {passed} ({passed/total:.0%})")
    print(f"Failed:      {total - passed}")
    print(f"Avg Latency: {avg_latency:.0f}ms")

    if passed == total:
        print("\n🏆 EXCELLENT! All test cases passed.")
    else:
        print("\n⚠️ SOME TESTS FAILED. This is expected if the Knowledge Base is incomplete.")
        print("    Check the data stores or document indexing for gaps.")

if __name__ == "__main__":
    main()
