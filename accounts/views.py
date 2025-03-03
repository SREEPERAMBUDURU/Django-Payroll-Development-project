from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .forms import EmployeeRegistrationForm, HrRegistrationForm, LoginForm, LeaveRequestForm
from .models import User, LeaveRequest
from datetime import datetime, timedelta
from calendar import monthrange
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from wkhtmltopdf.views import PDFTemplateResponse
from django.core.mail import EmailMessage
from .forms import UserUpdateForm
import io
from django.contrib.auth.decorators import login_required




# Home view
def home(request):
    return render(request, 'accounts/home.html')

# Register employee view
def register_employee(request):
    if request.method == 'POST':
        form = EmployeeRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Employee registration successful. Please login.')
            return redirect('login')
        else:
            messages.error(request, 'Employee registration failed. Please correct the errors below.')
    else:
        form = EmployeeRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form, 'title': 'Register Employee'})

# Register HR view
def register_hr(request):
    if request.method == 'POST':
        form = HrRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'HR registration successful. Please login.')
            return redirect('login')
        else:
            messages.error(request, 'HR registration failed. Please correct the errors below.')
    else:
        form = HrRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form, 'title': 'Register HR'})

# Login view
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                if user.is_employee:
                    return redirect('employee_dashboard')
                elif user.is_hr:
                    return redirect('hr_dashboard')
            else:
                messages.error(request, 'Invalid username or password. Please try again.')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form, 'title': 'Login'})

# Employee dashboard view
def employee_dashboard(request):
    leave_count = 15  # Assuming total leave count for an employee
    leaves_taken = LeaveRequest.objects.filter(employee=request.user, is_approved=True).count()
    remaining_paid_leaves = leave_count - leaves_taken
    approved_leave_requests = LeaveRequest.objects.filter(employee=request.user, is_approved=True)

    context = {
        'leave_count': leave_count,
        'leaves_taken': leaves_taken,
        'remaining_paid_leaves': remaining_paid_leaves,
        'approved_leave_requests': approved_leave_requests,
    }
    return render(request, 'accounts/employee_dashboard.html', context)

# HR dashboard view
def hr_dashboard(request):
    leave_requests = LeaveRequest.objects.filter(hr=request.user)

    context = {
        'leave_requests': leave_requests,
    }
    return render(request, 'accounts/hr_dashboard.html', context)

def employee_leave_management(request):
    form = LeaveRequestForm(request.POST or None)
    total_paid_leaves =15  # Assuming total leave count for an employee
    approved_leave_requests = LeaveRequest.objects.filter(employee=request.user, is_approved=True)
    pending_leave_requests = LeaveRequest.objects.filter(employee=request.user, is_approved=None)
    denied_leave_requests = LeaveRequest.objects.filter(employee=request.user, is_approved=False)

    # Calculate total leaves taken by summing up all approved leave requests
    leaves_taken = sum((leave_request.end_date - leave_request.start_date).days + 1 for leave_request in approved_leave_requests)

    # Calculate paid leaves taken by summing up all approved leave requests except 'Leave Without Pay'
    paid_leaves_taken = sum((leave_request.end_date - leave_request.start_date).days + 1
                            for leave_request in approved_leave_requests
                            if leave_request.leave_type != 'Leave Without Pay')

    remaining_paid_leaves = total_paid_leaves - paid_leaves_taken

    if form.is_valid():
        leave_request = form.save(commit=False)
        leave_request.employee = request.user
        leave_request.is_approved = None  # Ensure is_approved is set to None
        leave_request.save()
        messages.success(request, 'Leave request submitted successfully.')

        # Check if the leave type is 'Leave Without Pay'
        if leave_request.leave_type != 'Leave Without Pay':
            # Display message only if using paid leaves and they are exhausted
            if remaining_paid_leaves <= 0:
                messages.warning(request, "You have used all paid leave out of 15.")

        return redirect('employee_leave_management')

    context = {
        'form': form,
        'remaining_paid_leaves': max(0, remaining_paid_leaves),  # Ensure non-negative remaining leaves
        'leaves_taken': leaves_taken,  # Ensure this variable accurately reflects total leave days taken
        'approved_leave_requests': approved_leave_requests,
        'pending_leave_requests': pending_leave_requests,
        'denied_leave_requests': denied_leave_requests,
        'total_paid_leaves': total_paid_leaves,
    }
    return render(request, 'accounts/employee_leave_management.html', context)

