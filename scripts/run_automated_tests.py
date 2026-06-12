import os
import sys
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain_ollama import ChatOllama
from deepeval import evaluate
from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCase
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    ContextualRelevancyMetric
)
from agents.multi_agent_graph import run_multi_agent_graph

DATA_FILE = "data/comprehensive_eval_questions.json"
REPORT_FILE = "logs/evaluation_report.md"
OLLAMA_MODEL = "gemma4:e4b"

class OllamaDeepEvalModel(DeepEvalBaseLLM):
    def __init__(self):
        super().__init__()

    def load_model(self):
        if getattr(self, "model", None) is None:
            self.model = ChatOllama(model=OLLAMA_MODEL)
        return self.model

    def generate(self, prompt: str) -> str:
        return self.model.invoke(prompt).content

    async def a_generate(self, prompt: str) -> str:
        return self.generate(prompt)

    def get_model_name(self):
        return OLLAMA_MODEL

def load_eval_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def run_evaluation(limit=None):
    eval_data = load_eval_data()
    if limit and limit > 0:
        eval_data = eval_data[:limit]
    
    print(f"Loaded {len(eval_data)} test cases. Generating answers...")
    
    test_cases = []
    
    # 1. Run Graph to get actual answers and context
    for i, item in enumerate(eval_data, 1):
        question = item["question"]
        expected_answer = item["expected_answer"]
        print(f"[{i}/{len(eval_data)}] Running graph for: {question}")
        
        result = run_multi_agent_graph(question)
        
        test_case = LLMTestCase(
            input=question,
            actual_output=result["answer"],
            expected_output=expected_answer,
            retrieval_context=[result["context"]],
            context=[result["context"]]
        )
        test_cases.append(test_case)

    # 2. Setup Metrics
    local_judge = OllamaDeepEvalModel()
    metrics = [
        AnswerRelevancyMetric(threshold=0.7, model=local_judge),
        FaithfulnessMetric(threshold=0.7, model=local_judge),
        ContextualRelevancyMetric(threshold=0.7, model=local_judge),
    ]

    # 3. Evaluate and Build Report
    os.makedirs("logs", exist_ok=True)
    
    print("Starting evaluation metrics calculation...")
    
    with open(REPORT_FILE, "w", encoding="utf-8") as report:
        report.write(f"# Comprehensive Evaluation Report\n")
        report.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.write(f"**Total Cases:** {len(test_cases)}\n\n")
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"Evaluating Case {i}/{len(test_cases)}: {test_case.input}")
            
            report.write(f"## Test Case {i}\n")
            report.write(f"**Question:** {test_case.input}\n\n")
            report.write(f"**Expected:** {test_case.expected_output}\n\n")
            report.write(f"**Actual:** {test_case.actual_output}\n\n")
            
            for metric in metrics:
                metric.measure(test_case)
                
                status_icon = "✅" if metric.success else "❌"
                report.write(f"### {status_icon} {metric.__class__.__name__}\n")
                report.write(f"- **Score:** {metric.score}\n")
                report.write(f"- **Reason:** {metric.reason}\n\n")
            
            report.write("---\n\n")

    print(f"\nEvaluation complete! Report saved to {REPORT_FILE}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run comprehensive automated tests.")
    parser.add_argument("--limit", type=int, default=None, help="Limit the number of test cases to run")
    args = parser.parse_args()
    
    run_evaluation(limit=args.limit)
