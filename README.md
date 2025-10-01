# Learnevo - Django LMS  

Learnevo is a **Learning Management System (LMS)** built with Django.  
It provides a platform to manage courses, students, instructors, assignments, and online exams.  

---

## ✨ Features
- Authentication with **Custom User Model** (Student, Instructor, Admin Level 1, Admin Level 2)  
- Role-based dashboards  
- Course and class management  
- Online assignments management  
- Online exams (MCQ and descriptive)  
- Automatic grading for MCQ + manual grading for descriptive answers  
- Grade reports and progress tracking for students  
- Admin panel for full control  

---

## 🛠️ Tech Stack
- [Python 3.13](https://www.python.org/)  
- [Django 5.x](https://www.djangoproject.com/)  
- SQLite (default DB, can be switched to PostgreSQL/MySQL)  
- Bootstrap 5 (frontend)  

---

## 🚀 Getting Started
```bash
# Clone the repository
git clone https://github.com/<reza-khalili-dev>/learnevo.git
cd learnevo

# Create and activate virtualenv
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Run the development server
python manage.py runserver