# HR leave management view
def hr_leave_management(request):
    leave_requests = LeaveRequest.objects.filter(hr=request.user)

    if request.method == 'POST':
        leave_id = request.POST.get('leave_id')
        action = request.POST.get('action')
        leave_request = get_object_or_404(LeaveRequest, id=leave_id)

        if action == 'approve':
            leave_request.is_approved = True
            leave_request.approved_by = request.user
            leave_request.save()
            messages.success(request, 'Leave request approved.')
        elif action == 'deny':
            leave_request.is_approved = False
            leave_request.approved_by = request.user
            leave_request.save()
            messages.success(request, 'Leave request denied.')

        return redirect('hr_leave_management')

    context = {
        'leave_requests': leave_requests,
    }
    return render(request, 'accounts/hr_leave_management.html', context)

def payroll_management(request):
    employees = User.objects.filter(is_employee=True)
    selected_employee = None
    salary_details = None
    selected_month = None
    total_working_days_yearly = 250
    paid_leave_count = 15  # Assuming total paid leave count for an employee in a year

    if request.method == 'POST':
        employee_id = request.POST.get('employee')
        month = request.POST.get('month')

        # Get incentives and bonuses, defaulting to None if not provided
        incentives = request.POST.get('incentives')
        bonuses = request.POST.get('bonuses')

        if employee_id and month:
            selected_employee = User.objects.get(id=employee_id)
            position = selected_employee.position
            selected_month = month

            # Set base salary and net salary based on the position
            if position == 'Specialist':
                base_salary = 60000
                net_salary = 50000
            elif position == 'Project Manager':
                base_salary = 80000
                net_salary = 70000
            elif position == 'Software Designer':
                base_salary = 90000
                net_salary = 80000
            else:
                base_salary = 0
                net_salary = 0

            # Calculate leaves taken and unpaid leaves separately for the selected month
            year, month = map(int, month.split('-'))
            days_in_month = monthrange(year, month)[1]

            start_date = datetime(year, month, 1)
            end_date = datetime(year, month, days_in_month)

            # Filter approved leave requests that overlap with the selected month
            approved_leave_requests = LeaveRequest.objects.filter(
                employee=selected_employee,
                is_approved=True,
                start_date__lte=end_date,
                end_date__gte=start_date
            )

            # Initialize variables for calculations
            leaves_taken = 0
            unpaid_leaves = 0

            # Calculate leaves taken and unpaid leaves
            for leave_request in approved_leave_requests:
                leave_start = max(start_date, datetime.combine(leave_request.start_date, datetime.min.time()))
                leave_end = min(end_date, datetime.combine(leave_request.end_date, datetime.max.time()))

                leave_days = (leave_end - leave_start).days + 1
                leaves_taken += leave_days

                # Calculate unpaid leaves only for the month of the leave request
                if leave_request.leave_type == 'Leave Without Pay' and leave_start.month == month:
                    unpaid_leaves += leave_days
                elif leave_start.month == month:
                    unpaid_leaves += max(0, leave_days - paid_leave_count)

            # Calculate the daily salary
            daily_salary = net_salary / days_in_month

            # Initialize incentives and bonuses to 0 if not provided
            incentives = float(incentives) if incentives else 0
            bonuses = float(bonuses) if bonuses else 0

            # Calculate the salary deduction for unpaid leaves
            salary_deduction = daily_salary * unpaid_leaves

            # Calculate the final salary after deduction, adding incentives and bonuses
            final_salary = net_salary - salary_deduction + incentives + bonuses

            salary_details = {
                'base_salary': base_salary,
                'net_salary': net_salary,
                'month': f"{year}-{month:02}",
                'leaves_taken': leaves_taken,
                'unpaid_leaves': unpaid_leaves,
                'daily_salary': daily_salary,
                'salary_deduction': salary_deduction,
                'final_salary': final_salary,
                'incentives': incentives,
                'bonuses': bonuses,
            }

            # Redirect to calculate_salary.html with salary_details context
            return render(request, 'accounts/calculate_salary.html', {
                'salary_details': salary_details,
                'selected_employee': selected_employee,
                'selected_month': selected_month,
            })

    context = {
        'employees': employees,
        'selected_employee': selected_employee,
        'salary_details': salary_details,
        'selected_month': selected_month,
    }
    return render(request, 'accounts/payroll_management.html', context)

    
