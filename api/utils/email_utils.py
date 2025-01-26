from flask import url_for, current_app
from flask_mail import Message

from api.extensions import mail


def send_cert_body_approval_email(user, certification_body):
    subject = 'Your Certification Body Creation Request Has Been Approved'
    body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto;">
        <p style="font-size: 16px; color: #333;">Hello <strong>{user.full_name}</strong>,</p>

        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
          <p style="margin: 0;">
            Your request to create the certification body<br>
            <strong style="color: #2c3e50; font-size: 18px;">{certification_body.name}</strong><br>
            has been approved. You have been elevated to a manager role.
          </p>
        </div>

        <p style="margin-top: 25px; color: #666;">
          Best regards,<br>
          <strong style="color: #2c3e50;">Admin Team</strong>
        </p>
      </body>
    </html>
    """
    msg = Message(subject=subject, recipients=[user.email], html=body)
    mail.send(msg)


def send_cert_body_rejection_email(user, cert_body_request):
    subject = 'Your Certification Body Creation Request Has Been Rejected'
    body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto;">
        <p style="font-size: 16px; color: #333;">Hello <strong>{user.full_name}</strong>,</p>

        <div style="background: #fff3f3; padding: 20px; border-radius: 8px;">
          <p style="margin: 0;">
            We regret to inform you that your request to create<br>
            <strong style="color: #c0392b; font-size: 18px;">{cert_body_request.certification_body_name}</strong><br>
            has been rejected.
          </p>

          <div style="margin-top: 15px; padding: 12px; background: #fff; border-radius: 4px;">
            <p style="margin: 0; color: #666;">
              <strong>Comments:</strong><br>
              {cert_body_request.admin_comment or 'No comments provided'}
            </p>
          </div>
        </div>

        <p style="margin-top: 25px; color: #666;">
          If you have any questions, please contact the admin team.<br><br>
          Best regards,<br>
          <strong style="color: #2c3e50;">Admin Team</strong>
        </p>
      </body>
    </html>
    """
    msg = Message(subject=subject, recipients=[user.email], html=body)
    mail.send(msg)


def send_cert_invitation_accepted_email(user, certification_body):
    subject = 'Invitation Accepted'
    body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto;">
        <p style="font-size: 16px; color: #333;">Hello <strong>{user.full_name}</strong>,</p>

        <div style="background: #e8f5e9; padding: 20px; border-radius: 8px;">
          <p style="margin: 0; text-align: center;">
            You have successfully joined<br>
            <strong style="color: #2c3e50; font-size: 20px;">
              {certification_body.name if certification_body else "the certification body"}
            </strong><br>
            as an <strong style="color: #27ae60;">{user.role.value}</strong>
          </p>
        </div>

        <p style="margin-top: 25px; color: #666;">
          Best regards,<br>
          <strong style="color: #2c3e50;">Admin Team</strong>
        </p>
      </body>
    </html>
    """
    msg = Message(subject=subject, recipients=[user.email], html=body)
    mail.send(msg)


def send_organization_approval_email(user, organization):
    subject = 'Your Organization Creation Request Has Been Approved'
    body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto;">
        <p style="font-size: 16px; color: #333;">Hello <strong>{user.full_name}</strong>,</p>

        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
          <p style="margin: 0;">
            Your request to create<br>
            <strong style="color: #2c3e50; font-size: 20px;">{organization.name}</strong><br>
            has been approved. You have been elevated to a manager role.
          </p>
        </div>

        <p style="margin-top: 25px; color: #666;">
          Best regards,<br>
          <strong style="color: #2c3e50;">Admin Team</strong>
        </p>
      </body>
    </html>
    """
    msg = Message(subject=subject, recipients=[user.email], html=body)
    mail.send(msg)


