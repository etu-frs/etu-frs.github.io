import os
import sys
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

sendgrid_key = os.environ.get('SENDGRID_API_KEY')

def send_email(
    to_email: str,
    from_email: str,
    subject: str,
    text_content: str | None = None,
    html_content: str | None = None
) -> bool:
    """
    Send an email using SendGrid.
    
    Args:
        to_email: Recipient email address
        from_email: Sender email address
        subject: Email subject
        text_content: Plain text content (if html_content is None)
        html_content: HTML content (takes precedence over text_content)
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    if not sendgrid_key:
        print("SendGrid API key not set", file=sys.stderr)
        return False
    
    sg = SendGridAPIClient(sendgrid_key)

    message = Mail(
        from_email=Email(from_email),
        to_emails=To(to_email),
        subject=subject
    )

    if html_content:
        message.content = Content("text/html", html_content)
    elif text_content:
        message.content = Content("text/plain", text_content)
    else:
        print("No content provided for email", file=sys.stderr)
        return False

    try:
        sg.send(message)
        print(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"SendGrid error: {e}", file=sys.stderr)
        return False

def send_contact_form_notification(name: str, email: str, subject: str, message: str, admin_email: str) -> bool:
    """
    Send a notification to the admin when a contact form is submitted.
    
    Args:
        name: Name of the person who submitted the form
        email: Email of the person who submitted the form
        subject: Subject of the message
        message: Message content
        admin_email: Email address of the admin to notify
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    # معالجة الرسالة للعرض في HTML
    message_html = message.replace('\n', '<br>')
    
    html_content = f"""
    <h2>رسالة جديدة من نموذج الاتصال</h2>
    <p><strong>الاسم:</strong> {name}</p>
    <p><strong>البريد الإلكتروني:</strong> {email}</p>
    <p><strong>الموضوع:</strong> {subject}</p>
    <p><strong>الرسالة:</strong></p>
    <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px;">
        {message_html}
    </div>
    """
    
    return send_email(
        to_email=admin_email,
        from_email="noreply@firas-designs.com",
        subject=f"رسالة جديدة: {subject}",
        html_content=html_content
    )

def send_testimonial_notification(name: str, company: str, rating: int, content: str, admin_email: str) -> bool:
    """
    Send a notification to the admin when a new testimonial is submitted.
    
    Args:
        name: Name of the person who submitted the testimonial
        company: Company of the person (if provided)
        rating: Rating given (1-5)
        content: Testimonial content
        admin_email: Email address of the admin to notify
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    # Star rating HTML
    stars_html = ""
    for i in range(5):
        if i < rating:
            stars_html += "★"  # Filled star
        else:
            stars_html += "☆"  # Empty star
    
    # معالجة الرسالة للعرض في HTML
    content_html = content.replace('\n', '<br>')
    
    html_content = f"""
    <h2>تقييم جديد من أحد العملاء</h2>
    <p><strong>الاسم:</strong> {name}</p>
    <p><strong>الشركة:</strong> {company or 'غير محدد'}</p>
    <p><strong>التقييم:</strong> <span style="color: #fbbf24; font-size: 20px;">{stars_html}</span> ({rating}/5)</p>
    <p><strong>التعليق:</strong></p>
    <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; font-style: italic;">
        {content_html}
    </div>
    <p style="margin-top: 20px;">
        <a href="#" style="display: inline-block; padding: 10px 15px; background-color: #10b981; color: white; text-decoration: none; border-radius: 5px; margin-right: 10px;">اعتماد التقييم</a>
        <a href="#" style="display: inline-block; padding: 10px 15px; background-color: #ef4444; color: white; text-decoration: none; border-radius: 5px;">حذف التقييم</a>
    </p>
    <p style="color: #666; font-size: 0.9em;">ملاحظة: يجب عليك تسجيل الدخول إلى لوحة التحكم للموافقة على هذا التقييم أو حذفه.</p>
    """
    
    return send_email(
        to_email=admin_email,
        from_email="noreply@firas-designs.com",
        subject="تقييم جديد بانتظار الموافقة",
        html_content=html_content
    )