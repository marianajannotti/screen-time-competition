"""Email service for sending notification emails."""

from flask import current_app, render_template
from flask_mail import Message


def send_password_reset_email(email: str, reset_token: str) -> None:
    """Send password reset email to user.
    
    Args:
        email: User's email address.
        reset_token: Secure reset token.
    """
    # Construct reset URL (frontend will handle this route)
    # Uses FRONTEND_URL from config, defaults to Vite dev server
    frontend_url = current_app.config.get("FRONTEND_URL", "http://localhost:5173")
    reset_url = f"{frontend_url}/reset-password?token={reset_token}"
    
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
    from .. import mail
    mail.send(msg)


def send_badge_notification(email: str, username: str, badge_name: str) -> None:
    """Send badge earned notification email to user.
    
    Args:
        email: User's email address.
        username: User's username for personalization.
        badge_name: Name of the badge that was earned.
    """
    # Construct profile URL (frontend will handle this route)
    frontend_url = current_app.config.get("FRONTEND_URL", "http://localhost:5173")
    profile_url = f"{frontend_url}/profile"
    
    # Create email message
    msg = Message(
        subject=f"🎉 New Badge Unlocked: {badge_name}!",
        recipients=[email],
        sender=current_app.config["MAIL_DEFAULT_SENDER"]
    )
    
    # Render templates with badge info
    msg.html = render_template(
        'emails/badge_earned.html',
        username=username,
        badge_name=badge_name,
        profile_url=profile_url
    )
    msg.body = render_template(
        'emails/badge_earned.txt',
        username=username,
        badge_name=badge_name,
        profile_url=profile_url
    )
    
    # Send email
    from .. import mail
    mail.send(msg)


def send_friend_request_notification(
    recipient_email: str,
    recipient_username: str,
    requester_username: str
) -> None:
    """Send friend request notification email.
    
    Args:
        recipient_email: Email of the user receiving the request.
        recipient_username: Username of the user receiving the request.
        requester_username: Username of the user sending the request.
    """
    # Construct friends page URL
    frontend_url = current_app.config.get("FRONTEND_URL", "http://localhost:5173")
    friends_url = f"{frontend_url}/friends"
    
    # Create email message
    msg = Message(
        subject=f"👋 {requester_username} sent you a friend request!",
        recipients=[recipient_email],
        sender=current_app.config["MAIL_DEFAULT_SENDER"]
    )
    
    # Render templates with friend request info
    msg.html = render_template(
        'emails/friend_request.html',
        recipient_username=recipient_username,
        requester_username=requester_username,
        friends_url=friends_url
    )
    msg.body = render_template(
        'emails/friend_request.txt',
        recipient_username=recipient_username,
        requester_username=requester_username,
        friends_url=friends_url
    )
    
    # Send email
    from .. import mail
    mail.send(msg)


def send_friend_request_accepted_notification(
    requester_email: str,
    requester_username: str,
    accepter_username: str
) -> None:
    """Send notification when friend request is accepted.
    
    Args:
        requester_email: Email of the user who sent the original request.
        requester_username: Username of the user who sent the request.
        accepter_username: Username of the user who accepted the request.
    """
    # Construct friends page URL
    frontend_url = current_app.config.get("FRONTEND_URL", "http://localhost:5173")
    friends_url = f"{frontend_url}/friends"
    
    # Create email message
    msg = Message(
        subject=f"🎉 {accepter_username} accepted your friend request!",
        recipients=[requester_email],
        sender=current_app.config["MAIL_DEFAULT_SENDER"]
    )
    
    # Render templates with acceptance info
    msg.html = render_template(
        'emails/friend_request_accepted.html',
        requester_username=requester_username,
        accepter_username=accepter_username,
        friends_url=friends_url
    )
    msg.body = render_template(
        'emails/friend_request_accepted.txt',
        requester_username=requester_username,
        accepter_username=accepter_username,
        friends_url=friends_url
    )
    
    # Send email
    from .. import mail
    mail.send(msg)


def send_welcome_email(email: str, username: str) -> None:
    """Send welcome email to newly registered user.
    
    Args:
        email: User's email address.
        username: User's username for personalization.
    """
    # Construct app URL
    frontend_url = current_app.config.get("FRONTEND_URL", "http://localhost:5173")
    app_url = frontend_url
    
    # Create email message
    msg = Message(
        subject="Welcome to Offy - Let's Build Better Screen Time Habits! 🎉",
        recipients=[email],
        sender=current_app.config["MAIL_DEFAULT_SENDER"]
    )
    
    # Render templates with welcome info
    msg.html = render_template(
        'emails/welcome.html',
        username=username,
        app_url=app_url
    )
    msg.body = render_template(
        'emails/welcome.txt',
        username=username,
        app_url=app_url
    )
    
    # Send email
    from .. import mail
    mail.send(msg)
