from fastapi import FastAPI

from app.api.routes import router


app = FastAPI(title="Model Router Budget API")

app.include_router(router)
