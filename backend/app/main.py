from contextlib import asynccontextmanager
from fastapi import FastAPI, Response, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.CV.routes import router as cv_routes
from app.users.routes import router as users_routes
from app.admin.routes import router as admin_routes
import time
import os

tags_metadata = [
    {
        "name": "DevSepOps",
        "description": "DevOps with Sep",
        "externalDocs": {
            "description": "Learn DevOps is easiest way with Sep",
            "url": "https://github.com/DevSepOps",
        },
    }
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    '''Simple lifespan without auto-migration'''
    print("🚀 Application starting up...")
    
    try:
        from app.core.database import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("🔗 Database connection successful")
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        if os.getenv("ENVIRONMENT") == "development":
            raise
    
    print("🎯 Application is ready to handle requests")
    
    yield
    
    print("🛑 Application shutting down...")

app = FastAPI(
    lifespan=lifespan,
    openapi_tags=tags_metadata,
    title="DevSepOps Resume API",
    description="Learn DevOps in easiest way with Sep - Resume Review System",
    summary="CI/CD pipelines, IaC templates, automation, and resume management",
    version="1.0.0",
    contact={
        "name": "Sepehr Maadani",
        "url": "https://github.com/sepehrmdn77",
        "email": "sepehrmaadani98@gmail.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://choosealicense.com/",
    }
)

# Adding routes to API
app.include_router(users_routes)
app.include_router(cv_routes)
app.include_router(admin_routes)

@app.get("/")
async def root():
    return {"message": "Resume Review API"}

# in case of cookie management
@app.post("/set-cookie", tags=["Cookie management"])
def set_cookie(response: Response):
    response.set_cookie(key="test", value="somthing")
    return {"message": "Cookies has been set successfully"}

@app.get("/get-cookie", tags=["Cookie management"])
def get_cookie(request: Request):
    return {"Requested cookie": request.cookies.get("test")}

# Calculating process time
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    print(exc.__dict__)
    error_response = {
        "error": True,
        "status_code": exc.status_code,
        "detail": exc.detail
    }
    return JSONResponse(status_code =exc.status_code, content=error_response)

@app.exception_handler(RequestValidationError)
async def http_validation_handler(request, exc):
    print(exc.__dict__)
    error_response = {
        "error": True,
        "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "detail": exc.errors()
    }
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=error_response)
