import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional
from datetime import datetime

class EmailSender:
    """Handle email sending for Exotrac chatbot"""
    
    def __init__(self):
        """Initialize email sender"""
        self.company_email = "support@exotrac.com"
        self.company_name = "Exotrac LLC"
        
        # Email configuration (can be customized)
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_username = os.environ.get('SMTP_USERNAME', '')
        self.smtp_password = os.environ.get('SMTP_PASSWORD', '')
        
        # Track sent emails
        self.sent_emails = []
    
    def send_email(self, email_data: Dict) -> Dict:
        """
        Send email using SMTP
        
        Args:
            email_data: Dictionary with 'subject', 'body', 'to_email', 'from_email'
        
        Returns:
            Dictionary with status and message
        """
        try:
            # Validate email data
            if not email_data.get('to_email'):
                return {
                    'success': False,
                    'message': 'Recipient email address is required',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = email_data.get('subject', 'Exotrac Yard Management Solutions')
            msg['From'] = f"{self.company_name} <{email_data.get('from_email', self.company_email)}>"
            msg['To'] = email_data['to_email']
            
            # Add body
            body = email_data.get('body', '')
            msg.attach(MIMEText(body, 'plain'))
            
            # Check if SMTP is configured
            if not self.smtp_username or not self.smtp_password:
                # Save to file instead (for demo purposes)
                return self._save_email_to_file(email_data)
            
            # Send email via SMTP
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            # Track sent email
            self.sent_emails.append({
                'to': email_data['to_email'],
                'subject': email_data['subject'],
                'type': email_data.get('type', 'unknown'),
                'timestamp': datetime.now().isoformat(),
                'status': 'sent'
            })
            
            return {
                'success': True,
                'message': f"Email sent successfully to {email_data['to_email']}",
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            # If SMTP fails, save to file
            return self._save_email_to_file(email_data, error=str(e))
    
    def _save_email_to_file(self, email_data: Dict, error: Optional[str] = None) -> Dict:
        """Save email to file (when SMTP is not configured)"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"email_{email_data.get('type', 'outreach')}_{timestamp}.txt"
        
        # Create emails directory if it doesn't exist
        os.makedirs('emails', exist_ok=True)
        filepath = os.path.join('emails', filename)
        
        # Write email to file
        with open(filepath, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("EXOTRAC EMAIL - SAVED FOR REVIEW\n")
            f.write("=" * 70 + "\n\n")
            
            if error:
                f.write(f"NOTE: SMTP not configured - {error}\n")
                f.write("This email has been saved to file for manual sending.\n\n")
            else:
                f.write("NOTE: SMTP credentials not configured.\n")
                f.write("This email has been saved to file for manual sending.\n\n")
            
            f.write(f"To: {email_data.get('to_email', 'NOT PROVIDED')}\n")
            f.write(f"From: {email_data.get('from_email', self.company_email)}\n")
            f.write(f"Subject: {email_data.get('subject', '')}\n")
            f.write(f"Type: {email_data.get('type', 'unknown')}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write("\n" + "-" * 70 + "\n")
            f.write("EMAIL BODY:\n")
            f.write("-" * 70 + "\n\n")
            f.write(email_data.get('body', ''))
            f.write("\n\n" + "=" * 70 + "\n")
        
        # Track saved email
        self.sent_emails.append({
            'to': email_data.get('to_email', 'NOT PROVIDED'),
            'subject': email_data.get('subject', ''),
            'type': email_data.get('type', 'unknown'),
            'timestamp': datetime.now().isoformat(),
            'status': 'saved_to_file',
            'filename': filepath
        })
        
        return {
            'success': True,
            'message': f"Email saved to {filepath} (SMTP not configured)",
            'filename': filepath,
            'timestamp': datetime.now().isoformat()
        }
    
    def send_to_main_company(self, prospect_data: Dict) -> Dict:
        """
        Send prospect information to main company email for demo scheduling
        
        Args:
            prospect_data: Dictionary with prospect information
        
        Returns:
            Dictionary with status
        """
        subject = f"New Demo Request - {prospect_data.get('company_name', 'Prospect')}"
        
        body = f"""New prospect interested in Exotrac demo:

PROSPECT INFORMATION:
Company: {prospect_data.get('company_name', 'Not provided')}
Contact Name: {prospect_data.get('contact_name', 'Not provided')}
Email: {prospect_data.get('email', 'Not provided')}
Phone: {prospect_data.get('phone', 'Not provided')}
Industry: {prospect_data.get('industry', 'Not provided')}

PAIN POINTS:
{chr(10).join(['- ' + p for p in prospect_data.get('pain_points', ['Not specified'])])}

INTEREST LEVEL: {prospect_data.get('interest_level', 'High')}

CONVERSATION STAGE: Stage 3 - Ready for Demo

NEXT STEPS:
1. Contact prospect within 24 hours
2. Schedule personalized demo
3. Address specific yard management challenges
4. Discuss implementation and pricing

Generated by: Exotrac AI Chatbot
Timestamp: {datetime.now().isoformat()}
"""
        
        email_data = {
            'to_email': self.company_email,
            'from_email': self.company_email,
            'subject': subject,
            'body': body,
            'type': 'internal_demo_request'
        }
        
        return self.send_email(email_data)
    
    def get_sent_emails(self) -> list:
        """Get list of all sent emails"""
        return self.sent_emails
    
    def get_email_stats(self) -> Dict:
        """Get statistics about sent emails"""
        return {
            'total_sent': len(self.sent_emails),
            'by_type': self._count_by_type(),
            'by_status': self._count_by_status()
        }
    
    def _count_by_type(self) -> Dict:
        """Count emails by type"""
        counts = {}
        for email in self.sent_emails:
            email_type = email.get('type', 'unknown')
            counts[email_type] = counts.get(email_type, 0) + 1
        return counts
    
    def _count_by_status(self) -> Dict:
        """Count emails by status"""
        counts = {}
        for email in self.sent_emails:
            status = email.get('status', 'unknown')
            counts[status] = counts.get(status, 0) + 1
        return counts


# Example usage and testing
if __name__ == "__main__":
    print("Email Sender Module - Test")
    print("=" * 60)
    
    sender = EmailSender()
    
    # Test email
    test_email = {
        'to_email': 'prospect@example.com',
        'from_email': 'support@exotrac.com',
        'subject': 'Test Email - Exotrac Solutions',
        'body': 'This is a test email from Exotrac AI Chatbot.',
        'type': 'test'
    }
    
    result = sender.send_email(test_email)
    print(f"\nResult: {result['message']}")
    
    # Show stats
    stats = sender.get_email_stats()
    print(f"\nEmail Stats: {stats}")
