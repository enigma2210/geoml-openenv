from pydantic import BaseModel, Field
from typing import Optional, List, Literal

# 1. THE ACTION SPACE: What the AI is allowed to do.
class GeoMLAction(BaseModel):
    command: Literal["list_files", "read_file", "edit_file", "run_pipeline"] = Field(
        ..., description="The command you want to execute."
    )
    filepath: Optional[str] = Field(
        None, description="The name of the file you want to read or edit (e.g., 'extract.py')."
    )
    target_text: Optional[str] = Field(
        None, description="If editing a file, the exact text you want to replace."
    )
    new_text: Optional[str] = Field(
        None, description="If editing a file, the new text you want to insert."
    )

# 2. THE OBSERVATION SPACE: What the AI sees after taking an action.
class GeoMLObservation(BaseModel):
    current_objective: str = Field(
        ..., description="The specific bug or pipeline issue you need to fix."
    )
    terminal_output: str = Field(
        ..., description="The console output, tracebacks, or file contents from your last command."
    )
    available_files: List[str] = Field(
        ..., description="List of files currently in the directory."
    )

# 3. THE REWARD SPACE: How we grade the AI.
class GeoMLReward(BaseModel):
    score: float = Field(
        ..., description="A score between 0.0 and 1.0 evaluating the current state."
    )
    feedback: str = Field(
        ..., description="Human-readable feedback explaining why this score was given."
    )