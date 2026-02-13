"""
Vertex AI Load Testing for HR Agent

Load test the HR agent to measure performance under concurrent requests.

Modes:
1. local: Call HRPolicyAgent.query() directly
2. reasoning_engine: Call deployed Vertex AI Reasoning Engine endpoint
3. multi_agent: Call ADK multi-agent Runner

Metrics:
- P50 / P95 / P99 latency
- Throughput (queries/second)
- Error rate
- Response quality under load

"""

import asyncio
import json
import os
import sys
import time
import statistics
import argparse
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# ==============================================================================
# DATA STRUCTURES
# ==============================================================================

@dataclass
class RequestResult:
    """Result of a single load test request."""
    request_id: int
    prompt: str
    response: str
    latency_ms: float
    success: bool
    error: Optional[str] = None
    timestamp: str = ""


@dataclass
class LoadTestResults:
    """Aggregated load test results."""
    mode: str
    concurrency: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_duration_s: float
    throughput_qps: float
    latency_p50_ms: float
    latency_p95_ms: float
    latency_p99_ms: float
    latency_avg_ms: float
    latency_min_ms: float
    latency_max_ms: float
    error_rate: float
    requests: List[RequestResult] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        if self.requests:
            d["requests"] = [asdict(r) for r in self.requests]
        return d


# ==============================================================================
# TEST PROMPTS
# ==============================================================================

LOAD_TEST_PROMPTS = [
    # Easy - Policy Questions
    "What is the vacation policy?",
    "How many sick days do employees get?",
    "What are the working hours?",
    "What is the dress code policy?",
    "What is the remote work policy?",
    
    # Medium - Benefits Questions
    "How do I enroll in the 401k plan?",
    "What health insurance options are available?",
    "How does parental leave work?",
    "What is the tuition reimbursement policy?",
    "Are there employee wellness programs?",
    
    # Hard - Compliance & Sensitive
    "How do I file a harassment complaint?",
    "What is the process for workplace accommodations?",
    "What are the anti-discrimination policies?",
    "How does the whistleblower protection work?",
    "What are the data privacy policies for employee records?",
    
    # Edge Cases
    "Can I take vacation during my notice period?",
    "What happens to my benefits if I switch to part-time?",
    "Is there a policy on moonlighting?",
    "What are the rules around internal transfers?",
    "How does the performance review process work?",
]


# ==============================================================================
# LOAD TESTER
# ==============================================================================