def send_organization_rejection_email(user, org_request):
    subject = 'Your Organization Creation Request Has Been Rejected'
    body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto;">
        <p style="font-size: 16px; color: #333;">Hello <strong>{user.full_name}</strong>,</p>

        <div style="background: #fff3f3; padding: 20px; border-radius: 8px;">
          <p style="margin: 0;">
            We regret to inform you that your request to create<br>
            <strong style="color: #c0392b; font-size: 18px;">{org_request.organization_name}</strong><br>
            has been rejected.
          </p>

          <div style="margin-top: 15px; padding: 12px; background: #fff; border-radius: 4px;">
            <p style="margin: 0; color: #666;">
              <strong>Comments:</strong><br>
              {org_request.admin_comment or 'No comments provided'}
            </p>
          </div>
        </div>

        <p style="margin-top: 25px; color: #666;">
          If you have any questions, please contact the admin team.<br><br>
          Best regards,<br>
          <strong style="color: #2c3e50;">Admin Team</strong>
        </p>
      </body>
    </html>
    """
    msg = Message(subject=subject, recipients=[user.email], html=body)
    mail.send(msg)


def send_invitation_accepted_email(user, organization):
    subject = 'Invitation Accepted'
    body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto;">
        <p style="font-size: 16px; color: #333;">Hello <strong>{user.full_name}</strong>,</p>

        <div style="background: #e8f5e9; padding: 20px; border-radius: 8px;">
          <p style="margin: 0; text-align: center;">
            You have successfully joined<br>
            <strong style="color: #2c3e50; font-size: 20px;">{organization.name}</strong><br>
            as an <strong style="color: #27ae60;">{user.role.value}</strong>
          </p>
        </div>

        <p style="margin-top: 25px; color: #666;">
          Best regards,<br>
          <strong style="color: #2c3e50;">Admin Team</strong>
        </p>
      </body>
    </html>
    """
    msg = Message(subject=subject, recipients=[user.email], html=body)
    mail.send(msg)


def send_certification_email(certification):
    subject = 'Your Compliance Certification Issued'
    download_url = url_for(
        'Certification.DownloadCertification',
        certificate_id=certification.id,
        _external=True
    )
    organization = certification.organization
    recipients = [user.email for user in organization.users]
    body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto;">
        <p style="font-size: 16px; color: #333;">Hello <strong>{organization.name} Team</strong>,</p>

        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
          <p style="margin: 0 0 15px 0;">
            Congratulations! Your compliance certification for:<br>
            <strong style="color: #2c3e50; font-size: 18px;">{certification.audit.name}</strong>
          </p>
          <p style="margin: 0;">
            Issued on: <strong>{certification.issued_date}</strong>
          </p>
        </div>

        <div style="text-align: center; margin: 25px 0;">
          <a href="{download_url}" 
             style="background: #27ae60; color: white; padding: 12px 25px; 
                    text-decoration: none; border-radius: 5px; display: inline-block;">
            Download Certification
          </a>
        </div>

        <p style="color: #666; margin-top: 20px;">
          Thank you for your dedication to maintaining high standards.<br><br>
          Best regards,<br>
          <strong style="color: #2c3e50;">Certification Team</strong>
        </p>
      </body>
    </html>
    """
    msg = Message(subject=subject, recipients=recipients, html=body)
    mail.send(msg)


def send_audit_notification(audit):
    subject = f'New Audit Scheduled: {audit.name}'
    organization = audit.organization
    recipients = [user.email for user in organization.users if user.email]

    if not recipients:
        print("No users found to notify for this organization.")
        return

    body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto;">
        <p style="font-size: 16px; color: #333;">Hello Team,</p>

        <div style="background: #e8f4fc; padding: 20px; border-radius: 8px;">
          <p style="margin: 0 0 15px 0;">
            New audit scheduled for:<br>
            <strong style="color: #2c3e50; font-size: 20px;">{organization.name}</strong>
          </p>
          <div style="background: white; padding: 15px; border-radius: 4px;">
            <p style="margin: 0;">
              <strong>Audit Title:</strong> {audit.name}<br>
              <strong>Scheduled Date:</strong> {audit.scheduled_date}
            </p>
          </div>
        </div>

        <p style="color: #666; margin-top: 25px;">
          Please prepare accordingly.<br><br>
          Best regards,<br>
          <strong style="color: #2c3e50;">Audit Management</strong>
        </p>
      </body>
    </html>
    """
    msg = Message(subject=subject, recipients=recipients, html=body)
    mail.send(msg)


