from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import pandas as pd

# -----------------------------
# БАЗА ДАННЫХ
# -----------------------------
Base = declarative_base()


class Student(Base):
    __tablename__ = 'students'

    id = Column(Integer, primary_key=True, autoincrement=True)
    last_name = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    faculty = Column(String, nullable=False)
    course = Column(String, nullable=False)
    grade = Column(Integer, nullable=False)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)


class StudentDB:
    def __init__(self, db_url='sqlite:///students.db'):
        self.engine = create_engine(db_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    # -----------------------------
    # STUDENTS
    # -----------------------------
    def insert_student(self, last_name, first_name, faculty, course, grade):
        session: Session = self.Session()
        student = Student(
            last_name=last_name,
            first_name=first_name,
            faculty=faculty,
            course=course,
            grade=grade
        )
        session.add(student)
        session.commit()
        session.refresh(student)
        session.close()
        return student

    def select_all_students(self):
        session: Session = self.Session()
        students = session.query(Student).all()
        session.close()
        return students

    def select_student(self, student_id):
        session: Session = self.Session()
        student = session.query(Student).filter(Student.id == student_id).first()
        session.close()
        return student

    def update_student(self, student_id, **kwargs):
        session: Session = self.Session()
        student = session.query(Student).filter(Student.id == student_id).first()
        if not student:
            session.close()
            return None
        for key, value in kwargs.items():
            setattr(student, key, value)
        session.commit()
        session.refresh(student)
        session.close()
        return student

    def delete_student(self, student_id):
        session: Session = self.Session()
        student = session.query(Student).filter(Student.id == student_id).first()
        if not student:
            session.close()
            return False
        session.delete(student)
        session.commit()
        session.close()
        return True

    # -----------------------------
    # USERS (AUTH)
    # -----------------------------
    def create_user(self, username, password):
        session = self.Session()
        user = User(username=username, password=password)
        session.add(user)
        session.commit()
        session.refresh(user)
        session.close()
        return user

    def get_user(self, username):
        session = self.Session()
        user = session.query(User).filter(User.username == username).first()
        session.close()
        return user


# -----------------------------
# Pydantic модели
# -----------------------------
class StudentCreate(BaseModel):
    last_name: str
    first_name: str
    faculty: str
    course: str
    grade: int = Field(..., ge=1, le=100)


class StudentUpdate(BaseModel):
    last_name: str | None = None
    first_name: str | None = None
    faculty: str | None = None
    course: str | None = None
    grade: int | None = Field(None, ge=1, le=100)


class UserCreate(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


# -----------------------------
# Проверка авторизации
# -----------------------------
def auth_required(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user_id


# -----------------------------
# FastAPI
# -----------------------------
app = FastAPI()
db = StudentDB()


# -----------------------------
# AUTH
# -----------------------------
@app.post("/auth/register")
def register(user: UserCreate):
    if db.get_user(user.username):
        raise HTTPException(400, "User already exists")

    new_user = db.create_user(user.username, user.password)
    return {"status": "registered", "user_id": new_user.id}


@app.post("/auth/login")
def login(user: UserLogin):
    u = db.get_user(user.username)
    if not u or u.password != user.password:
        raise HTTPException(401, "Invalid username or password")

    response = JSONResponse({"status": "logged_in"})
    response.set_cookie(key="user_id", value=str(u.id))
    return response


@app.post("/auth/logout")
def logout():
    response = JSONResponse({"status": "logged_out"})
    response.delete_cookie("user_id")
    return response


# -----------------------------
# STUDENTS — защищённые эндпоинты
# -----------------------------
@app.post("/students/", dependencies=[Depends(auth_required)])
def create_student(student: StudentCreate):
    s = db.insert_student(**student.dict())
    return {"status": "success", "id": s.id}


@app.get("/students/", dependencies=[Depends(auth_required)])
def get_students():
    students = db.select_all_students()
    return [s.__dict__ for s in students]


@app.get("/students/{student_id}", dependencies=[Depends(auth_required)])
def get_student(student_id: int):
    s = db.select_student(student_id)
    if not s:
        raise HTTPException(404, "Student not found")
    return s.__dict__


@app.put("/students/{student_id}", dependencies=[Depends(auth_required)])
def update_student(student_id: int, student: StudentUpdate):
    updated = db.update_student(
        student_id,
        **{k: v for k, v in student.dict().items() if v is not None}
    )
    if not updated:
        raise HTTPException(404, "Student not found")
    return {"status": "success"}


@app.delete("/students/{student_id}", dependencies=[Depends(auth_required)])
def delete_student(student_id: int):
    deleted = db.delete_student(student_id)
    if not deleted:
        raise HTTPException(404, "Student not found")
    return {"status": "success"}
