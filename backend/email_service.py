"""Email service for sending password reset emails."""

from flask import current_app, render_template
from flask_mail import Message


def send_password_reset_email(email: str, reset_token: str) -> None:
    """Send password reset email to user.
    
    Args:
        email: User's email address.
        reset_token: Secure reset token.
    """
    # Construct reset URL (frontend will handle this route)
    reset_url = f"http://localhost:3000/reset-password?token={reset_token}"
    
    # Create email message
    msg = Message(
        subject="Screen Time Competition - Password Reset Request",
        recipients=[email],
        sender=current_app.config["MAIL_DEFAULT_SENDER"]
    )
    
    # Render templates with reset URL
    msg.html = render_template('emails/password_reset.html', reset_url=reset_url)
    msg.body = render_template('emails/password_reset.txt', reset_url=reset_url)
    
    # Send email
    from . import mail
    mail.send(msg)