def calculate_salary(request):
    # Your view logic here
    return render(request, 'accounts/calculate_salary.html')


def send_salary_email(request):
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        selected_month = request.POST.get('selected_month')
        base_salary = request.POST.get('base_salary')
        net_salary = request.POST.get('net_salary')
        leaves_taken = request.POST.get('leaves_taken')
        unpaid_leaves = request.POST.get('unpaid_leaves')
        daily_salary = request.POST.get('daily_salary')
        salary_deduction = request.POST.get('salary_deduction')
        incentives = request.POST.get('incentives')
        bonuses = request.POST.get('bonuses')
        final_salary = request.POST.get('final_salary')

        employee = get_object_or_404(User, id=employee_id)

        # Render HTML content for email (optional, if you want to include HTML in email)
        html_content = render_to_string('accounts/salary_email.html', {
            'employee': employee,
            'selected_month': selected_month,
            'base_salary': base_salary,
            'net_salary': net_salary,
            'leaves_taken': leaves_taken,
            'unpaid_leaves': unpaid_leaves,
            'daily_salary': daily_salary,
            'salary_deduction': salary_deduction,
            'incentives': incentives,
            'bonuses': bonuses,
            'final_salary': final_salary,
        })

        # Create PDF attachment
        response = PDFTemplateResponse(request=request,
                                       template='accounts/salary_email.html',
                                       filename=f'Salary_Details_{selected_month}_{employee.username}.pdf',
                                       context={
                                           'employee': employee,
                                           'selected_month': selected_month,
                                           'base_salary': base_salary,
                                           'net_salary': net_salary,
                                           'leaves_taken': leaves_taken,
                                           'unpaid_leaves': unpaid_leaves,
                                           'daily_salary': daily_salary,
                                           'salary_deduction': salary_deduction,
                                           'incentives': incentives,
                                           'bonuses': bonuses,
                                           'final_salary': final_salary,
                                       })

        # Generate PDF content
        rendered_pdf_content = response.rendered_content

        # Create EmailMessage instance
        email = EmailMessage(
            subject=f"Salary Details for {selected_month}",
            body="Please find attached your salary details.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[employee.email],
        )

        # Attach PDF file
        email.attach(f'Salary_Details_{selected_month}_{employee.username}.pdf', rendered_pdf_content, 'application/pdf')

        # Send email
        email.send()

        messages.success(request, f'Salary details sent to {employee.username} via email.')
        return redirect('payroll_management')  # Replace with your actual redirect URL
    else:
        return redirect('payroll_management')  # Redirect if not a POST request




@login_required
def user_management(request):
    user_data = request.user

    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your data has been updated successfully.')
            # Redirect to a different URL or refresh the current page to clear POST data
            return redirect('user_management')
        else:
            messages.error(request, 'Error updating your data. Please correct the errors.')
    else:
        form = UserUpdateForm(instance=request.user)

    return render(request, 'accounts/user_management.html', {'form': form, 'user_data': user_data})
