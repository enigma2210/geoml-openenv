import asyncio
import os
import json
import re
import textwrap
from typing import List, Optional

from openai import OpenAI

from geoml_models import GeoMLAction, GeoMLObservation
from geoml_env import GeoMLEnv


API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")

TASK_NAME = "geoml-rescue-task"
BENCHMARK = "geoml-env"
MAX_STEPS = 12
TEMPERATURE = 0.1
SUCCESS_SCORE_THRESHOLD = 0.5

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are an autonomous AI machine learning engineer fixing a broken geospatial pipeline.
    You interact with a mock terminal. 
    
    You have exactly 4 commands available:
    1. "list_files" - See what is in the directory.
    2. "read_file" - Read a specific file. Requires 'filepath'.
    3. "edit_file" - Patch code. Requires 'filepath', 'target_text', and 'new_text'.
    4. "run_pipeline" - Run the tests to see if you fixed the bug.
    
    You MUST respond with ONLY valid JSON matching this exact schema:
    {
      "command": "command_name",
      "filepath": "string or null",
      "target_text": "string or null",
      "new_text": "string or null"
    }
    Do not include markdown formatting or explanations. Just the raw JSON object.
    """
).strip()

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    safe_action = action.replace('\n', ' ').replace('\r', '')[:100]
    print(f"[STEP] step={step} action={safe_action} reward={reward:.2f} done={done_val} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

def extract_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise ValueError("Could not parse JSON from LLM output")

def get_model_action(client: OpenAI, step: int, obs: GeoMLObservation, history: List[str]) -> GeoMLAction:
    history_block = "\n".join(history[-3:]) if history else "No history yet."
    
    user_prompt = f"""
    Step: {step}
    Current Objective: {obs.current_objective}
    Terminal Output: {obs.terminal_output}
    Available Files: {obs.available_files}
    
    Previous actions:
    {history_block}
    
    Provide your next action in JSON format.
    """
    
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
        )
        raw_text = (completion.choices[0].message.content or "").strip()
        parsed_json = extract_json(raw_text)
        return GeoMLAction(**parsed_json)
    except Exception:
        return GeoMLAction(command="list_files")

async def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
    env = GeoMLEnv()
    
    history: List[str] = []
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)

    try:
        obs = await env.reset()
        
        for step in range(1, MAX_STEPS + 1):
            if env.done:
                break
                
            action_obj = get_model_action(client, step, obs, history)
            obs, reward_obj, done, info = await env.step(action_obj)
            
            reward_val = reward_obj.score
            rewards.append(reward_val)
            steps_taken = step
            action_str = f"{action_obj.command}({action_obj.filepath})"
            
            log_step(step=step, action=action_str, reward=reward_val, done=done, error=None)
            history.append(f"Step {step}: {action_str} -> {reward_obj.feedback}")
            
            if done:
                break
        
        
        MAX_TOTAL_REWARD = 1.60
        score = sum(rewards) / MAX_TOTAL_REWARD
        score = min(max(score, 0.0), 1.0)
        success = score >= SUCCESS_SCORE_THRESHOLD

    finally:
        
        await env.close()
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

if __name__ == "__main__":
    asyncio.run(main())