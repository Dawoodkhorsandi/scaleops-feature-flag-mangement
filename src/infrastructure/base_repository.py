from typing import Any, Generic, Type, TypeVar

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    A generic repository with basic asynchronous CRUD operations.

    This class is designed to be inherited by specific repository classes.
    The session is passed to each method, ensuring a request-scoped session.
    """

    def __init__(self, model: Type[ModelType], db_session: AsyncSession):
        """
        Initializes the repository with a model and a database session.

        :param model: The SQLAlchemy model class.
        :param db_session: The request-scoped async database session.
        """
        self.model = model
        self.db = db_session

    async def get(self, _id: Any) -> ModelType | None:
        """
        Get a single record by its primary key.

        :param id: The primary key of the record.
        :return: The model instance or None if not found.
        """
        statement = select(self.model).where(self.model.id == _id)
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def get_all(self, *, skip: int = 0, limit: int = 100) -> list[ModelType]:
        """
        Get all records with pagination.

        :param skip: Number of records to skip.
        :param limit: Maximum number of records to return.
        :return: A list of model instances.
        """
        statement = select(self.model).offset(skip).limit(limit)
        result = await self.db.execute(statement)
        return result.scalars().all()

    async def create(self, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record.

        :param obj_in: The Pydantic schema with the creation data.
        :return: The created model instance.
        """
        obj_in_data = obj_in.model_dump()
        db_obj = self.model(**obj_in_data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, *, db_obj: ModelType, obj_in: UpdateSchemaType) -> ModelType:
        """
        Update an existing record.

        :param db_obj: The existing model instance to update.
        :param obj_in: The Pydantic schema with the update data.
        :return: The updated model instance.
        """
        update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, *, id: Any) -> ModelType | None:
        """
        Delete a record by its primary key.

        This method first fetches the object to ensure it exists
        and to return the deleted object, which is a common REST API pattern.

        :param db: The async database session.
        :param id: The primary key of the record to delete.
        :return: The deleted model instance or None if not found.
        """
        db_obj = await self.get(id)
        if db_obj:
            await self.db.delete(db_obj)
            await self.db.commit()
        return db_obj
