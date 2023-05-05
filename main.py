import uvicorn
from fastapi import FastAPI
from fastapi.routing import APIRouter

from api.endpoints import task_router, login_router, user_router, tag_router


app = FastAPI(title="Task manager")


main_api_router = APIRouter()


main_api_router.include_router(task_router, prefix="/task", tags=["task"])
main_api_router.include_router(login_router, prefix="/login", tags=["login"])
main_api_router.include_router(user_router, prefix="/user", tags=["user"])
main_api_router.include_router(tag_router, prefix="/tag", tags=["tag"])


app.include_router(main_api_router)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
