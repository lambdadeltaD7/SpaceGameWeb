from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from endpoints.auth import router as auth_router
from endpoints.admin import router as admin_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:8004",
        "http://127.0.0.1",
        "http://127.0.0.1:8004",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, tags=["register and auth"])
app.include_router(admin_router, tags=["admin stuff"])



