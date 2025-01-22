import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
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
    certificates_dir = os.path.join(os.getcwd(), 'certificates')
    os.makedirs(certificates_dir, exist_ok=True)
    timestamp = datetime.utcnow().strftime('%Y%m%d')
    filename = f"Certificate_{certificate_details['recipient_name'].replace(' ', '_')}_{timestamp}.pdf"
    file_path = os.path.join(certificates_dir, filename)

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    c.setLineWidth(4)
    c.rect(20, 20, width - 40, height - 40)

    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2, height - 100, "Compliance Certification")

    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 150, certificate_details['recipient_name'])

    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, height - 180, f"Organization: {certificate_details['organization_id']}")

    c.drawCentredString(width / 2, height - 210, f"Standard: {''.join(certificate_details['checklist'])}")

    issued_date = datetime.utcnow().strftime('%Y-%m-%d')
    c.drawCentredString(width / 2, height - 270, f"Issued on: {issued_date}")

    c.line(width / 2 - 100, height - 320, width / 2 + 100, height - 320)
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height - 330, "Authorized Signature")

    c.showPage()
    c.save()

    return file_path