def send_account_confirmation_email(user, confirmation_url):
    subject = "Confirm Your Email"
    body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto;">
        <p style="font-size: 16px; color: #333;">Hello <strong>{user.full_name}</strong>,</p>

        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
          <p style="margin: 0 0 15px 0;">Please confirm your email address:</p>
          <a href="{confirmation_url}" 
             style="background: #3498db; color: white; padding: 12px 25px; 
                    text-decoration: none; border-radius: 5px; display: inline-block;">
            Confirm Email
          </a>
        </div>

        <p style="color: #666; margin-top: 25px;">
          If you did not register for this account, please ignore this email.<br><br>
          Best regards,<br>
          <strong style="color: #2c3e50;">The Team</strong>
        </p>
      </body>
    </html>
    """
    msg = Message(subject=subject, recipients=[user.email], html=body)
    mail.send(msg)


def send_password_reset_email(user, reset_url):
    subject = "Password Reset Link"
    body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto;">
        <p style="font-size: 16px; color: #333;">Hello <strong>{user.full_name}</strong>,</p>

        <div style="background: #fff3e0; padding: 20px; border-radius: 8px;">
          <p style="margin: 0 0 15px 0;">Please reset your password:</p>
          <a href="{reset_url}" 
             style="background: #f39c12; color: white; padding: 12px 25px; 
                    text-decoration: none; border-radius: 5px; display: inline-block;">
            Reset Password
          </a>
          <p style="margin: 15px 0 0 0; color: #666; font-size: 14px;">
            This link will expire in 1 hour.
          </p>
        </div>

        <p style="color: #666; margin-top: 25px;">
          If you didn't request this, please ignore this email.<br><br>
          Best regards,<br>
          <strong style="color: #2c3e50;">The Team</strong>
        </p>
      </body>
    </html>
    """
    msg = Message(subject=subject, recipients=[user.email], html=body)
    mail.send(msg)


