from flask_mail import Message
from flask import url_for

from api.extensions import mail
def send_certification_email(certification):
    subject = 'Your Compliance Certification Issued'
    # Fetch organization members' emails
    organization = certification.organization
    recipients = [member.email for member in organization.members]
    body = f"""
    Hello {organization.name} Team,

    Congratulations! Your compliance certification for the audit '{certification.audit.name}' has been issued on {certification.issued_date}.

    You can download your certification here:
    {certification.certificate_pdf}

    Thank you for your dedication to maintaining high standards.

    Best regards,
    Certification Team
    """
    msg = Message(subject=subject, recipients=recipients, body=body)
    mail.send(msg)
def send_audit_notification(audit):
    subject = f'New Audit Scheduled: {audit.name}'
    # Fetch organization members' emails
    organization = audit.organization
    recipients = [member.email for member in organization.members]
    body = f"""
    Hello Team,

    A new audit titled '{audit.name}' has been scheduled for the organization '{organization.name}'.
    Scheduled Date: {audit.scheduled_date}

    Please prepare accordingly.

    Best regards,
    Audit Management
    """
    msg = Message(subject=subject, recipients=recipients, body=body)
    mail.send(msg)

def send_invitation_email(invitation, org_name, org_type, is_new_user=True):
    """
    Sends an invitation email to the specified user.

    :param invitation: The Invitation object.
    :param is_new_user: Boolean indicating if the invitation is for a new user registration.
    """
    if is_new_user:
        registration_link = url_for('Auth.RegisterInvitation', token=invitation.token, _external=True)
        subject = f'You are Invited to Join {org_name}'
        body = f'''
        Hello,

        You have been invited to join our platform as an {invitation.role.value}. Please click the link below to register:

        {registration_link}

        This invitation will expire on {invitation.expires_at.strftime('%Y-%m-%d %H:%M:%S')} UTC.

        If you did not expect this invitation, please ignore this email.

        Best regards,
        Your Company
        '''
    else:
        # Generate acceptance link
        acceptance_link = url_for(f'{org_type}.AcceptInvitation', token=invitation.token, _external=True)
        subject = f'You are Invited to Join {org_name}'
        body = f'''
        Hello,

        You have been invited to join our organization as an {invitation.role.value}. Please log in and accept the invitation by clicking the link below:

        {acceptance_link}

        Alternatively, you can accept the invitation by sending a POST request to the accept endpoint with your invitation token.

        This invitation will expire on {invitation.expires_at.strftime('%Y-%m-%d %H:%M:%S')} UTC.

        If you did not expect this invitation, please ignore this email.

        Best regards,
        Your Company
        '''

    msg = Message(subject=subject, recipients=[invitation.email], body=body)
    mail.send(msg)
