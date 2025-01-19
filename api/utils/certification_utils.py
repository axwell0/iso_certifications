# utils/certification_utils.py

import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from datetime import datetime

def generate_certificate_pdf(certificate_details):
    """
    Generate a PDF certificate based on provided details.

    Args:
        certificate_details (dict): A dictionary containing certificate information.
            Expected keys:
                - recipient_name (str)
                - organization_name (str)
                - standard (str)
                - compliance_status (str)

    Returns:
        str: The file path to the generated PDF certificate.
    """
    # Define the directory to save certificates
    certificates_dir = os.path.join(os.getcwd(), 'certificates')
    os.makedirs(certificates_dir, exist_ok=True)

    # Generate a unique filename based on timestamp and recipient name
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    filename = f"Certificate_{certificate_details['recipient_name'].replace(' ', '_')}_{timestamp}.pdf"
    file_path = os.path.join(certificates_dir, filename)

    # Create a PDF canvas
    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    # Draw border
    c.setLineWidth(4)
    c.rect(20, 20, width - 40, height - 40)

    # Title
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2, height - 100, "Compliance Certification")

    # Recipient Name
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 150, certificate_details['recipient_name'])

    # Organization Name
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, height - 180, f"Organization: {certificate_details['organization_name']}")

    # Standard
    c.drawCentredString(width / 2, height - 210, f"Standard: {certificate_details['standard']}")

    # Compliance Status
    c.drawCentredString(width / 2, height - 240, f"Compliance Status: {certificate_details['compliance_status']}")

    # Issued Date
    issued_date = datetime.utcnow().strftime('%Y-%m-%d')
    c.drawCentredString(width / 2, height - 270, f"Issued on: {issued_date}")

    # Signature Line
    c.line(width / 2 - 100, height - 320, width / 2 + 100, height - 320)
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height - 330, "Authorized Signature")

    # Finalize the PDF
    c.showPage()
    c.save()

    return file_path
