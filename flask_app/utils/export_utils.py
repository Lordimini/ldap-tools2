import csv
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from flask import make_response

def util_export_group_users_csv(group_name, users):
    """
    Export group users to a CSV file.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['CN', 'Full Name', 'Title', 'Service'])  # Write header
    for user in users:
        writer.writerow([user['CN'], user['fullName'], user['title'], user['service']])
    
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename=group_users_{group_name}.csv'
    response.headers['Content-type'] = 'text/csv'
    return response

def util_export_role_users_csv(role_cn, users):
    """
    Export role users to a CSV file.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['CN', 'Full Name', 'Title', 'Service'])  # Write header
    for user in users:
        writer.writerow([user['CN'], user['fullName'], user['title'], user['ou']])
    
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename=role_users_{role_cn}.csv'
    response.headers['Content-type'] = 'text/csv'
    return response

def util_export_service_users_csv(service_name, users):
    """
    Export service users to a CSV file.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['CN', 'Full Name', 'Title', 'Email'])  # Write header
    for user in users:
        writer.writerow([user['CN'], user['fullName'], user['title'], user['mail']])
    
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename=service_users_{service_name}.csv'
    response.headers['Content-type'] = 'text/csv'
    return response

def util_export_role_users_pdf(role_cn, users):
    """
    Export role users to a PDF file.
    """
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter  # Page dimensions

    # Add title
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, height - 50, f"Users in Role: {role_cn}")

    # Add table headers
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, height - 80, "CN")
    pdf.drawString(150, height - 80, "Full Name")
    pdf.drawString(300, height - 80, "Title")
    pdf.drawString(450, height - 80, "Service")

    # Add table rows
    pdf.setFont("Helvetica", 10)
    y = height - 100
    for user in users:
        pdf.drawString(50, y, user['CN'])
        pdf.drawString(150, y, user['fullName'])
        pdf.drawString(300, y, user['title'])
        pdf.drawString(450, y, user['ou'])
        y -= 20
        if y < 50:  # Handle page overflow
            pdf.showPage()
            y = height - 50

    # Save the PDF
    pdf.save()

    # Prepare the response
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename=role_users_{role_cn}.pdf'
    response.headers['Content-type'] = 'application/pdf'
    return response