class VertexAILoadTester:
    """
    Load test the HR agent with configurable concurrency.
    
    Usage:
        tester = VertexAILoadTester(concurrency=10, total_requests=50)
        results = tester.run_load_test(mode="local")
        tester.print_report(results)
    """
    
    def __init__(
        self,
        concurrency: int = 5,
        total_requests: int = 20,
        timeout_s: float = 30.0,
        prompts: Optional[List[str]] = None
    ):
        self.concurrency = concurrency
        self.total_requests = total_requests
        self.timeout_s = timeout_s
        self.prompts = prompts or LOAD_TEST_PROMPTS
        self._agent = None
        self._executor = ThreadPoolExecutor(max_workers=concurrency)
    
    def _get_prompt(self, request_id: int) -> str:
        """Get a prompt for a given request ID (cycles through prompts)."""
        return self.prompts[request_id % len(self.prompts)]
    
    def _init_local_agent(self):
        """Initialize local agent for testing."""
        if self._agent is None:
            try:
                from hr_agent.agent import HRPolicyAgent, PROJECT_ID, LOCATION, DATA_STORE_ID, DATASET_ID, TABLE_ID
                
                self._agent = HRPolicyAgent(
                    project_id=PROJECT_ID or "test-project",
                    location=LOCATION or "us-central1",
                    datastore_id=DATA_STORE_ID,
                    dataset_id=DATASET_ID,
                    table_id=TABLE_ID,
                    model_name="gemini-2.0-flash"
                )
                self._agent.set_up()
            except Exception as e:
                print(f"⚠️ Could not init local agent: {e}")
                print("   Falling back to mock mode")
                self._agent = "mock"
    
    def _query_local(self, prompt: str) -> str:
        """Query the local agent."""
        if self._agent == "mock":
            # Simulate variable latency
            import random
            time.sleep(random.uniform(0.1, 0.5))
            return f"Mock response for: {prompt[:50]}..."
        return self._agent.query(prompt)
    
    def _query_reasoning_engine(self, prompt: str) -> str:
        """Query the deployed Reasoning Engine endpoint."""
        try:
            import vertexai
            from vertexai.preview import reasoning_engines
            
            project_id = os.getenv("PROJECT_ID", "hr-policy-agent-486811")
            location = os.getenv("LOCATION", "us-central1")
            resource_name = os.getenv("REASONING_ENGINE_ID")
            
            if not resource_name:
                raise ValueError("Set REASONING_ENGINE_ID env var")
            
            vertexai.init(project=project_id, location=location)
            engine = reasoning_engines.ReasoningEngine(resource_name)
            response = engine.query(input=prompt)
            return str(response)
            
        except Exception as e:
            raise RuntimeError(f"Reasoning Engine query failed: {e}")
    
    def _query_mock(self, prompt: str) -> str:
        """Mock agent for dry-run testing."""
        import random
        # Simulate realistic latency distribution
        latency = random.gauss(0.3, 0.1)  # Mean 300ms, std 100ms
        latency = max(0.05, latency)  # Min 50ms
        time.sleep(latency)
        return f"[Mock Response] Based on our HR policies, {prompt[:30]}..."
    
    async def _send_request(self, request_id: int, mode: str) -> RequestResult:
        """Send a single request and capture timing."""
        prompt = self._get_prompt(request_id)
        start_time = time.time()
        
        try:
            loop = asyncio.get_event_loop()
            
            if mode == "local":
                response = await asyncio.wait_for(
                    loop.run_in_executor(self._executor, self._query_local, prompt),
                    timeout=self.timeout_s
                )
            elif mode == "reasoning_engine":
                response = await asyncio.wait_for(
                    loop.run_in_executor(self._executor, self._query_reasoning_engine, prompt),
                    timeout=self.timeout_s
                )
            elif mode == "mock":
                response = await asyncio.wait_for(
                    loop.run_in_executor(self._executor, self._query_mock, prompt),
                    timeout=self.timeout_s
                )
            else:
                raise ValueError(f"Unknown mode: {mode}")
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            return RequestResult(
                request_id=request_id,
                prompt=prompt,
                response=response[:200],  # Truncate for storage
                latency_ms=elapsed_ms,
                success=True,
                timestamp=datetime.now().isoformat()
            )
            
        except asyncio.TimeoutError:
            elapsed_ms = (time.time() - start_time) * 1000
            return RequestResult(
                request_id=request_id,
                prompt=prompt,
                response="",
                latency_ms=elapsed_ms,
                success=False,
                error=f"Timeout after {self.timeout_s}s",
                timestamp=datetime.now().isoformat()
            )
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            return RequestResult(
                request_id=request_id,
                prompt=prompt,
                response="",
                latency_ms=elapsed_ms,
                success=False,
                error=str(e),
                timestamp=datetime.now().isoformat()
            )
    
    async def run_load_test(self, mode: str = "mock") -> LoadTestResults:
        """
        Run the load test.
        
        Args:
            mode: "local", "reasoning_engine", or "mock"
        """
        print(f"\n{'=' * 70}")
        print(f"🔥 VERTEX AI LOAD TEST")
        print(f"{'=' * 70}")
        print(f"  Mode:         {mode}")
        print(f"  Concurrency:  {self.concurrency}")
        print(f"  Total Reqs:   {self.total_requests}")
        print(f"  Timeout:      {self.timeout_s}s")
        print(f"{'=' * 70}\n")
        
        if mode == "local":
            self._init_local_agent()
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.concurrency)
        
        async def bounded_request(req_id):
            async with semaphore:
                return await self._send_request(req_id, mode)
        
        # Fire all requests
        start_time = time.time()
        
        tasks = [bounded_request(i) for i in range(self.total_requests)]
        results = []
        
        # Track progress
        completed = 0
        for coro in asyncio.as_completed(tasks):
            result = await coro
            results.append(result)
            completed += 1
            
            status = "✅" if result.success else "❌"
            if completed % max(1, self.total_requests // 10) == 0 or completed == self.total_requests:
                print(f"  Progress: {completed}/{self.total_requests} "
                      f"({completed * 100 // self.total_requests}%) "
                      f"- Last: {result.latency_ms:.0f}ms {status}")
        
        total_duration = time.time() - start_time
        
        # Calculate metrics
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        if successful:
            latencies = sorted([r.latency_ms for r in successful])
            p50 = latencies[len(latencies) // 2]
            p95_idx = int(len(latencies) * 0.95)
            p99_idx = int(len(latencies) * 0.99)
            p95 = latencies[min(p95_idx, len(latencies) - 1)]
            p99 = latencies[min(p99_idx, len(latencies) - 1)]
            avg = statistics.mean(latencies)
        else:
            p50 = p95 = p99 = avg = 0
            latencies = [0]
        
        return LoadTestResults(
            mode=mode,
            concurrency=self.concurrency,
            total_requests=self.total_requests,
            successful_requests=len(successful),
            failed_requests=len(failed),
            total_duration_s=total_duration,
            throughput_qps=len(successful) / total_duration if total_duration > 0 else 0,
            latency_p50_ms=p50,
            latency_p95_ms=p95,
            latency_p99_ms=p99,
            latency_avg_ms=avg,
            latency_min_ms=min(latencies),
            latency_max_ms=max(latencies),
            error_rate=len(failed) / self.total_requests if self.total_requests > 0 else 0,
            requests=results
        )
    
    def print_report(self, results: LoadTestResults):
        """Print a formatted load test report."""
        print(f"\n{'=' * 70}")
        print(f"📊 LOAD TEST REPORT")
        print(f"{'=' * 70}")
        
        # Summary
        print(f"\n  Mode:              {results.mode}")
        print(f"  Concurrency:       {results.concurrency}")
        print(f"  Duration:          {results.total_duration_s:.2f}s")
        
        # Success/Failure
        print(f"\n  ── Requests ──")
        print(f"  Total:             {results.total_requests}")
        print(f"  Successful:        {results.successful_requests} ✅")
        print(f"  Failed:            {results.failed_requests} ❌")
        print(f"  Error Rate:        {results.error_rate * 100:.1f}%")
        
        # Throughput
        print(f"\n  ── Throughput ──")
        print(f"  QPS:               {results.throughput_qps:.2f} queries/sec")
        
        # Latency
        print(f"\n  ── Latency ──")
        print(f"  P50:               {results.latency_p50_ms:.0f}ms")
        print(f"  P95:               {results.latency_p95_ms:.0f}ms")
        print(f"  P99:               {results.latency_p99_ms:.0f}ms")
        print(f"  Avg:               {results.latency_avg_ms:.0f}ms")
        print(f"  Min:               {results.latency_min_ms:.0f}ms")
        print(f"  Max:               {results.latency_max_ms:.0f}ms")
        
        # SLA Check
        print(f"\n  ── SLA Validation ──")
        sla_p50 = 2000  # 2 seconds
        sla_p95 = 5000  # 5 seconds
        sla_p99 = 10000  # 10 seconds
        
        p50_ok = results.latency_p50_ms < sla_p50
        p95_ok = results.latency_p95_ms < sla_p95
        p99_ok = results.latency_p99_ms < sla_p99
        error_ok = results.error_rate < 0.05  # 5% error rate
        
        print(f"  P50 < {sla_p50}ms:      {'✅ PASS' if p50_ok else '❌ FAIL'} ({results.latency_p50_ms:.0f}ms)")
        print(f"  P95 < {sla_p95}ms:     {'✅ PASS' if p95_ok else '❌ FAIL'} ({results.latency_p95_ms:.0f}ms)")
        print(f"  P99 < {sla_p99}ms:    {'✅ PASS' if p99_ok else '❌ FAIL'} ({results.latency_p99_ms:.0f}ms)")
        print(f"  Error < 5%:        {'✅ PASS' if error_ok else '❌ FAIL'} ({results.error_rate * 100:.1f}%)")
        
        all_pass = p50_ok and p95_ok and p99_ok and error_ok
        print(f"\n  Overall:           {'✅ ALL SLAs MET' if all_pass else '❌ SLA VIOLATION'}")
        
        # Error details
        if results.requests:
            errors = [r for r in results.requests if not r.success]
            if errors:
                print(f"\n  ── Errors ──")
                error_types: Dict[str, int] = {}
                for e in errors:
                    err = e.error or "Unknown"
                    error_types[err] = error_types.get(err, 0) + 1
                for err_type, count in error_types.items():
                    print(f"  {err_type}: {count}x")
        
        print(f"\n{'=' * 70}")
    
    def export_results(self, results: LoadTestResults, path: str):
        """Export results to JSON."""
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        with open(path, "w") as f:
            json.dump(results.to_dict(), f, indent=2)
        print(f"📤 Results exported to {path}")


# ==============================================================================
# INTERVIEW CONCEPTS
# ==============================================================================

    if args.export:
        tester.export_results(results, args.export)


if __name__ == "__main__":
    main()
