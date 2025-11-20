# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import pandas as pd

Base = declarative_base()

# Модель SQLAlchemy
class Student(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True, autoincrement=True)
    last_name = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    faculty = Column(String, nullable=False)
    course = Column(String, nullable=False)
    grade = Column(Integer, nullable=False)

# Класс для работы с БД
class StudentDB:
    def __init__(self, db_url='sqlite:///students.db'):
        self.engine = create_engine(db_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

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

    def select_all(self):
        session: Session = self.Session()
        students = session.query(Student).all()
        session.close()
        return students

    def select_by_id(self, student_id):
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

    def load_from_csv(self, csv_path):
        df = pd.read_csv(csv_path)
        session: Session = self.Session()
        for _, row in df.iterrows():
            student = Student(
                last_name=row['Фамилия'],
                first_name=row['Имя'],
                faculty=row['Факультет'],
                course=row['Курс'],
                grade=int(row['Оценка'])
            )
            session.add(student)
        session.commit()
        session.close()

# Pydantic модель для FastAPI
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

# FastAPI сервис
app = FastAPI()
db = StudentDB()
# db.load_from_csv('students.csv')  # Если нужно загрузить CSV

@app.post("/students/", response_model=dict)
def create_student(student: StudentCreate):
    s = db.insert_student(**student.dict())
    return {"status": "success", "id": s.id}

@app.get("/students/", response_model=list[dict])
def get_students():
    students = db.select_all()
    return [s.__dict__ for s in students]

@app.get("/students/{student_id}", response_model=dict)
def get_student(student_id: int):
    s = db.select_by_id(student_id)
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")
    return s.__dict__

@app.put("/students/{student_id}", response_model=dict)
def update_student(student_id: int, student: StudentUpdate):
    updated = db.update_student(student_id, **{k: v for k, v in student.dict().items() if v is not None})
    if not updated:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"status": "success"}

@app.delete("/students/{student_id}", response_model=dict)
def delete_student(student_id: int):
    deleted = db.delete_student(student_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"status": "success"}
