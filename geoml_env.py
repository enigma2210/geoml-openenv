import copy
from typing import Dict, Any, Tuple
from geoml_models import GeoMLAction, GeoMLObservation, GeoMLReward

# This represents the "broken" state of our project when the AI first boots up.
INITIAL_FILES = {
    "config.yaml": "projection: 'EPSG:9999'\nresolution: 10m\n",
    "temporal_merge.py": "df_merged = df.merge(df_lag, on='wrong_id') # BUG: Misaligned temporal features",
    "extract.py": "image.mosaic() # BUG: Causes Out-Of-Memory (OOM) error for large areas"
}

class GeoMLEnv:
    def __init__(self):
        # We start with task 1
        self.current_task_index = 1
        self.files: Dict[str, str] = {}
        self.done = False

    async def reset(self) -> GeoMLObservation:
        """Wipes the slate clean for a new episode[cite: 5]."""
        self.files = copy.deepcopy(INITIAL_FILES)
        self.current_task_index = 1
        self.done = False
        
        return self._get_observation(
            terminal_output="System booted. Pipeline is currently broken. Begin debugging."
        )

    async def state(self) -> Dict[str, Any]:
        """Returns the current internal state of the environment[cite: 5]."""
        return {
            "current_task": self.current_task_index,
            "files": self.files,
            "done": self.done
        }

    async def step(self, action: GeoMLAction) -> Tuple[GeoMLObservation, GeoMLReward, bool, dict]:
        """Processes the AI's action and returns the results[cite: 5]."""
        terminal_output = ""
        reward_score = 0.0
        feedback = ""

        # ACTION: list_files
        if action.command == "list_files":
            terminal_output = f"Files in directory: {', '.join(self.files.keys())}"
            reward_score = 0.01  # Tiny reward for exploring
            feedback = "Listed files successfully."

        # ACTION: read_file
        elif action.command == "read_file":
            if action.filepath in self.files:
                terminal_output = f"--- {action.filepath} ---\n{self.files[action.filepath]}"
                reward_score = 0.05  # Reward for reading documentation/code
                feedback = f"Read {action.filepath}."
            else:
                terminal_output = f"Error: File '{action.filepath}' not found."
                reward_score = -0.05 # Penalty for hallucinating files
                feedback = "Attempted to read non-existent file."

        # ACTION: edit_file
        elif action.command == "edit_file":
            if action.filepath in self.files and action.target_text and action.new_text:
                current_content = self.files[action.filepath]
                if action.target_text in current_content:
                    self.files[action.filepath] = current_content.replace(action.target_text, action.new_text)
                    terminal_output = f"Successfully updated {action.filepath}."
                    reward_score = 0.1 # Reward for attempting a fix
                    feedback = "Applied code patch."
                else:
                    terminal_output = f"Error: Target text not found in {action.filepath}."
                    reward_score = -0.1 # Penalty for bad patches
                    feedback = "Failed to apply patch."
            else:
                terminal_output = "Error: Invalid edit parameters."
                reward_score = -0.1
                feedback = "Malformed edit request."

        # ACTION: run_pipeline (This triggers the Grading Engine)
        elif action.command == "run_pipeline":
            reward_score, feedback, terminal_output = self._grade_pipeline()

        # Generate the Observation
        obs = self._get_observation(terminal_output)
        
        # Generate the Reward
        reward = GeoMLReward(score=reward_score, feedback=feedback)

        return obs, reward, self.done, {}

    def _get_observation(self, terminal_output: str) -> GeoMLObservation:
        """Helper to build the observation object."""
        objectives = {
            1: "Task 1 (Easy): Fix the spatial projection error in config.yaml.",
            2: "Task 2 (Medium): Fix the temporal misalignment bug in temporal_merge.py.",
            3: "Task 3 (Hard): Fix the Out-Of-Memory (OOM) memory leak in extract.py.",
            4: "All tasks completed! Pipeline is healthy."
        }
        return GeoMLObservation(
            current_objective=objectives.get(self.current_task_index, "Unknown"),
            terminal_output=terminal_output,
            available_files=list(self.files.keys())
        )

    def _grade_pipeline(self) -> Tuple[float, str, str]:
        """
        The core logic evaluating if the AI actually fixed the bugs.
        Returns: (reward_score, feedback, terminal_output)
        """
        # Grade Task 1
        if self.current_task_index == 1:
            if "EPSG:4326" in self.files["config.yaml"]:
                self.current_task_index = 2
                return 1.0, "Task 1 complete!", "SUCCESS: Projection fixed. Pipeline advanced to temporal merge... ERROR: Misaligned temporal features."
            else:
                return 0.0, "Task 1 failed.", "CRITICAL ERROR: Invalid projection string 'EPSG:9999'. Pipeline halted."

        # Grade Task 2
        elif self.current_task_index == 2:
            if "on='spatial_id'" in self.files["temporal_merge.py"] or "on=['spatial_id', 'year']" in self.files["temporal_merge.py"]:
                self.current_task_index = 3
                return 1.0, "Task 2 complete!", "SUCCESS: Temporal features aligned. Pipeline advanced to extraction... ERROR: OOM during .mosaic()."
            else:
                return 0.0, "Task 2 failed.", "ERROR: Misaligned temporal features detected. Merged dataframe has wrong dimensions."

        # Grade Task 3
        elif self.current_task_index == 3:
            if "chunk" in self.files["extract.py"].lower() or "batch" in self.files["extract.py"].lower():
                self.done = True
                self.current_task_index = 4
                return 1.0, "Task 3 complete!", "SUCCESS: Pipeline completed extraction perfectly. R-squared baseline achieved: 0.82. You win."
            else:
                return 0.0, "Task 3 failed.", "FATAL: Out of Memory (OOM) error. The container ran out of RAM."
        
        return 0.0, "Pipeline healthy.", "No tasks remaining."

    async def close(self):
        """Cleanup method called at the end of an episode[cite: 47]."""
        pass