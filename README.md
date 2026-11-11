# 🐳 Docker Basics 🐳

A practical and structured guide to getting started with **Docker**, containerization and data persistence for modern development and Data Science workflows.

---

## Repository Structure

This repository is organized into two main modules:

```
docker-basics/
├── docker-setup-introduction/   # Theory, concepts & installation guides
└── app-todo/                    # Practical hands-on multi-container project
```

---

### 1. [docker-setup-introduction/](./docker-setup-introduction/)

This folder covers foundational knowledge and installation instructions for Docker across different operating systems.

- **[introduction.md](./docker-setup-introduction/introduction.md)**: A theoretical overview explaining:
  - What Docker is and why it matters
  - The *"works on my machine"* problem and how containerization solves it
  - Traditional deployment vs. Docker containers
  - Core Docker concepts: **Images**, **Containers**, **Volumes** and **Networks**
  - Why Docker is essential in Data Science for reproducibility and isolation
- **[setup_guide.pdf](./docker-setup-introduction/setup_guide.pdf)**: A step-by-step installation guide for **macOS**, **Windows** and **Linux**, comparing two setups:
  - **Multipass**: Lightweight Ubuntu VM running Docker in an isolated Linux environment
  - **Docker Desktop**: The official GUI application for a native desktop experience

---

### 2. [app-todo/](./app-todo/)

A hands-on, end-to-end example of containerizing a full-stack web application with **persistent storage**.

The application is a clean **TODO App** that allows users to create, view, and delete tasks with relative timestamps:

- **[app.py](./app-todo/app.py)**: Python backend built with **Flask** and **SQLAlchemy**. Connects to a PostgreSQL database via `DATABASE_URL` so that todos persist across container stops, restarts, and redeployments.
- **[templates/index.html](./app-todo/templates/index.html)**: Interactive frontend interface served via Flask templates.
- **[requirements.txt](./app-todo/requirements.txt)**: Python dependencies (`flask`, `humanize`, `psycopg2-binary`, `sqlalchemy`).
- **[Dockerfile](./app-todo/Dockerfile)**: Defines how to package the Flask application into a lightweight Python container image.
- **[docker-compose.yml](./app-todo/docker-compose.yml)**: Orchestrates the multi-container environment, linking the Flask web app with a persistent **PostgreSQL** database service and volume storage.

---

## Quickstart

To run the hands-on project with Docker Compose:

```bash
cd app-todo
docker compose up --build
```

Then visit **http://localhost:5000** in your browser.
