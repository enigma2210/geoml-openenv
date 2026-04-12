from fastapi import FastAPI, Body
from fastapi.responses import HTMLResponse
from geoml_env import GeoMLEnv
from geoml_models import GeoMLAction

app = FastAPI()
env = GeoMLEnv()

@app.post("/reset")
async def reset_env(payload: dict = Body(default={})):
    obs = await env.reset()
    return {"observation": obs.model_dump()}

@app.post("/step")
async def step_env(action: GeoMLAction):
    obs, reward, done, info = await env.step(action)
    return {
        "observation": obs.model_dump(),
        "reward": reward.score,
        "done": done,
        "info": info
    }

@app.get("/state")
async def state_env():
    return await env.state()

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>GeoML-RescueEnv | Live Telemetry</title>
        <style>
            body { background-color: #0f172a; color: #f8fafc; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; flex-direction: column; align-items: center; padding: 50px; }
            h1 { color: #38bdf8; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 10px;}
            p { color: #94a3b8; max-width: 600px; text-align: center; margin-bottom: 40px; line-height: 1.6;}
            .dag-container { display: flex; align-items: center; justify-content: center; gap: 20px; background: #1e293b; padding: 40px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); border: 1px solid #334155;}
            .node { width: 160px; height: 80px; display: flex; align-items: center; justify-content: center; text-align: center; font-weight: bold; font-size: 14px; border-radius: 8px; border: 2px solid #475569; background: #0f172a; color: #64748b; transition: all 0.5s ease; position: relative;}
            .arrow { color: #475569; font-size: 24px; font-weight: bold; transition: color 0.5s ease;}
            
            /* Status Classes */
            .node.active { border-color: #ef4444; color: #ef4444; box-shadow: 0 0 15px rgba(239, 68, 68, 0.4); }
            .node.success { border-color: #10b981; background: rgba(16, 185, 129, 0.1); color: #10b981; box-shadow: 0 0 15px rgba(16, 185, 129, 0.4); }
            .arrow.success { color: #10b981; }

            .stats { margin-top: 30px; font-family: monospace; color: #cbd5e1; background: #000; padding: 15px 30px; border-radius: 6px; border: 1px solid #334155;}
        </style>
    </head>
    <body>
        <h1>GeoML-RescueEnv Telemetry</h1>
        <p>Live DAG state monitoring. As the autonomous agent deploys code patches to the micro-execution sandbox, the pipeline nodes will update in real-time.</p>
        
        <div class="dag-container">
            <div class="node success" id="node-0">1. System Boot</div>
            <div class="arrow" id="arrow-1">➔</div>
            <div class="node" id="node-1">2. Spatial<br>Projection</div>
            <div class="arrow" id="arrow-2">➔</div>
            <div class="node" id="node-2">3. Temporal<br>Alignment</div>
            <div class="arrow" id="arrow-3">➔</div>
            <div class="node" id="node-3">4. Memory<br>Chunking</div>
        </div>

        <div class="stats" id="status-text">Awaiting Agent Connection...</div>

        <script>
            async function fetchState() {
                try {
                    const response = await fetch('/state');
                    const data = await response.json();
                    const progress = data.max_progress;
                    
                    
                    for(let i=1; i<=3; i++) {
                        document.getElementById('node-'+i).className = 'node';
                        document.getElementById('arrow-'+i).className = 'arrow';
                    }

                    
                    for(let i=1; i<=3; i++) {
                        let node = document.getElementById('node-'+i);
                        let arrow = document.getElementById('arrow-'+i);
                        
                        if (progress >= i) {
                            node.className = 'node success';
                            arrow.className = 'arrow success';
                        } else if (progress == i - 1) {
                            node.className = 'node active';
                        }
                    }

                    let statusText = "Agent is debugging pipeline...";
                    if (progress === 3) statusText = "Pipeline Healthy";
                    document.getElementById('status-text').innerText = "Status: " + statusText + " | Max Progress: " + progress + "/3";

                } catch (e) {
                    console.error("Telemetry disconnected.");
                }
            }

            
            setInterval(fetchState, 1500);
            fetchState();
        </script>
    </body>
    </html>
    """

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
