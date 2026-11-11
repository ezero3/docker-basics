from flask import Flask, request, render_template, redirect, url_for
import humanize
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
import os

app = Flask(__name__)

# ==========================================
# DATABASE
# ==========================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@db:5432/todos"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Todo(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True)
    task = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)


Base.metadata.create_all(engine)


@app.route("/")
def index():
    session = SessionLocal()
    todos = session.query(Todo).all()
    for todo in todos:
        todo.created_human = humanize.naturaltime(datetime.now() - todo.created_at)
    session.close()
    return render_template("index.html", todos=todos)


@app.route("/add", methods=["POST"])
def add():
    task = request.form.get("task")
    if task:
        session = SessionLocal()
        new_todo = Todo(task=task)
        session.add(new_todo)
        session.commit()
        session.close()
    return redirect(url_for("index"))


@app.route("/delete/<int:id>")
def delete(id):
    session = SessionLocal()
    todo = session.get(Todo, id)
    if todo:
        session.delete(todo)
        session.commit()
    session.close()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
