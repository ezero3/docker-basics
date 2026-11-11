# 🛠️ Hands-on Project: Containerized TODO App (`app-todo`)

This document provides a comprehensive, step-by-step breakdown of how the **TODO application** was built, containerized and evolved into a multi-container architecture with persistent database storage.

---

## 📋 Table of Contents
1. [Overview of the Application](#1-overview-of-the-application)
2. [Step 1: Containerizing the Web App (`Dockerfile` & `.dockerignore`)](#2-step-1-containerizing-the-web-app-dockerfile--dockerignore)
   - [Deep Dive into the Dockerfile](#deep-dive-into-the-dockerfile)
   - [The Layer Caching Strategy](#the-layer-caching-strategy)
   - [The Role of `.dockerignore`](#the-role-of-dockerignore)
3. [Step 2: Building and Running the First Container (Terminal Commands)](#3-step-2-building-and-running-the-first-container-terminal-commands)
   - [Port Mapping Explained](#port-mapping-explained)
   - [The Ephemeral Storage Problem](#the-ephemeral-storage-problem)
4. [Step 3: Multi-Container Architecture with Docker Compose](#4-step-3-multi-container-architecture-with-docker-compose)
   - [Best Practice: One Container per Service](#best-practice-one-container-per-service)
   - [Database Integration in the Code](#database-integration-in-the-code)
   - [Deep Dive into `docker-compose.yml`](#deep-dive-into-docker-composeyml)
   - [Persistent Storage with Docker Volumes](#persistent-storage-with-docker-volumes)
5. [Step 4: Launching and Testing the Stack](#5-step-4-launching-and-testing-the-stack)
6. [Summary of Key Docker Concepts Learned](#6-summary-of-key-docker-concepts-learned)

---

## 1. Overview of the Application

The project located in [`app-todo/`](./) is a lightweight Python web application:
- **Backend ([app.py](./app.py)):** Built with the **Flask** micro-framework. It exposes endpoints to list (`/`), add (`/add`), and delete (`/delete/<id>`) tasks.
- **Frontend ([templates/index.html](./templates/index.html)):** A clean user interface rendered via Jinja2 templates.
- **Timestamps:** Dynamically formatted into relative time (e.g., *"3 minutes ago"*, *"just now"*) using the Python `humanize` library.

### The Evolution:
* **Initial version:** Used an in-memory Python list (`todos = []`). While functional, all tasks were immediately wiped out whenever the application or container stopped.
* **Final version:** Integrated with a **PostgreSQL** database managed through **SQLAlchemy**, ensuring complete data persistence across container lifecycles.

---

## 2. Step 1: Containerizing the Web App (`Dockerfile` & `.dockerignore`)

To run this application inside Docker, we need a recipe that tells Docker how to assemble an environment containing the operating system, runtime, libraries, application code, and startup commands. That recipe is the [`Dockerfile`](./Dockerfile).

### Deep Dive into the Dockerfile

Here is the exact [`Dockerfile`](./Dockerfile) used for the web service, explained line by line:

```dockerfile
# 1. Base Image
FROM python:3.12-slim

# 2. Working Directory inside the container
WORKDIR /app

# 3. Copy dependencies list first
COPY requirements.txt requirements.txt

# 4. Install dependencies
RUN pip install -r requirements.txt

# 5. Copy the rest of the application code
COPY . .

# 6. Document the exposed network port
EXPOSE 5000

# 7. Default command executed when the container starts
CMD ["python", "app.py"]
```

#### Line-by-Line Breakdown:

1. **`FROM python:3.12-slim`**
   - **What it does:** Sets the base image from Docker Hub.
   - **Why this image:** It provides a minimal Linux distribution (Debian) with Python 3.12 pre-installed. The `-slim` variant strips out non-essential packages to keep image size small and downloads fast.
   - **Alternative base images:** For a Node.js app you might choose `FROM node:20`, or for a general-purpose Linux system `FROM ubuntu:22.04` (where you would install Python manually).
   - **Containers vs. Virtual Machines:** Note that a container **does not include its own operating system kernel**. It packages its own filesystem, libraries, and processes, but directly shares the host machine's Linux kernel. This makes containers orders of magnitude lighter, faster to boot (milliseconds vs. minutes), and less resource-intensive than traditional VMs.

2. **`WORKDIR /app`**
   - **What it does:** Sets `/app` as the active working directory inside the container's virtual filesystem.
   - **Why it matters:** If the directory does not exist, Docker creates it automatically. All subsequent instructions (`COPY`, `RUN`, `CMD`) are executed relative to this path.

3. **`COPY requirements.txt requirements.txt`**
   - **What it does:** Copies only the dependency specification file from your local computer into `/app/requirements.txt` inside the container.

4. **`RUN pip install -r requirements.txt`**
   - **What it does:** Runs the standard Python package manager to install Flask, Humanize, SQLAlchemy, and Psycopg2.
   - **Build-time execution:** `RUN` commands are executed **during the image build phase**. The output (the installed packages) is permanently frozen into that image layer.

5. **`COPY . .`**
   - **What it does:** Copies all remaining files and folders from the local project folder into `/app` inside the container (e.g., `app.py`, `templates/`).
   - *(Note on `COPY` vs `ADD`: `COPY` is the standard and transparent command for transferring local files. `ADD` is an alternative that additionally supports downloading files from remote URLs or automatically unpacking tar archives).*

6. **`EXPOSE 5000`**
   - **What it does:** Acts as metadata and documentation indicating that the web server inside the container listens on port `5000`.
   - **Important nuance:** `EXPOSE` **does not actually publish or open the port on the host machine**. It is an informative label. Actual network access requires port mapping when starting the container (`-p` flag).

7. **`CMD ["python", "app.py"]`**
   - **What it does:** Specifies the default command to execute when a container is instantiated and launched from this image.
   - **`RUN` vs. `CMD` (The crucial distinction):**
     - **`RUN`**: Executed *at build time* to construct the image (e.g., compile code, install packages). Saves changes into the image layer.
     - **`CMD`**: Executed *at runtime* when the container starts. Does not alter the image.
   - **Best Practice:** A Dockerfile should have only **one** `CMD` instruction, placed at the end, formatted in *exec form* (`["executable", "param1", "param2"]`) to allow proper Linux signal handling (such as graceful shutdown with `Ctrl+C`).

---

### The Layer Caching Strategy

A common question is: *Why did we copy `requirements.txt` separately in step 3, if step 5 (`COPY . .`) would copy it anyway?*

The answer lies in **Docker Layer Caching**:

```
Layer 1: FROM python:3.12-slim         ──► [CACHED]
Layer 2: WORKDIR /app                  ──► [CACHED]
Layer 3: COPY requirements.txt ...     ──► [CACHED] (only re-runs if requirements.txt changes)
Layer 4: RUN pip install ...           ──► [CACHED] (skipped if Layer 3 was cached!)
Layer 5: COPY . .                      ──► [EXECUTED] (re-runs whenever app.py or HTML changes)
```

- Docker builds images in stacked layers. Each instruction creates a new cached layer.
- When you rebuild an image, Docker checks if the inputs for a layer have changed. If they haven't, it reuses the cached layer and skips execution.
- Installing Python packages (`pip install`) takes significant time. Application source code (`app.py`, HTML templates) changes frequently, while dependencies change rarely.
- By separating the two steps, editing your code allows Docker to reuse the cached `pip install` layer instantly, reducing rebuild times from minutes to seconds!

---

### The Role of `.dockerignore`

When `COPY . .` runs, it copies everything in the directory into the container image. Without a filter, this would needlessly include temporary files, sensitive configurations, or unnecessary files like `Dockerfile` itself.

The [`.dockerignore`](./.dockerignore) file instructs Docker which files to exclude during the build context transfer:

```
Dockerfile
docker-compose.yml
explanation.md
.dockerignore
__pycache__/
*.pyc
```

**Benefits:**
- Reduces the size of the final image.
- Speeds up the build process by keeping the build context small.
- Prevents leaking local caches (`__pycache__`) or documentation into production images.

---

## 3. Step 2: Building and Running the First Container (Terminal Commands)

Once the `Dockerfile` is written, we build the image using the Docker CLI.

### 1. Build the Docker Image

```bash
docker build -t todo-app .
```

- **`docker build`**: Instructs the Docker Engine to create an image based on instructions in a `Dockerfile`.
- **`-t todo-app`**: Tags (names) the resulting image as `todo-app`.
- **`.` (dot)**: Specifies the **build context** (the current directory where the Dockerfile and source files reside).

---

### 2. Run the Container (Initial Attempt)

```bash
docker run todo-app
```

The container starts up, runs `python app.py`, and Flask logs:
```
* Running on http://127.0.0.1:5000
```

However, opening `http://localhost:5000` in the computer's web browser produces a connection error: **"Site cannot be reached"**.

**Why?**
The container is an isolated environment with its own private network stack. The port `5000` is open **inside** the container, but it has not been mapped to the **host** machine.

---

### 3. Port Mapping Explained

To bridge the host computer and the container, we use the `-p` (publish / port map) flag:

```bash
docker run -p 5000:5000 todo-app
```

```
   Host Machine Browser                 Docker Container
┌───────────────────────────┐         ┌───────────────────────────┐
│  http://localhost:5000    │ ──────► │  Port 5000 (Flask app)    │
└───────────────────────────┘         └───────────────────────────┘
               ▲                                    ▲
               │                                    │
               └───────── -p [HOST_PORT]:[CONTAINER_PORT]
```

- The first `5000` is the port on your physical computer (host).
- The second `5000` is the internal port inside the container where Flask is listening.
- Now, navigating to `http://localhost:5000` successfully opens the TODO App!

---

### The Ephemeral Storage Problem

In this initial stage, the application saved todos into an in-memory Python list:

```python
# In-memory storage (volatile)
todos = []
```

When you stop the container (`Ctrl+C` or `docker stop`) and start a new one, **all tasks disappear**. Containers are designed to be **ephemeral** (stateless and disposable). To persist data across container lifecycles, an external database with persistent storage is required.

**THIS WAS THE FIRST VERSION OF THE TO DO APP, THAT IS NOT PRESENT IN THIS REPOSITORY.**
---

## 4. Step 3: Multi-Container Architecture with Docker Compose

### Best Practice: One Container per Service

Could we install PostgreSQL inside the same container alongside Flask?  
Technically yes, but in Docker architecture, **one container should handle exactly one concern/service**:
1. **Lightweight & Modular:** Independent scaling and resource limits.
2. **Simplified Maintenance:** You can update or restart the database without taking down or rebuilding the web server.
3. **Reusability:** Pre-built official images (like `postgres`) can be plugged in directly without writing custom setup scripts.

---

### Database Integration in the Code

To support PostgreSQL:
1. Added database drivers to [`requirements.txt`](./requirements.txt):
   - `psycopg2-binary`: PostgreSQL adapter for Python.
   - `sqlalchemy`: Object-Relational Mapping (ORM) to interact with tables using Python classes rather than raw SQL strings.
2. Updated [`app.py`](./app.py) to read connection parameters from an environment variable:
   ```python
   DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://apptodo:todoapp@db:5432/todo_db")
   engine = create_engine(DATABASE_URL)
   ```
   Notice the host name in the URL: `@db:5432`. In Docker, containers on the same network reach each other using their service name as their DNS address.

---

### Deep Dive into `docker-compose.yml`

Instead of manually running multiple `docker run` and `docker network` commands, **Docker Compose** lets us configure all services declaratively in a single file: [`docker-compose.yml`](./docker-compose.yml).

```yaml
services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://apptodo:todoapp@db:5432/todo_db
    depends_on:
      - db

  db:
    image: postgres:15.3
    environment:
      POSTGRES_USER: apptodo
      POSTGRES_PASSWORD: todoapp
      POSTGRES_DB: todo_db
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

#### Detailed Breakdown of each block:

#### 1. The `web` Service (Flask Application)
- **`build: .`**: Tells Docker to build the image using the `Dockerfile` located in the current directory (`.`).
- **`ports: - "5000:5000"`**: Maps port 5000 of the host to port 5000 of the container, making the web UI accessible from your browser.
- **`environment:`**: Injects environment variables into the container at startup.
  - `DATABASE_URL`: Supplies the database credentials and location. The hostname `db` resolves directly to the `db` container.
- **`depends_on: - db`**: Specifies startup dependency order. Docker Compose will start the `db` service before starting `web`.

#### 2. The `db` Service (PostgreSQL Database)
- **`image: postgres:15.3`**: Uses the official PostgreSQL version 15.3 image directly from Docker Hub. No custom `Dockerfile` needed.
- **`environment:`**: Supplies the initialization parameters required by the official Postgres image:
  - `POSTGRES_USER`: The administrative username.
  - `POSTGRES_PASSWORD`: The user password.
  - `POSTGRES_DB`: The default database created upon startup (`todo_db`).
- **`volumes: - pgdata:/var/lib/postgresql/data`**: Mounts the named volume `pgdata` to the official directory where PostgreSQL stores database files.

#### 3. Top-Level `volumes:`
- **`pgdata:`**: Declares the named volume managed by Docker on the host storage.

---

### Persistent Storage with Docker Volumes

A **Docker Volume** is a dedicated storage directory created and managed by Docker directly on the host machine filesystem:

```
  Host Filesystem (Managed by Docker)                   Container: 'db'
┌──────────────────────────────────────┐             ┌───────────────────────────────────┐
│  Docker Volume: 'pgdata'             │ ◄─────────► │  /var/lib/postgresql/data        │
│  (Persists independently on host)    │   Mounted   │  (PostgreSQL storage directory)   │
└──────────────────────────────────────┘             └───────────────────────────────────┘
```

- When the `db` container writes tables and records, they are written directly to `pgdata`.
- If the `db` container crashes, is stopped, or is destroyed, the data in `pgdata` remains intact.
- When a new `db` container starts up with the same volume attached, it instantly regains access to all existing records.

---

## 5. Step 4: Launching and Testing the Stack

### Launch the Application

From within the `app-todo/` directory, launch the complete environment:

```bash
docker compose up --build
```

#### What this command does:
- **`docker compose up`**: Reads `docker-compose.yml`, sets up an internal network, creates required volumes, and launches both containers.
- **`--build`**: Forces Docker to rebuild the custom image (`web`) before starting.
  > ⚠️ **Always use `--build`** whenever you edit `requirements.txt`, `app.py`, or your HTML templates. Without `--build`, Docker Compose reuses previously built images and will not reflect your latest code changes.

---

### Verifying Data Persistence

1. Open your browser at **`http://localhost:5000`**.
2. Add several tasks to the list (e.g., *"Study Docker"*, *"Review SQLAlchemy"*).
3. In the terminal, stop the running containers by pressing `Ctrl+C` (or running `docker compose down` in another window).
4. Restart the stack:
   ```bash
   docker compose up
   ```
5. Refresh **`http://localhost:5000`**:  
   🎉 **All your tasks are still there!** Data survived container shutdown thanks to the persistent volume `pgdata`.

---

## 6. Summary of Key Docker Concepts Learned

| Concept | Purpose in this Project |
|---|---|
| **Image** | The immutable blueprint containing Python, packages, and code (`python:3.12-slim`, `postgres:15.3`). |
| **Container** | The live, isolated runtime instance executing our code (`web`, `db`). |
| **Dockerfile** | Step-by-step instructions to assemble the custom Flask web image. |
| **Layer Caching** | Optimization separating `COPY requirements.txt` + `RUN pip install` from application code. |
| **.dockerignore** | Excludes non-essential files from the build context to keep images small and clean. |
| **Port Mapping (`-p`)** | Forwards traffic from host ports to internal container ports (`5000:5000`). |
| **Docker Compose** | Multi-container orchestrator that starts, connects, and configures multiple services with one command. |
| **Volume** | Dedicated host storage mounted into containers to ensure data persistence across lifecycles. |
| **Internal DNS** | Automatic hostname resolution inside Docker networks (allowing `web` to reach `db:5432`). |
