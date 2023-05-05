from datetime import timedelta
from typing import Optional
import settings
from security import create_access_token
from fastapi import Depends
from fastapi import HTTPException
from fastapi.routing import APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
from api.schemas import Tag_
from api.schemas import TagCreate
from api.schemas import TaskCreate
from api.schemas import UserCreate
from api.schemas import UserShow
from api.schemas import TaskResponse
from db.models import Tag
from db.models import Task
from db.models import User
from db.session import get_db
from api.hashing import Hasher

task_router = APIRouter()
tag_router = APIRouter()
user_router = APIRouter()
login_router = APIRouter()


@tag_router.put("/add_tag")
async def add_tag(
        task_id: int, tag_name: str, user_id: int, db: AsyncSession = Depends(get_db)
) -> TaskResponse:
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    tag = await db.execute(
        select(Tag).where(Tag.tag == tag_name, Tag.user_id == user_id)
    )
    tag = tag.scalar()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    task.tags = tag
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return TaskResponse(
        id=task.id,
        user_id=task.user_id,
        title=task.title,
        tag_id=task.tag_id,
        created_at=task.created_at,
    )


@tag_router.post("/create_tag")
async def create_tag(item: TagCreate, db: AsyncSession = Depends(get_db)) -> Tag_:
    existing_tag = await db.execute(
        select(Tag).where(Tag.tag == item.tag, Tag.user_id == item.user_id)
    )
    existing_tag = existing_tag.scalar()

    if existing_tag:
        raise HTTPException(status_code=400, detail="Tag already exists")

    db_item = Tag(**item.dict())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return Tag_(tag=db_item.tag, user_id=db_item.user_id)


@tag_router.get("/get_all_tags")
async def get_all_tags(user_id: int, db: AsyncSession = Depends(get_db)) -> list[str]:
    tasks = await db.execute(select(Tag).filter_by(user_id=user_id))
    tasks = tasks.scalars().all()
    text = [i.tag for i in tasks]
    return text


@tag_router.get("/is_exist_tag")
async def is_exist_tag(tag: str, db: AsyncSession = Depends(get_db)) -> bool:
    stmt = select(Tag).where(Tag.tag == tag)
    result = await db.execute(stmt)
    return bool(result.scalar())


@tag_router.delete("/delete_tag")
async def delete_tag(
        user_id: int, tag: str, db: AsyncSession = Depends(get_db)
) -> dict[str, bool]:
    async with db.begin():
        tag_instance = await db.execute(select(Tag).filter_by(user_id=user_id, tag=tag))

        if not tag_instance:
            raise HTTPException(status_code=404, detail="Tag not found")

        await db.delete(tag_instance.scalars().first())
        await db.commit()
    return {"ok": True}


@task_router.post("/create")
async def create_task(
        obj: TaskCreate, db: AsyncSession = Depends(get_db)
) -> TaskResponse:
    if not obj.title or obj.title.strip() == "":
        raise HTTPException(status_code=400, detail="Task title cannot be empty")

    new_task = Task(
        user_id=obj.user_id,
        title=obj.title,
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    return TaskResponse(
        id=new_task.id,
        user_id=new_task.user_id,
        title=new_task.title,
        created_at=new_task.created_at,
    )


@task_router.delete("/delete_task")
async def delete_task(
        task_id: int, db: AsyncSession = Depends(get_db)
) -> dict[str, bool]:
    async with db.begin():
        task = await db.execute(select(Task).where(Task.id == task_id))
        task = task.scalar()

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        await db.delete(task)
        await db.commit()
    return {"ok": True}


# todo айограм оптимизейшен
@task_router.get("/get_all_tasks")
async def get_all_tasks(
        user_id: int, tag: Optional[str] = None, db: AsyncSession = Depends(get_db)
) -> list[TaskResponse]:
    async with db.begin():
        if tag:
            tasks = await db.execute(
                select(Task)
                .join(Task.tags)
                .filter(Task.user_id == user_id)
                .filter(Tag.tag == tag)
            )
            tasks = tasks.scalars().all()
        else:
            tasks = await db.execute(select(Task).filter(Task.user_id == user_id))
            tasks = tasks.scalars().all()
    return [
        TaskResponse(
            id=task.id,
            title=task.title,
            user_id=task.user_id,
            created_at=task.created_at,
        )
        for task in tasks
    ]


async def auth_user(email: str, password: str, db: AsyncSession) -> None | User:
    user = await db.execute(select(User).where(User.email == email))
    user = user.scalar()
    if not user:
        return
    if not Hasher.verify_password(password, user.hashed_password):
        return
    return user


@user_router.post("/create_user")
async def create_user(
        obj: UserCreate, db: AsyncSession = Depends(get_db)
) -> UserShow:
    new_task = User(
        email=obj.email,
        name=obj.name,
        hashed_password=Hasher.get_hashed_password(obj.password)
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    return UserShow(
        name=new_task.name,
        user_id=new_task.user_id,
        email=new_task.email
    )


@user_router.post("/token")
async def login_for_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await auth_user(form_data.username, form_data.password, db)
    print(user.hashed_password)
    if not user:
        raise HTTPException(status_code=401, detail='There is no user in database with this email')
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE)
    access_token = create_access_token(
        data={"sub": user.email, "other_custom_data": [1, 2, 3, 4]},
        expires_delta=access_token_expires,
    )
    return {'access_token': access_token, 'token_type': 'bearer'}
