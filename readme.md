# Team Collaboration System (Backend)

A **Django + DRF** backend for a team collaboration system with **task management**, **role-based access**, **file attachments**, **real-time notifications**, and **JWT authentication**.

---

## Features

- Role-based access: **Admin**, **Manager**, and **Employee**
- Task management:
  - CRUD operations for tasks
  - Assign tasks to employees
  - Attach files to tasks
  - Filter tasks by **status** and **deadline**
  - Mark tasks as completed
- User management:
  - Registration, login
  - JWT-based authentication
  - Password change with refresh token rotation
- Real-time notifications using **Redis + Django Channels**
- Pagination for task lists
- Swagger UI documentation for all APIs
- Dockerized setup

---

## Tech Stack

- Python 3.13
- Django 5.x
- Django REST Framework (DRF)
- DRF-YASG for Swagger Documentation
- Django Channels for WebSockets
- Redis (for real-time notifications)
- SQLite / MySQL for database
- Docker & Docker Compose

---


