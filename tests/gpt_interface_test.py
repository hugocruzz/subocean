import pytest
from unittest.mock import patch, MagicMock
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'src')
sys.path.append(src_dir)

from gpt_interface.prompt_handler import PromptHandler
from gpt_interface.command_parser import CommandParser
from gpt_interface.response_formatter import ResponseFormatter

def test_command_parser():
    parser = CommandParser()
    test_response = '{"action": "change_axis", "parameters": {"axis": "y", "min": 0, "max": 100}}'
    result = parser.parse_command(test_response)
    assert result['action'] == 'change_axis'
    assert result['parameters']['axis'] == 'y'

@patch('openai.ChatCompletion.create')
def test_prompt_handler(mock_openai):
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"action": "change_axis", "parameters": {}}'
    mock_openai.return_value = mock_response
    
    handler = PromptHandler()
    result = handler.process_plot_command("change y axis from 0 to 100")
    assert isinstance(result, str)
