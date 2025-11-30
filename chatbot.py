import openai
import os
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional


class ExotracChatbot:

    def __init__(self, local: bool = False):
        """Initialize the Exotrac AI Chatbot"""
        # local mode (no OpenAI calls) useful for development/testing
        self.local = local
        # Load OpenAI API key
        self.api_key = os.environ.get('OPENAI_API_KEY', '')
        if not self.api_key and not self.local:
            raise ValueError(
                "OpenAI API key not found. Please add OPENAI_API_KEY as a secret or run in local mode."
            )

        if self.api_key:
            openai.api_key = self.api_key
        else:
            # Ensure openai.api_key exists even if empty (safe default)
            openai.api_key = None

        # Load training dataset
        with open('training_dataset.json', 'r') as f:
            self.training_data = json.load(f)

        # Initialize conversation state
        self.conversation_history = []
        self.current_stage = 1
        self.prospect_info = {
            'company_name': None,
            'contact_name': None,
            'email': None,
            'phone': None,
            'industry': None,
            'pain_points': [],
            'interest_level': 'unknown'
        }

        # Build system prompt
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """Build comprehensive system prompt for the AI"""
        company_info = self.training_data['company_info']
        services = self.training_data['core_services']
        guidelines = self.training_data['conversation_guidelines']

        services_text = "\n".join(
            [f"- {s['name']}: {s['description']}" for s in services])

        benefits_text = "\n".join([
            f"- {benefit}"
            for benefit in self.training_data['key_value_propositions']
        ])

        prompt = f"""You are an AI sales assistant for {company_info['name']}, a leading Yard Management System provider.

COMPANY INFORMATION:
- Company: {company_info['name']}
- Website: {company_info['website']}
- Email: {company_info['email']}
- Phone: {company_info['phone']}
- Industry: {company_info['industry']}

YOUR COMMUNICATION STYLE:
- Tone: {company_info['tone']}
- Be {', '.join(guidelines['style'].split(', '))}
- {', '.join(guidelines['approach'])}

CORE SERVICES YOU REPRESENT:
{services_text}

KEY VALUE PROPOSITIONS:
{benefits_text}

YOUR PRIMARY GOALS:
1. Engage with yard management companies professionally
2. Understand their pain points and challenges
3. Present Exotrac solutions that address their specific needs
4. Guide interested prospects through a 3-stage process:
   - Stage 1: Initial introduction and interest assessment
   - Stage 2: Detailed services presentation
   - Stage 3: Demo scheduling and handoff to main team

CONVERSATION FLOW:
- Start by introducing yourself and Exotrac
- Ask qualifying questions to understand their needs
- Listen actively and address their specific concerns
- When they show interest, offer to send detailed information
- When they want to proceed, initiate demo scheduling
- Always maintain a professional, consultative approach

IMPORTANT RULES:
- Never be pushy or aggressive
- Focus on value and ROI
- Use specific metrics (30-40% cost reduction)
- Address objections with empathy and data
- Collect prospect information naturally during conversation
- When prospect agrees to demo, prepare to send their info to support@exotrac.com

Remember: You're here to help solve their yard management challenges, not just make a sale.
"""
        return prompt

    def chat(self, user_message: str) -> Dict:
        """Process user message and return AI response with metadata"""
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Analyze message for prospect information
        self._extract_prospect_info(user_message)

        # Build messages for OpenAI
        messages: List[Dict[str, str]] = [{
            "role": "system",
            "content": self.system_prompt
        }] + self.conversation_history

        # Get AI response
        try:
            if self.local:
                # Local/mock mode - produce a richer canned response based on intent
                ai_message = self._local_response(user_message)

                # Add AI response to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": ai_message
                })

                # Analyze response for stage progression (analysis primarily uses user message)
                stage_info = self._analyze_conversation_stage(user_message, ai_message)

                stage_for_response = self.current_stage
                if stage_info.get('advance_to_stage'):
                    self.current_stage = stage_info['advance_to_stage']

                return {
                    'response': ai_message,
                    'current_stage': stage_for_response,
                    'next_stage': self.current_stage,
                    'should_send_email': stage_info['should_send_email'],
                    'email_type': stage_info['email_type'],
                    'prospect_info': self.prospect_info,
                    'timestamp': datetime.now().isoformat()
                }

            # Production mode - call OpenAI
            response = openai.chat.completions.create(model="gpt-4",
                                                      messages=messages,
                                                      temperature=0.7,
                                                      max_tokens=1000)

            ai_message = response.choices[0].message.content or "I apologize, I couldn't generate a response."

            # Add AI response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": ai_message
            })

            # Analyze response for stage progression
            stage_info = self._analyze_conversation_stage(user_message, ai_message)

            # Save current stage before advancement (for response metadata)
            stage_for_response = self.current_stage

            # Advance stage after determining email type
            if stage_info.get('advance_to_stage'):
                self.current_stage = stage_info['advance_to_stage']

            return {
                'response': ai_message,
                'current_stage': stage_for_response,
                'next_stage': self.current_stage,
                'should_send_email': stage_info['should_send_email'],
                'email_type': stage_info['email_type'],
                'prospect_info': self.prospect_info,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'response': f"I apologize, but I encountered an error: {str(e)}",
                'current_stage': self.current_stage,
                'should_send_email': False,
                'email_type': None,
                'prospect_info': self.prospect_info,
                'timestamp': datetime.now().isoformat()
            }

    def _extract_prospect_info(self, message: str):
        """Extract prospect information from conversation"""
        message_lower = message.lower()

        # Simple pattern matching for contact info
        # In production, this would use more sophisticated NLP
        if '@' in message:
            # Extract email
            words = message.split()
            for word in words:
                if '@' in word:
                    self.prospect_info['email'] = word.strip('.,;:')
                    break

        # Look for company mentions
        if 'company' in message_lower or 'we are' in message_lower:
            # This is simplified - in production use NER
            self.prospect_info['company_name'] = "Extracted from conversation"

    def _analyze_conversation_stage(self, user_message: str,
                                    ai_response: str) -> Dict:
        """Analyze conversation to determine if email should be sent"""
        user_lower = user_message.lower()
        ai_lower = ai_response.lower()

        # Stage 3: Demo scheduling (only when current_stage == 3)
        demo_keywords = [
            'demo', 'schedule', 'meeting', 'call', 'lets proceed',
            'move forward', 'agree'
        ]
        if self.current_stage == 3 and any(keyword in user_lower
                                           for keyword in demo_keywords):
            return {
                'should_send_email': True,
                'email_type': 'stage_3_demo_scheduling',
                'advance_to_stage': 3
            }

        # Stage 2: Detailed information request (only when current_stage == 2)
        detail_keywords = [
            'services', 'features', 'how does it work', 'pricing',
            'more details', 'tell me more'
        ]
        if self.current_stage == 2 and any(keyword in user_lower
                                           for keyword in detail_keywords):
            return {
                'should_send_email': True,
                'email_type': 'stage_2_detailed_services',
                'advance_to_stage': 3
            }

        # Stage 1: Initial interest (only when current_stage == 1)
        interest_keywords = [
            'interested', 'yes', 'sounds good', 'more information', 'hello',
            'hi'
        ]
        if self.current_stage == 1 and any(keyword in user_lower
                                           for keyword in interest_keywords):
            return {
                'should_send_email': True,
                'email_type': 'stage_1_initial_outreach',
                'advance_to_stage': 2
            }

        return {
            'should_send_email': False,
            'email_type': None,
            'advance_to_stage': None
        }

    def generate_email(self, email_type: str) -> Dict:
        """Generate email based on type and prospect information"""
        template_data = self.training_data['email_templates'].get(email_type)

        if not template_data:
            return {
                'subject': 'Exotrac Yard Management Solutions',
                'body': f'Email template not found for {email_type}',
                'to_email': self.prospect_info.get('email'),
                'from_email': self.training_data['company_info']['email'],
                'type': email_type
            }

        # Personalize email with prospect info
        subject = template_data['subject']
        body = template_data['template']

        # Replace placeholders
        company_name = self.prospect_info.get(
            'company_name') or '[Company Name]'
        body = body.replace('[Company Name]', company_name)
        body = body.replace('[AI Assistant Name]', 'Exotrac AI Assistant')
        body = body.replace('[AI Assistant]', 'Exotrac AI Assistant')

        return {
            'subject': subject,
            'body': body,
            'to_email': self.prospect_info.get('email'),
            'from_email': self.training_data['company_info']['email'],
            'type': email_type
        }

    def _local_response(self, message: str) -> str:
        """Return a canned, richer response when running in local mode.

        Uses simple keyword matching to return a helpful reply that mirrors
        what the production AI might say (short form) and references
        the email templates where appropriate.
        """
        msg = message.lower()

        # Demo scheduling intent
        if any(k in msg for k in ['demo', 'schedule', 'meeting', 'demo?','let\'s demo','move forward']):
            tpl = self.training_data['email_templates'].get('stage_3_demo_scheduling')
            return (
                "Thanks — it sounds like you'd like to schedule a demo. "
                "I'll prepare the next steps and connect you with our team.\n\n" 
                f"(preview subject: {tpl['subject']})"
            )

        # Detailed services request
        if any(k in msg for k in ['services', 'features', 'how does it work', 'pricing', 'more details', 'tell me more', 'details']):
            tpl = self.training_data['email_templates'].get('stage_2_detailed_services')
            return (
                "Great — I can share detailed information about our services. "
                "Please see the summary below and I can send the full overview via email.\n\n"
                f"(preview subject: {tpl['subject']})"
            )

        # Initial interest / greeting
        if any(k in msg for k in ['interested', 'yes', 'sounds good', 'more information', 'hello', 'hi', 'hey']):
            tpl = self.training_data['email_templates'].get('stage_1_initial_outreach')
            return (
                "Thanks for your interest — happy to help. "
                "I can send an overview email that highlights how Exotrac reduces costs and increases visibility.\n\n"
                f"(preview subject: {tpl['subject']})"
            )

        # Fallback reply
        return (
            "Thanks for reaching out. Could you tell me a bit more about your yard "
            "operations (e.g., trailer count, main pain points, or whether you'd like a demo)?"
        )

    def get_conversation_summary(self) -> Dict:
        """Get summary of current conversation"""
        return {
            'stage': self.current_stage,
            'prospect_info': self.prospect_info,
            'message_count': len(self.conversation_history),
            'last_updated': datetime.now().isoformat()
        }

    def save_conversation(self, filename: Optional[str] = None):
        """Save conversation to file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'conversation_{timestamp}.json'

        data = {
            'conversation_history': self.conversation_history,
            'prospect_info': self.prospect_info,
            'current_stage': self.current_stage,
            'timestamp': datetime.now().isoformat()
        }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

        return filename

    def reset_conversation(self):
        """Reset conversation state"""
        self.conversation_history = []
        self.current_stage = 1
        self.prospect_info = {
            'company_name': None,
            'contact_name': None,
            'email': None,
            'phone': None,
            'industry': None,
            'pain_points': [],
            'interest_level': 'unknown'
        }


def main():
    """Main function for testing the chatbot"""
    print("=" * 60)
    print("EXOTRAC AI CHATBOT - Email Outreach System")
    print("=" * 60)
    print("\nInitializing chatbot...")

    try:
        bot = ExotracChatbot()
        print("✓ Chatbot initialized successfully")
        print(
            f"✓ Loaded {len(bot.training_data['core_services'])} core services"
        )
        print(
            f"✓ Loaded {len(bot.training_data['email_templates'])} email templates"
        )
        print("\n" + "=" * 60)
        print(
            "CHATBOT READY - Type 'quit' to exit, 'save' to save conversation")
        print("=" * 60 + "\n")

        while True:
            user_input = input("You: ").strip()

            if user_input.lower() == 'quit':
                print("\nThank you for using Exotrac AI Chatbot!")
                break

            if user_input.lower() == 'save':
                filename = bot.save_conversation()
                print(f"\n✓ Conversation saved to {filename}\n")
                continue

            if not user_input:
                continue

            # Get chatbot response
            result = bot.chat(user_input)

            print(f"\nExotrac AI: {result['response']}\n")

            # Check if email should be sent
            if result['should_send_email']:
                print(
                    f"[SYSTEM] Stage {result['current_stage']} - Email type: {result['email_type']}"
                )
                email = bot.generate_email(result['email_type'])
                if email:
                    print(f"[EMAIL READY] Subject: {email['subject']}")
                    print(
                        f"[EMAIL READY] To: {email['to_email'] or 'Prospect email needed'}"
                    )
                    print()

    except KeyboardInterrupt:
        print("\n\nChatbot interrupted. Goodbye!")
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
