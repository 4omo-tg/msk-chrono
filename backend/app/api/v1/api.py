from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth, users, pois, routes, progress, files, 
    quizzes, verification, achievements, profile, friends, cosmetics, learning,
    time_machine, site_settings,
)

api_router = APIRouter()
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])
api_router.include_router(friends.router, prefix="/friends", tags=["friends"])
api_router.include_router(cosmetics.router, prefix="/cosmetics", tags=["cosmetics"])
api_router.include_router(pois.router, prefix="/pois", tags=["pois"])
api_router.include_router(routes.router, prefix="/routes", tags=["routes"])
api_router.include_router(progress.router, prefix="/progress", tags=["progress"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(quizzes.router, prefix="/quizzes", tags=["quizzes"])
api_router.include_router(verification.router, prefix="/verification", tags=["verification"])
api_router.include_router(achievements.router, prefix="/achievements", tags=["achievements"])
api_router.include_router(learning.router, prefix="/learning", tags=["learning"])
api_router.include_router(time_machine.router, prefix="/time-machine", tags=["time-machine"])
api_router.include_router(site_settings.router, prefix="/settings", tags=["settings"])
