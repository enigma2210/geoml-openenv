import copy
import os
import subprocess
import tempfile
import shutil
import random
from typing import Dict, Any, Tuple
from geoml_models import GeoMLAction, GeoMLObservation, GeoMLReward

class GeoMLEnv:
    def __init__(self):
        # Create a secure temporary directory for execution
        self.workspace = tempfile.mkdtemp()
        self.max_progress = 0
        self.done = False
        self.files: Dict[str, str] = {}

    def _generate_procedural_files(self) -> Dict[str, str]:
        """The Chaos Engine: Generates syntactically valid but logically broken code."""
        # Randomize the exact nature of the bugs for infinite replayability
        bad_epsg = random.choice(['EPSG:3857', 'EPSG:27700', 'EPSG:900913', 'EPSG:4269'])
        bad_merge_key = random.choice(['wrong_id', 'spatial_index', 'temp_id', 'uuid'])
        bad_strategy = random.choice(['mosaic_all', 'process_full_batch', 'load_entire_dataset'])

        return {
            "config.yaml": f"projection: '{bad_epsg}'\nresolution: '10m'\n",
            
            "temporal_merge.py": f"""import pandas as pd

def merge_data():
    df = pd.DataFrame({{'spatial_id': [1,2,3], 'val': [10,20,30]}})
    df_lag = pd.DataFrame({{'spatial_id': [1,2,3], 'lag_val': [5,15,25]}})
    
    # BUG: Misaligned temporal features due to wrong merge key
    df_merged = df.merge(df_lag, on='{bad_merge_key}')
    return df_merged
""",

            "extract.py": f"""def process_images():
    # BUG: Processing all images at once causes an OOM crash
    strategy = '{bad_strategy}'
    
    if strategy == '{bad_strategy}':
        raise MemoryError(f"FATAL: Out of Memory (OOM) using {{strategy}}. Change strategy to 'chunk'.")
    elif strategy == 'chunk':
        print("SUCCESS: Pipeline completed extraction perfectly. R-squared baseline achieved: 0.82")
""",

            "pipeline.py": """import yaml
import sys
from temporal_merge import merge_data
from extract import process_images

def run():
    print("--- Running Pipeline Diagnostics ---")
    
    with open('config.yaml') as f:
        config = yaml.safe_load(f)
    if config.get('projection') != 'EPSG:4326':
        print(f"CRITICAL ERROR: Invalid projection '{config.get('projection')}'. Expected EPSG:4326.")
        sys.exit(1)
    print("SUCCESS: Projection validated.")

    try:
        df = merge_data()
        if 'lag_val' not in df.columns or len(df) != 3:
            print("ERROR: Merged dataframe has wrong dimensions.")
            sys.exit(1)
        print("SUCCESS: Temporal features aligned.")
    except Exception as e:
        print(f"ERROR during temporal merge: {e}")
        sys.exit(1)
    
    try:
        process_images()
    except MemoryError as e:
        print(e)
        sys.exit(1)

if __name__ == "__main__":
    run()
"""
        }

    async def reset(self) -> GeoMLObservation:
        """Wipes the state clean, generates new bugs, and provisions the workspace for a new episode."""
        self.max_progress = 0
        self.done = False
        self.files = self._generate_procedural_files()
        self._write_files_to_disk()
        
        return self._get_observation(
            terminal_output="System booted. Workspace provisioned. Run 'pipeline.py' to diagnose errors."
        )

    def _write_files_to_disk(self):
        """Synchronizes the in-memory files to the physical sandbox directory."""
        for filename, content in self.files.items():
            path = os.path.join(self.workspace, filename)
            with open(path, 'w') as f:
                f.write(content)

    async def state(self) -> Dict[str, Any]:
        return {
            "max_progress": self.max_progress,
            "done": self.done,
            "workspace": self.workspace
        }

    async def step(self, action: GeoMLAction) -> Tuple[GeoMLObservation, GeoMLReward, bool, dict]:
        terminal_output = ""
        step_reward = 0.0
        feedback = ""

        if action.command == "list_files":
            terminal_output = f"Files in directory: {', '.join(self.files.keys())}"
            step_reward = 0.01  
            feedback = "Listed files successfully."

        elif action.command == "read_file":
            if action.filepath in self.files:
                terminal_output = f"--- {action.filepath} ---\n{self.files[action.filepath]}"
                step_reward = 0.02  
                feedback = f"Read {action.filepath}."
            else:
                terminal_output = f"Error: File '{action.filepath}' not found."
                step_reward = -0.05 
                feedback = "Attempted to read non-existent file."

        elif action.command == "edit_file":
            if action.filepath in self.files and action.target_text and action.new_text:
                current_content = self.files[action.filepath]
                if action.target_text in current_content:
                    self.files[action.filepath] = current_content.replace(action.target_text, action.new_text)
                    self._write_files_to_disk() # Sync the patch to the actual execution sandbox
                    terminal_output = f"Successfully updated {action.filepath}."
                    step_reward = 0.05 
                    feedback = "Applied code patch."
                else:
                    terminal_output = f"Error: Target text not found in {action.filepath}."
                    step_reward = -0.05 
                    feedback = "Failed to apply patch."
            else:
                terminal_output = "Error: Invalid edit parameters."
                step_reward = -0.05
                feedback = "Malformed edit request."

        elif action.command == "run_pipeline":
            # TRUE EXECUTION: Run the actual python script in the sandbox
            result = subprocess.run(
                ["python", "pipeline.py"], 
                cwd=self.workspace, 
                capture_output=True, 
                text=True
            )
            
            # Feed the real console output (including Python tracebacks) back to the agent
            terminal_output = result.stdout + "\n" + result.stderr
            
            # Grade based on actual execution output
            current_progress = 0
            if "SUCCESS: Projection validated." in terminal_output:
                current_progress = 1
            if "SUCCESS: Temporal features aligned." in terminal_output:
                current_progress = 2
            if "SUCCESS: Pipeline completed" in terminal_output:
                current_progress = 3
                self.done = True
            
            # Anti-Exploit Reward Shaping: The agent only gets a large reward the FIRST time it beats a stage.
            if current_progress > self.max_progress:
                step_reward = (current_progress - self.max_progress) * 0.3
                self.max_progress = current_progress
                feedback = f"Pipeline advanced to stage {current_progress}!"
            elif result.returncode != 0:
                step_reward = -0.02
                feedback = "Pipeline execution failed. Review traceback."
            else:
                step_reward = 0.0
                feedback = "Pipeline executed but no new progress made."

        obs = self._get_observation(terminal_output)
        reward = GeoMLReward(score=step_reward, feedback=feedback)

        return obs, reward, self.done, {}

    def _get_observation(self, terminal_output: str) -> GeoMLObservation:
        objectives = {
            0: "Task 1 (Easy): Fix the spatial projection error in config.yaml to expect EPSG:4326.",
            1: "Task 2 (Medium): Fix the pandas KeyError in temporal_merge.py by merging on 'spatial_id'.",
            2: "Task 3 (Hard): Fix the MemoryError in extract.py by changing the strategy to 'chunk'.",
            3: "All tasks completed! Pipeline is healthy."
        }
        return GeoMLObservation(
            current_objective=objectives.get(self.max_progress, "Unknown"),
            terminal_output=terminal_output.strip()[-2000:], # Prevent prompt context overflow
            available_files=list(self.files.keys())
        )

    async def close(self):
        """Clean up the physical temporary directory to prevent memory leaks."""
        shutil.rmtree(self.workspace, ignore_errors=True)