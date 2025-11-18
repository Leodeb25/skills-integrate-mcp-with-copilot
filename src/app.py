"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlmodel import SQLModel, create_engine, Session, select
import os
from pathlib import Path
import models


app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")


# Database setup
DATABASE_URL = "sqlite:///./data.db"
engine = create_engine(DATABASE_URL, echo=False)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    # Seed initial activities if none exist
    with Session(engine) as session:
        stmt = select(models.Activity)
        results = session.exec(stmt)
        if not results.first():
            seed_activities(session)


def seed_activities(session: Session):
    sample = [
        ("Chess Club", "Learn strategies and compete in chess tournaments", "Fridays, 3:30 PM - 5:00 PM", 12,
         ["michael@mergington.edu", "daniel@mergington.edu"]),
        ("Programming Class", "Learn programming fundamentals and build software projects", "Tuesdays and Thursdays, 3:30 PM - 4:30 PM", 20,
         ["emma@mergington.edu", "sophia@mergington.edu"]),
        ("Gym Class", "Physical education and sports activities", "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM", 30,
         ["john@mergington.edu", "olivia@mergington.edu"]),
        ("Soccer Team", "Join the school soccer team and compete in matches", "Tuesdays and Thursdays, 4:00 PM - 5:30 PM", 22,
         ["liam@mergington.edu", "noah@mergington.edu"]),
        ("Basketball Team", "Practice and play basketball with the school team", "Wednesdays and Fridays, 3:30 PM - 5:00 PM", 15,
         ["ava@mergington.edu", "mia@mergington.edu"]),
        ("Art Club", "Explore your creativity through painting and drawing", "Thursdays, 3:30 PM - 5:00 PM", 15,
         ["amelia@mergington.edu", "harper@mergington.edu"]),
        ("Drama Club", "Act, direct, and produce plays and performances", "Mondays and Wednesdays, 4:00 PM - 5:30 PM", 20,
         ["ella@mergington.edu", "scarlett@mergington.edu"]),
        ("Math Club", "Solve challenging problems and participate in math competitions", "Tuesdays, 3:30 PM - 4:30 PM", 10,
         ["james@mergington.edu", "benjamin@mergington.edu"]),
        ("Debate Team", "Develop public speaking and argumentation skills", "Fridays, 4:00 PM - 5:30 PM", 12,
         ["charlotte@mergington.edu", "henry@mergington.edu"]),
    ]

    for name, desc, sched, max_p, participants in sample:
        activity = models.Activity(name=name, description=desc, schedule=sched, max_participants=max_p)
        session.add(activity)
        session.commit()
        session.refresh(activity)
        for email in participants:
            student = session.exec(select(models.Student).where(models.Student.email == email)).first()
            if not student:
                student = models.Student(email=email)
                session.add(student)
                session.commit()
                session.refresh(student)
            signup = models.Signup(student_id=student.id, activity_id=activity.id)
            session.add(signup)
        session.commit()


create_db_and_tables()


def activity_to_dict(activity: models.Activity):
    return {
        "name": activity.name,
        "description": activity.description,
        "schedule": activity.schedule,
        "max_participants": activity.max_participants,
        "participants": [s.email for s in activity.students]
    }


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    with Session(engine) as session:
        stmt = select(models.Activity)
        activities = session.exec(stmt).all()
        return [activity_to_dict(a) for a in activities]


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity (DB-backed)"""
    with Session(engine) as session:
        activity = session.exec(select(models.Activity).where(models.Activity.name == activity_name)).first()
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")

        # Refresh relationship
        session.refresh(activity)

        # Check if student exists, else create
        student = session.exec(select(models.Student).where(models.Student.email == email)).first()
        if not student:
            student = models.Student(email=email)
            session.add(student)
            session.commit()
            session.refresh(student)

        # Reload participants
        session.refresh(activity)
        if any(s.email == email for s in activity.students):
            raise HTTPException(status_code=400, detail="Student is already signed up")

        if len(activity.students) >= activity.max_participants:
            raise HTTPException(status_code=409, detail="Activity is full")

        signup = models.Signup(student_id=student.id, activity_id=activity.id)
        session.add(signup)
        session.commit()
        return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity (DB-backed)"""
    with Session(engine) as session:
        activity = session.exec(select(models.Activity).where(models.Activity.name == activity_name)).first()
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")

        student = session.exec(select(models.Student).where(models.Student.email == email)).first()
        if not student:
            raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

        # Find signup
        signup = session.exec(
            select(models.Signup).where(models.Signup.activity_id == activity.id, models.Signup.student_id == student.id)
        ).first()
        if not signup:
            raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

        session.delete(signup)
        session.commit()
        return {"message": f"Unregistered {email} from {activity_name}"}

