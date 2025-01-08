from pathlib import Path
import openai
from dotenv import load_dotenv
import os
from typing import Dict, List, Optional
import json
from core.executor import Executor

class PromptHandler:
    def __init__(self, df=None):
        load_dotenv()
        self.client = openai.OpenAI()  # Initialize client once
        self.df = df
        self.current_code = None
        self.executor = Executor()

    def _clean_gpt_response(self, response: str) -> str:
        """Extract clean Python code from GPT response"""
        # If response doesn't contain markdown, return as is
        if '```' not in response:
            return response.strip()
            
        code_lines = []
        in_code_block = False
        
        for line in response.split('\n'):
            if '```python' in line:
                in_code_block = True
                continue
            elif '```' in line:
                in_code_block = False
                continue
            elif in_code_block and not line.startswith('#'):
                code_lines.append(line)
                
        return '\n'.join(code_lines).strip()
    
    def generate_plot_code(self, command: str) -> str:
        # Create system prompt with DataFrame info
        system_prompt = f"""You are a matplotlib code generator.
        Generate ONLY executable Python code. No explanations.
        Use 'df' as the DataFrame variable name.
        
        Available DataFrame columns:
        {list(self.df.columns)}
        """
        
        if self.current_code is None:
            user_prompt = f"Create initial plot: {command}"
        else:
            user_prompt = f"""
            Current code:
            {self.current_code}
            
            Modify with command: {command}
            """
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        
        raw_code = response.choices[0].message.content
        self.current_code = self._clean_gpt_response(raw_code)

        return self.current_code