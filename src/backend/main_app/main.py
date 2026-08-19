from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from endpoints.auth import router as auth_router
from endpoints.admin import router as admin_router
from endpoints.planets import router as planets_router
from endpoints.worlds import router as worlds_router
from endpoints.users import router as users_router
from endpoints.transactions import router as transactions_router
from endpoints.miners import router as miners_router

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


app.include_router(auth_router, tags=["auth"])
app.include_router(admin_router, tags=["admin stuff"])
app.include_router(planets_router, tags=["planets"])
app.include_router(worlds_router, tags=["worlds"])
app.include_router(users_router, tags=["users"])
app.include_router(transactions_router, tags=["transactions"])
app.include_router(miners_router, tags=["miners"])






