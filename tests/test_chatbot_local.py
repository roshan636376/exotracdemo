import os
import json
import tempfile
import pytest
from exotracdemo.chatbot import ExotracChatbot

def test_local_init_and_load_dataset():
    bot = ExotracChatbot(local=True)
    assert hasattr(bot, 'training_data')
    assert 'core_services' in bot.training_data
    assert 'email_templates' in bot.training_data

def test_local_chat_initial_interest_and_email_generation(tmp_path):
    bot = ExotracChatbot(local=True)

    # Send a greeting that should trigger stage 1 interest
    result = bot.chat('Hi, we are interested')
    assert 'response' in result
    assert result['should_send_email'] is True
    assert result['email_type'] == 'stage_1_initial_outreach'

    # Generate the email and verify subject and placeholders replaced
    email = bot.generate_email(result['email_type'])
    assert 'subject' in email
    assert 'Optimize Your Yard Operations' in email['subject']
    assert email['from_email'] == bot.training_data['company_info']['email']

def test_generate_email_personalization_and_save(tmp_path):
    bot = ExotracChatbot(local=True)
    bot.prospect_info['company_name'] = 'Acme Logistics'
    bot.prospect_info['email'] = 'contact@acme.example'

    email = bot.generate_email('stage_1_initial_outreach')
    assert 'Acme Logistics' in email['body'] or '[Company Name]' not in email['body']
    assert email['to_email'] == 'contact@acme.example'

    # Test saving conversation creates a file
    filename = bot.save_conversation(str(tmp_path / 'conv_test.json'))
    assert os.path.exists(filename)
    with open(filename, 'r') as f:
        data = json.load(f)
        assert 'conversation_history' in data
        assert 'prospect_info' in data


if __name__ == '__main__':
    pytest.main()