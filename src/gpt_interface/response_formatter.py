from typing import Dict, Any

class ResponseFormatter:
    def format_plot_action(self, action_dict: Dict[str, Any]) -> str:
        """Format plot action response"""
        action = action_dict.get('action')
        params = action_dict.get('parameters', {})
        
        responses = {
            'change_axis': self._format_axis_change,
            'add_title': self._format_title_change,
            'filter_data': self._format_filter,
            'export': self._format_export
        }
        
        formatter = responses.get(action)
        return formatter(params) if formatter else "Unknown action"
    
    def _format_axis_change(self, params: Dict) -> str:
        return f"Changed {params['axis']} axis: range [{params['min']}, {params['max']}]"
    
    def _format_title_change(self, params: Dict) -> str:
        return f"Updated title to: {params['text']}"