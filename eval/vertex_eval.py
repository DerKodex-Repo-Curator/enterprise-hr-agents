"""
Vertex AI Native Evaluation - Using Official SDK

This script uses the official Vertex AI Gen AI Evaluation Service for:
1. Pairwise (Side-by-Side) Comparison - Compare two models/responses
2. Pointwise Metrics - Evaluate individual responses
3. Built-in Metrics - Coherence, Fluency, Safety, Groundedness

"""
import os
import sys
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

import vertexai
from vertexai.evaluation import (
    EvalTask,
    PairwiseMetric,
    PointwiseMetric,
    MetricPromptTemplateExamples,
)

PROJECT_ID = os.getenv("PROJECT_ID", "hr-policy-agent-486811")
LOCATION = os.getenv("LOCATION", "us-central1")

vertexai.init(project=PROJECT_ID, location=LOCATION)


# ==============================================================================
# PAIRWISE (SXS) EVALUATION
# ==============================================================================

def run_pairwise_evaluation():
    """
    Compare two model responses side-by-side using Vertex AI AutoSxS.
    """
    print("=" * 70)
    print("🔄 PAIRWISE (SXS) EVALUATION - Vertex AI Native")
    print("=" * 70)
    
    # Create evaluation dataset
    # Format: prompt, response (baseline), baseline_model_response (candidate to compare)
    eval_data = pd.DataFrame({
        "prompt": [
            "What is the vacation policy at our company?",
            "How do I report workplace harassment?",
            "What benefits are available to employees?",
        ],
        "response": [  # Baseline - our agent
            "Employees are entitled to 15 days of paid vacation annually, accruing monthly.",
            "Report harassment to HR directly or use the anonymous ethics hotline at 1-800-ETHICS.",
            "We offer health insurance, 401k matching, and 10 paid sick days per year.",
        ],
        "baseline_model_response": [  # Competitor/alternative
            "You get some vacation days. Check with HR for details.",
            "Talk to someone if there's a problem.",
            "There are various benefits available to employees.",
        ],
    })
    
    print(f"\n📊 Eval dataset: {len(eval_data)} comparison pairs")
    
    # Define pairwise metric
    # This uses an LLM autorater to judge which response is better
    pairwise_helpfulness = PairwiseMetric(
        metric="pairwise_question_answering_quality",
        metric_prompt_template=MetricPromptTemplateExamples.get_prompt_template(
            "pairwise_question_answering_quality"
        ),
    )
    
    # Create and run EvalTask
    eval_task = EvalTask(
        dataset=eval_data,
        metrics=[pairwise_helpfulness],
        experiment="hr-agent-sxs-eval",
    )
    
    print("\n⏳ Running pairwise evaluation (this calls Gemini as autorater)...")
    
    try:
        result = eval_task.evaluate()
        
        print("\n📈 PAIRWISE RESULTS:")
        print("-" * 70)
        
        # Display summary metrics
        summary = result.summary_metrics
        for metric_name, value in summary.items():
            print(f"  {metric_name}: {value}")
        
        # Display per-row results
        print("\n📝 Detailed Results:")
        if hasattr(result, 'metrics_table') and result.metrics_table is not None:
            print(result.metrics_table.to_string())
        
        return result
        
    except Exception as e:
        print(f"\n❌ Evaluation failed: {e}")
        print("\nNote: This requires the Vertex AI Evaluation API to be enabled.")
        print("Run: gcloud services enable aiplatform.googleapis.com")
        return None


# ==============================================================================
# POINTWISE EVALUATION
# ==============================================================================

def run_pointwise_evaluation():
    """
    Evaluate individual responses using Vertex AI metrics.
    """
    print("\n" + "=" * 70)
    print("📊 POINTWISE EVALUATION - Vertex AI Native")
    print("=" * 70)
    
    # Create evaluation dataset with context for groundedness
    eval_data = pd.DataFrame({
        "prompt": [
            "What is our vacation policy?",
            "How do I enroll in 401k?",
            "What is the dress code?",
        ],
        "response": [
            "According to the employee handbook, employees receive 15 days of paid vacation annually.",
            "You can enroll in 401k through the HR portal during open enrollment or within 30 days of hire.",
            "Business casual is standard. Casual Fridays are permitted with manager approval.",
        ],
        "context": [
            "Employee Handbook: Vacation Policy - All full-time employees are entitled to 15 days of paid vacation per year, accruing at 1.25 days per month.",
            "Benefits Guide: 401k enrollment is available during annual open enrollment period or within 30 days of your start date via the HR self-service portal.",
            "Company Policy: The dress code is business casual Monday-Thursday. Casual attire is permitted on Fridays.",
        ],
    })
    
    print(f"\n📊 Eval dataset: {len(eval_data)} responses to evaluate")
    
    # Define pointwise metrics
    coherence_metric = PointwiseMetric(
        metric="coherence",
        metric_prompt_template=MetricPromptTemplateExamples.get_prompt_template("coherence"),
    )
    
    fluency_metric = PointwiseMetric(
        metric="fluency", 
        metric_prompt_template=MetricPromptTemplateExamples.get_prompt_template("fluency"),
    )
    
    groundedness_metric = PointwiseMetric(
        metric="groundedness",
        metric_prompt_template=MetricPromptTemplateExamples.get_prompt_template("groundedness"),
    )
    
    # Create and run EvalTask
    eval_task = EvalTask(
        dataset=eval_data,
        metrics=[coherence_metric, fluency_metric, groundedness_metric],
        experiment="hr-agent-pointwise-eval",
    )
    
    print("\n⏳ Running pointwise evaluation...")
    
    try:
        result = eval_task.evaluate()
        
        print("\n📈 POINTWISE RESULTS:")
        print("-" * 70)
        
        summary = result.summary_metrics
        for metric_name, value in summary.items():
            print(f"  {metric_name}: {value}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Evaluation failed: {e}")
        return None


def main():
    """Run all Vertex AI native evaluations."""
    print("\n" + "=" * 70)
    print("Running Vertex AI Native Evaluations...")
    print("=" * 70)
    
    # Run pairwise (SxS) evaluation
    pairwise_result = run_pairwise_evaluation()
    
    # Run pointwise evaluation
    pointwise_result = run_pointwise_evaluation()
    
    print("\n" + "=" * 70)
    print("✅ Vertex AI Evaluation Complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
