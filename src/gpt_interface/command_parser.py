from typing import Dict, Any
import json

class CommandParser:
    VALID_ACTIONS = {
        'change_axis': ['axis', 'min', 'max', 'label'],
        'add_title': ['text', 'fontsize'],
        'filter_data': ['column', 'min_value', 'max_value'],
        'export': ['format', 'filename']
    }
    
    def parse_command(self, gpt_response: str) -> Dict[str, Any]:
        """Parse GPT response into actionable commands"""
        try:
            parsed = json.loads(gpt_response)
            action = parsed.get('action')
            
            if action not in self.VALID_ACTIONS:
                raise ValueError(f"Invalid action: {action}")
                
            return parsed
        except json.JSONDecodeError:
            raise ValueError("Invalid GPT response format")