from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship


class Signup(SQLModel, table=True):
    """Association table between students and activities."""
    student_id: Optional[int] = Field(default=None, foreign_key="student.id", primary_key=True)
    activity_id: Optional[int] = Field(default=None, foreign_key="activity.id", primary_key=True)


class Student(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, nullable=False)
    signups: List["Activity"] = Relationship(back_populates="students", link_model=Signup)


class Activity(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, nullable=False, unique=True)
    description: Optional[str] = None
    schedule: Optional[str] = None
    max_participants: int = Field(default=30)
    students: List[Student] = Relationship(back_populates="signups", link_model=Signup)
