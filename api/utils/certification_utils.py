import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime


def generate_certificate_pdf(certificate_details):
    """
    Generate a PDF certificate with CertiPro styling theme.
    Maintains original content while matching the provided design aesthetic.
    """
    certificates_dir = os.path.join(os.getcwd(), 'certificates')
    os.makedirs(certificates_dir, exist_ok=True)
    timestamp = datetime.utcnow().strftime('%Y%m%d')
    filename = f"Certificate_{certificate_details['recipient_name'].replace(' ', '_')}_{timestamp}.pdf"
    file_path = os.path.join(certificates_dir, filename)

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    primary_color = "#2C3E50"
    secondary_color = "#3498DB"
    accent_color = "#7F8C8D"

    # Background frame
    c.setStrokeColor(primary_color)
    c.setLineWidth(2)
    c.rect(30, 30, width - 60, height - 60)
    # Header section
    c.setFillColor(secondary_color)
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(width / 2, height - 100, "CertiPro")

    c.setFillColor(accent_color)
    c.setFont("Helvetica", 16)
    c.drawCentredString(width / 2, height - 130, "Certification Management, Simplified")

    content_y = height - 200
    c.setFillColor(primary_color)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, content_y, "Compliance Certification")
    c.setFillColor(secondary_color)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, content_y - 60, certificate_details['recipient_name'])

    c.setFillColor(primary_color)
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, content_y - 130, f"Standard: {''.join(certificate_details['checklist'])}")


    c.setFillColor(accent_color)
    c.setFont("Helvetica", 12)
    issued_date = datetime.utcnow().strftime('%Y-%m-%d')
    c.drawCentredString(width / 2, height - 300, f"Issued on: {issued_date}")
    c.setFillColor(accent_color)
    c.setFont("Helvetica", 8)
    c.drawCentredString(width / 2, 40, "CertiPro Certification Platform - ISO Management Made Simple")

    c.save()

    return file_path