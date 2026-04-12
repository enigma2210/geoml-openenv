# 🌍 GeoML-RescueEnv: The AI Flight Simulator

Welcome to **GeoML-RescueEnv**! 

In the real world, when engineers use satellites to map forests or predict weather, they write massive data pipelines. If there is a single typo in that code, the pipeline silently fails, and the data is ruined. 

We don't want to let an unproven AI touch a real $100 Million satellite system. So, we built this **"Digital Danger Room"**. This is a safe, simulated environment where AI agents (like Qwen, Llama, or GPT) can practice diagnosing, debugging, and patching broken Machine Learning pipelines without breaking anything real.

---

## 🚀 What makes this special?

This isn't a text-adventure game. It is a highly advanced, mathematically graded sandbox:

1. 🌪️ **The Procedural Chaos Engine:** Every time you reset the environment, the underlying bugs change. The AI cannot "memorize" the answer; it is forced to actually read the code and diagnose the problem every single session.
2. 🧠 **AST (Abstract Syntax Tree) Grading:** If the AI writes code that is *almost* right (correct logic, wrong variable name), our environment reads the mathematical structure of the code and awards partial points. This dense reward signal is what trains frontier models.
3. 📊 **Live DAG Dashboard:** The environment features a live web dashboard that tracks the health of the pipeline in real-time as the AI agent patches files.

---

## 🧗 The 3-Stage Rescue Mission

When the AI enters the sandbox, it must fix three distinct bugs to get a perfect score (1.0).

* **Task 1 (Easy):** Fix a spatial projection error in `config.yaml` (e.g., changing a broken EPSG code to the correct `EPSG:4326`).
* **Task 2 (Medium):** Fix a Pandas dataframe `KeyError` in `temporal_merge.py` by identifying the correct merge column (`spatial_id`).
* **Task 3 (Hard):** Fix a fatal Out-Of-Memory (OOM) crash in `extract.py` by rewriting the data processing strategy to use memory `chunk`ing.

---

## 🛠️ The Agent's Toolkit (OpenEnv Specification)

The AI interacts with the environment exactly like a human engineer would in a terminal.

### 👁️ Observation Space (What the AI sees)
Every turn, the environment gives the AI a JSON object containing:
* `current_objective`: A plain-English description of the current goal.
* `terminal_output`: The crash logs, traceback errors, or file contents.
* `available_files`: A list of files currently in the workspace.

### 🕹️ Action Space (What the AI can do)
The AI can execute 4 strict commands:
1. `list_files`: Look at the directory.
2. `read_file`: Look inside a specific script.
3. `edit_file`: Patch the code by finding `target_text` and replacing it with `new_text`.
4. `run_pipeline`: Execute the pipeline to see if the patch fixed the crash!

---

## 💻 How to Run It (Setup Instructions)

Follow these exact steps to run the AI simulation on your computer.

### Step 1: Install the Requirements
Make sure you have Python installed on your computer. Open your terminal, navigate to this project folder, and run:

    pip install -r requirements.txt


### Step 2: Give the AI a Brain (Set your API Key)
The AI needs an engine to think. We are using Hugging Face. You must set your API key in your terminal so the script can find it. 

If you are using Windows (PowerShell):

    $env:HF_TOKEN="paste_your_huggingface_token_here"


If you are using Mac or Linux:

    export HF_TOKEN="paste_your_huggingface_token_here"


### Step 3: Start the Simulation!
Now, run the baseline script. This drops the AI into the broken environment and tells it to fix all 3 bugs autonomously.

    python inference.py


### Step 4: Watch the Magic
Look at your terminal! You will see the AI reading files, making edits, and earning partial rewards. 

If it successfully fixes all three bugs, the final line in your terminal will print:
`[END] success=true steps=9 score=1.000`

---

## 🐳 Docker & Hugging Face Spaces (Live Dashboard)

This environment is fully containerized. To view the **Live DAG Dashboard** and watch the nodes turn green as the pipeline heals:

1. Deploy this repository to a Hugging Face Docker Space.
2. The `Dockerfile` will automatically build the web server.
3. Open the Space URL to see the Dashboard, or navigate to `/docs` (Swagger UI) to play as the AI yourself by manually triggering `/reset` and `/step` commands!