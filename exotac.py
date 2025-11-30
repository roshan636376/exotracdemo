#!/usr/bin/env python3
"""
Exotrac AI Chatbot - Main Entry Point
Email outreach system for yard management companies
"""

import os
import sys
from chatbot import ExotracChatbot
from email_sender import EmailSender

def print_banner():
    """Print application banner"""
    print("\n" + "=" * 70)
    print(" " * 15 + "EXOTRAC AI CHATBOT")
    print(" " * 10 + "Automated Email Outreach System")
    print(" " * 15 + "for Yard Management Companies")
    print("=" * 70)

def print_help():
    """Print help information"""
    print("\nAVAILABLE COMMANDS:")
    print("  Type your message - Chat with the AI")
    print("  'save'  - Save current conversation")
    print("  'stats' - View email statistics")
    print("  'help'  - Show this help message")
    print("  'quit'  - Exit the chatbot")
    print()

def main():
    """Main application entry point"""
    print_banner()
    
    # Check for OpenAI API key
    api_key = os.environ.get('OPENAI_API_KEY', '')
    if not api_key:
        print("\n❌ ERROR: OpenAI API key not found!")
        print("\nTo use this chatbot, you need to add your OpenAI API key:")
        print("1. Go to https://platform.openai.com/api-keys")
        print("2. Create a new API key")
        print("3. Add it as an environment variable named 'OPENAI_API_KEY'")
        print("\nExiting...")
        sys.exit(1)
    
    print("\n🔄 Initializing chatbot...")
    
    try:
        # Initialize chatbot and email sender
        bot = ExotracChatbot()
        email_sender = EmailSender()
        
        print("✅ Chatbot initialized successfully")
        print(f"✅ Loaded {len(bot.training_data['core_services'])} core services")
        print(f"✅ Loaded {len(bot.training_data['email_templates'])} email templates")
        print("\n" + "=" * 70)
        print("READY TO START EMAIL OUTREACH CONVERSATIONS")
        print("=" * 70)
        print("\nThe AI will help you approach yard companies with Exotrac solutions.")
        print("It will automatically generate emails based on prospect interest levels.")
        print_help()
        
        # Main conversation loop
        while True:
            try:
                user_input = input("\n👤 You: ").strip()
                
                # Handle commands
                if user_input.lower() == 'quit':
                    print("\n👋 Thank you for using Exotrac AI Chatbot!")
                    print("Goodbye!\n")
                    break
                
                if user_input.lower() == 'help':
                    print_help()
                    continue
                
                if user_input.lower() == 'save':
                    filename = bot.save_conversation()
                    print(f"\n✅ Conversation saved to: {filename}\n")
                    continue
                
                if user_input.lower() == 'stats':
                    stats = email_sender.get_email_stats()
                    print(f"\n📊 EMAIL STATISTICS:")
                    print(f"   Total Emails: {stats['total_sent']}")
                    print(f"   By Type: {stats['by_type']}")
                    print(f"   By Status: {stats['by_status']}\n")
                    continue
                
                if not user_input:
                    continue
                
                # Get chatbot response
                print("\n🤖 Exotrac AI: ", end="", flush=True)
                result = bot.chat(user_input)
                print(result['response'])
                
                # Check if email should be sent
                if result['should_send_email'] and result['email_type']:
                    print(f"\n📧 [SYSTEM] Preparing email: {result['email_type']}")
                    print(f"   Current Stage: {result['current_stage']}/3")
                    if result.get('next_stage') and result['next_stage'] != result['current_stage']:
                        print(f"   → Advancing to Stage: {result['next_stage']}/3")
                    
                    # Generate email
                    email = bot.generate_email(result['email_type'])
                    if email:
                        # Display email preview
                        print(f"\n┌─ EMAIL PREVIEW " + "─" * 50)
                        print(f"│ Subject: {email['subject']}")
                        print(f"│ To: {email['to_email'] or 'Prospect email needed'}")
                        print(f"│ From: {email['from_email']}")
                        print(f"│ Type: {email['type']}")
                        print(f"└─" + "─" * 66)
                        
                        # Send email (simulated)
                        send_result = email_sender.send_email(email)
                        if send_result['success']:
                            print(f"✅ {send_result['message']}")
                            if 'filename' in send_result:
                                print(f"   📄 File: {send_result['filename']}")
                        else:
                            print(f"❌ {send_result['message']}")
                        
                        # If stage 3, also send to main company
                        if result['current_stage'] == 3:
                            print(f"\n📨 Sending prospect info to main company...")
                            company_result = email_sender.send_to_main_company(result['prospect_info'])
                            if company_result['success']:
                                print(f"✅ {company_result['message']}")
                                if 'filename' in company_result:
                                    print(f"   📄 File: {company_result['filename']}")
                
                # Show conversation summary periodically
                if len(bot.conversation_history) % 10 == 0 and len(bot.conversation_history) > 0:
                    summary = bot.get_conversation_summary()
                    print(f"\n📊 Conversation: {summary['message_count']//2} exchanges | Stage: {summary['stage']}/3")
            
            except KeyboardInterrupt:
                print("\n\n⚠️ Interrupted. Type 'quit' to exit or continue chatting.")
                continue
    
    except Exception as e:
        print(f"\n❌ Error initializing chatbot: {str(e)}")
        print("\nPlease check:")
        print("1. OpenAI API key is set correctly")
        print("2. training_dataset.json exists (or defaults are used)")
        print("3. All required files are present")
        sys.exit(1)

if __name__ == "__main__":
    main()