def send_revocation_email(invitation, org_name):
    subject = f'Your invitation to Join {org_name} has been revoked'
    body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto;">
        <p style="font-size: 16px; color: #333;">Hello,</p>

        <div style="background: #ffebee; padding: 20px; border-radius: 8px;">
          <p style="margin: 0 0 15px 0;">
            Your invitation to join<br>
            <strong style="color: #c0392b; font-size: 18px;">{org_name}</strong><br>
            as a <strong>{invitation.role.value}</strong> has been revoked.
          </p>
          <p style="margin: 0; color: #666;">
            Please contact your manager for more information.
          </p>
        </div>

        <p style="color: #666; margin-top: 25px;">
          If you did not expect this invitation, please ignore this email.<br><br>
          Best regards,<br>
          <strong style="color: #2c3e50;">Your Company</strong>
        </p>
      </body>
    </html>
    """
    msg = Message(subject=subject, recipients=[invitation.email], html=body)
    mail.send(msg)


def send_invitation_email(invitation, org_name, org_type, is_new_user=True):
    if is_new_user:
        registration_link = f"https://127.0.0.1:5000/auth/register?token={invitation.token}"
        subject = f'You are Invited to Join {org_name}'
        body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto;">
            <p style="font-size: 16px; color: #333;">Hello,</p>

            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
              <p style="margin: 0 0 15px 0;">
                You've been invited as<br>
                <strong style="color: #2c3e50; font-size: 18px;">{invitation.role.value}</strong>
              </p>
              <a href="{registration_link}" 
                 style="background: #27ae60; color: white; padding: 12px 25px; 
                        text-decoration: none; border-radius: 5px; display: inline-block;">
                Accept Invitation
              </a>
              <p style="margin: 15px 0 0 0; color: #666;">
                Expires: {invitation.expires_at.strftime('%Y-%m-%d')}
              </p>
            </div>

            <p style="color: #666; margin-top: 25px;">
              Best regards,<br>
              <strong style="color: #2c3e50;">Your Company</strong>
            </p>
          </body>
        </html>
        """
    else:
        acceptance_link = f"https://127.0.0.1:5000/organization/invitations/accept/?token={invitation.token}"
        subject = f'You are Invited to Join {org_name}'
        body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto;">
            <p style="font-size: 16px; color: #333;">Hello,</p>

            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
              <p style="margin: 0 0 15px 0;">
                Join <strong>{org_name}</strong> as<br>
                <strong style="color: #2c3e50; font-size: 18px;">{invitation.role.value}</strong>
              </p>
              <a href="{acceptance_link}" 
                 style="background: #3498db; color: white; padding: 12px 25px; 
                        text-decoration: none; border-radius: 5px; display: inline-block;">
                Accept Invitation
              </a>
              <div style="margin-top: 15px; color: #666; font-size: 14px;">
                <p style="margin: 10px 0;">
                  Expires: {invitation.expires_at.strftime('%Y-%m-%d %H:%M:%S')} UTC
                </p>
                <p style="margin: 10px 0;">
                  Or send POST request with your token
                </p>
              </div>
            </div>

            <p style="color: #666; margin-top: 25px;">
              Best regards,<br>
              <strong style="color: #2c3e50;">Your Company</strong>
            </p>
          </body>
        </html>
        """

    msg = Message(subject=subject, recipients=[invitation.email], html=body)
    mail.send(msg)


def send_audit_request_notification_to_cb_managers(audit_request, cb_managers):
    """
    Sends an email to each certification body manager about a new audit request.
    Each email contains links or instructions for approving or rejecting.
    """
    for manager in cb_managers:
        approve_url = url_for('Audit.AuditRequestAction', request_id=audit_request.id,
                              _external=True) + "?decision=approve"
        reject_url = url_for('Audit.AuditRequestAction', request_id=audit_request.id,
                             _external=True) + "?decision=reject"

        subject = f"Audit Request Pending: {audit_request.name}"
        body = f"""
                   <html>
                     <body style="font-family: Arial, sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto;">
                       <p style="font-size: 16px; color: #333;">
                         Hello <strong>{manager.full_name}</strong>,
                       </p>
    
                       <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                         <p style="margin: 0 0 15px 0;">
                           The organization <strong style="color: #2c3e50;">{audit_request.organization.name}</strong> 
                           has requested an audit:
                         </p>
                         <ul style="margin: 0 0 15px 0; padding-left: 18px; color: #555;">
                           <li><strong>Audit Name:</strong> {audit_request.name}</li>
                           <li><strong>Scheduled Date:</strong> {audit_request.scheduled_date}</li>
                           <li><strong>Standards:</strong> {audit_request.standard_ids}</li>
                         </ul>
                         <p style="margin: 0 0 5px 0;">
                           Please click on one of the links below to respond:
                         </p>
                         <p>
                           <a href="{approve_url}" style="color: #27ae60; text-decoration: none; font-weight: 
                           bold;">Approve Request</a> | <a href="{reject_url}" style="color: #c0392b; 
                           text-decoration: none; font-weight: bold;">Reject Request</a>
                         </p>
                       </div>
    
                       <p style="margin-top: 25px; color: #666;">
                         Best regards,<br>
                         <strong style="color: #2c3e50;">Audit Management System</strong>
                       </p>
                     </body>
                   </html>
                   """
        msg = Message(subject=subject, recipients=[manager.email], html=body)
        mail.send(msg)


def send_audit_request_response_to_org_managers(audit_request, org_managers, approved=True):
    """
    Notifies the organization managers that their audit request has been approved or rejected.
    """
    status_text = "approved" if approved else "rejected"

    for manager in org_managers:
        subject = f"Your Audit Request Has Been {status_text.title()}"
        body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto;">
            <p style="font-size: 16px; color: #333;">
              Hello <strong>{manager.full_name}</strong>,
            </p>

            <div style="background: #{'e8f5e9' if approved else 'fff3f3'}; 
                        padding: 20px; border-radius: 8px;">
              <p style="margin: 0 0 15px 0;">
                Your request for an audit 
                <strong style="color: #2c3e50;">({audit_request.name})</strong> 
                has been <strong style="color: #{'27ae60' if approved else 'c0392b'};">
                  {status_text}
                </strong> by the Certification Body.
              </p>
            </div>

            <p style="margin-top: 25px; color: #666;">
              If you have any questions, please contact your certification body manager.<br><br>
              Best regards,<br>
              <strong style="color: #2c3e50;">Audit Management System</strong>
            </p>
          </body>
        </html>
        """
        msg = Message(subject=subject, recipients=[manager.email], html=body)
        mail.send(msg)


def send_audit_created_notification(audit, organization_users):
    """
    Informs the entire organization that an audit was created.
    """
    for user in organization_users:
        subject = f"Audit Scheduled: {audit.name}"
        body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto;">
            <p style="font-size: 16px; color: #333;">Hello <strong>{user.full_name}</strong>,</p>

            <div style="background: #e8f4fc; padding: 20px; border-radius: 8px;">
              <p style="margin: 0 0 15px 0;">
                A new audit has been scheduled for your organization 
                <strong style="color: #2c3e50; font-size: 18px;">({audit.organization.name})</strong>:
              </p>
              <p style="margin: 0;">
                <strong>Audit Title:</strong> {audit.name}<br>
                <strong>Scheduled Date:</strong> {audit.scheduled_date}<br>
                <strong>Checklist / Standards:</strong> {audit.checklist}
              </p>
            </div>

            <p style="color: #666; margin-top: 25px;">
              Please prepare accordingly.<br><br>
              Best regards,<br>
              <strong style="color: #2c3e50;">Audit Management System</strong>
            </p>
          </body>
        </html>
        """
        msg = Message(subject=subject, recipients=[user.email], html=body)
        mail.send(msg)
