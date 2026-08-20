from fastapi import FastAPI
from api.router import router
import uvicorn

def create_app():
    app = FastAPI(title="Knowledge API", description="API for Knowledge Management", version="0.1.0")
    
    app.include_router(router)   
    
    return app



if __name__ == "__main__":
    uvicorn.run("api.main:create_app", host="127.0.0.1", port=8001, reload=True)