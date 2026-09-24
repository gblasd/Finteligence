import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock vertexai to avoid Ragas import error
import sys
from unittest.mock import MagicMock
sys.modules['langchain_community.chat_models.vertexai'] = MagicMock()
sys.modules['langchain_community.embeddings.vertexai'] = MagicMock()

from openai import OpenAI
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import Faithfulness
from ragas.metrics.collections import answer_relevancy
from agent.state import AgentState
from agent.loop import run as run_loop

load_dotenv()

_DATASET_PATH = Path(__file__).parent / "golden_dataset.json"

def run_ragas_eval():
    client = OpenAI()
    
    with open(_DATASET_PATH) as f:
        dataset = json.load(f)
        
    questions = []
    answers = []
    contexts_list = []
    
    print("Running queries through the agent...")
    for item in dataset:
        if item.get("should_be_blocked", False):
            continue
            
        question = item["question"]
        print(f"Processing: {question}")
        
        state = AgentState().add_user_message(question)
        final = run_loop(state=state, client=client, model="gpt-4o-mini") # use gpt-4o-mini to save cost/time
        
        # Extract contexts from tool calls
        contexts = [msg.content for msg in final.messages if msg.role == "tool"]
        answer = final.last_response
        
        questions.append(question)
        answers.append(answer)
        contexts_list.append(contexts)
        
    print("\nPreparing dataset for Ragas...")
    eval_dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts_list,
    })
    
    print("Running Ragas evaluation...")
    result = evaluate(
        eval_dataset,
        metrics=[Faithfulness()],
    )
    
    print("\n--- Ragas Evaluation Results ---")
    print(result)
    
if __name__ == "__main__":
    run_ragas_eval()
