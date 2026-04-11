from fastapi import FastAPI, Body
from geoml_env import GeoMLEnv
from geoml_models import GeoMLAction

app = FastAPI()
env = GeoMLEnv()

# The hackathon validator strictly sends an empty JSON {} to /reset via POST
@app.post("/reset")
async def reset_env(payload: dict = Body(default={})):
    obs = await env.reset()
    # Pydantic v2 uses model_dump() to convert objects to JSON
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