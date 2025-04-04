from typing import List, Optional, Any, Dict
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    is_active: bool = True


class UserCreate(UserBase):
    password: Optional[str] = None


class UserUpdate(UserBase):
    password: Optional[str] = None


class UserInDB(UserBase):
    id: int
    is_superuser: bool = False
    google_id: Optional[str] = None
    token_expiry: Optional[datetime] = None

    class Config:
        orm_mode = True


class User(UserInDB):
    pass


# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None


# Google OAuth schemas
class GoogleAuthRequest(BaseModel):
    code: str
    redirect_uri: str


class GoogleToken(BaseModel):
    access_token: str
    refresh_token: Optional[str]
    expires_in: int
    token_type: str
    id_token: Optional[str] = None


# Course schemas
class CourseBase(BaseModel):
    name: str
    section: Optional[str] = None
    description: Optional[str] = None
    room: Optional[str] = None


class CourseCreate(CourseBase):
    google_course_id: str
    user_id: int


class CourseUpdate(CourseBase):
    pass


class CourseInDB(CourseBase):
    id: int
    google_course_id: str
    created_at: datetime
    updated_at: datetime
    user_id: int

    class Config:
        orm_mode = True


class Course(CourseInDB):
    pass


# Assignment schemas
class AssignmentBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None


class AssignmentCreate(AssignmentBase):
    google_assignment_id: str
    course_id: int
    user_id: int


class AssignmentUpdate(AssignmentBase):
    pass


class AssignmentInDB(AssignmentBase):
    id: int
    google_assignment_id: str
    created_at: datetime
    updated_at: datetime
    course_id: int
    user_id: int

    class Config:
        orm_mode = True


class Assignment(AssignmentInDB):
    course: Optional[Course] = None


# Material schemas
class MaterialBase(BaseModel):
    title: str
    type: str
    url: Optional[str] = None
    content: Optional[str] = None
    processed_content: Optional[str] = None


class MaterialCreate(MaterialBase):
    google_material_id: Optional[str] = None
    assignment_id: int


class MaterialUpdate(MaterialBase):
    pass


class MaterialInDB(MaterialBase):
    id: int
    google_material_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    assignment_id: int

    class Config:
        orm_mode = True


class Material(MaterialInDB):
    pass


# Draft schemas
class DraftBase(BaseModel):
    content: str
    status: str = "draft"
    feedback: Optional[str] = None


class DraftCreate(DraftBase):
    user_id: int
    assignment_id: int


class DraftUpdate(DraftBase):
    submission_date: Optional[datetime] = None


class DraftInDB(DraftBase):
    id: int
    created_at: datetime
    updated_at: datetime
    submission_date: Optional[datetime] = None
    user_id: int
    assignment_id: int

    class Config:
        orm_mode = True


class Draft(DraftInDB):
    pass


# AI Generation schemas
class GenerationRequest(BaseModel):
    assignment_id: int
    course_context: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)


class GenerationResponse(BaseModel):
    content: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)