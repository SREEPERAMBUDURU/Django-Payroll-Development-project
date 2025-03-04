Payroll Management System

Project Overview:-
This project was developed collaboratively by a team of three members. 
My specific contributions include:
✔ Payroll Calculation Logic & Salary Deduction (Main Backend Feature)
✔ Leave Management System (Backend Logic & Validation)
✔ REST API Development for Payroll & Leave Requests
✔ PDF Payslip Generation (wkhtmltopdf Integration)
✔ Email Automation for Salary Slips

The Payroll Management System is a Django-based web application that automates payroll processing, leave tracking, and payslip generation. It simplifies HR tasks by integrating salary calculations, leave deductions, and automated payslip emails.

Key Features:-

Automated Payroll Calculation based on employee attendance.

Leave Management System for employees & HR approvals.

Dynamic PDF Payslip Generation using wkhtmltopdf.

Automated Email Dispatch of salary slips.

Role-Based Access Control for HR and employees.

REST API Integration for payroll, leave, and authentication.


Technologies Used:-

Backend: Django, Django REST Framework

Database: SQLite

Frontend: HTML, CSS

PDF Generation: wkhtmltopdf

Email Service: Mailtrap (SMTP)

Version Control: Git & GitHub

📥 Installation & Setup

Clone the repository:

git clone https://github.com/yourusername/payroll-management.git
cd payroll-management

Create and activate a virtual environment:

python -m venv venv
source venv/bin/activate  # For Linux/macOS
venv\Scripts\activate  # For Windows

Install dependencies:

pip install -r requirements.txt

Run migrations:

python manage.py migrate

Start the development server:

python manage.py runserver

API Endpoints:-

Employee Registration: POST /register/employee/

HR Registration: POST /register/hr/

Login: POST /login/

Submit Leave Request: POST /employee/leave/

Approve/Deny Leave: POST /hr/leave/

Process Payroll: POST /payroll_management/

Send Payslip via Email: POST /send_salary_email/



Email: sreeperambuduru2003@gmail.com
