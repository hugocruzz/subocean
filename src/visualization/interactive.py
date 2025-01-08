import matplotlib.pyplot as plt
from matplotlib.widgets import Button, TextBox, Slider
import pandas as pd
from typing import Optional, Dict, List, Tuple, Callable
from .plot_manager import PlotManager
from matplotlib.widgets import Button, TextBox
import matplotlib.pyplot as plt
from typing import List, Dict, Optional
import pandas as pd
class InteractivePlot:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.original_df = df.copy()
        self.axis_labels = {'x': None, 'y': None}
        self.axis_states = {'x': False, 'y': False}
        self.command_history = []
        self.current_state = 0
        
    def _save_state(self):
        """Save current plot state"""
        return {
            'xlim': self.ax.get_xlim(),
            'ylim': self.ax.get_ylim(),
            'title': self.ax.get_title(),
            'xlabel': self.ax.get_xlabel(),
            'ylabel': self.ax.get_ylabel(),
            'axis_inverted': {
                'x': self.ax.xaxis_inverted(),
                'y': self.ax.yaxis_inverted()
            }
        }
        
    def _restore_state(self, state):
        """Restore plot state"""
        self.ax.set_xlim(state['xlim'])
        self.ax.set_ylim(state['ylim'])
        self.ax.set_title(state['title'])
        self.ax.set_xlabel(state['xlabel'])
        self.ax.set_ylabel(state['ylabel'])
        
        # Restore axis inversions
        if state['axis_inverted']['x'] != self.ax.xaxis_inverted():
            self.ax.invert_xaxis()
        if state['axis_inverted']['y'] != self.ax.yaxis_inverted():
            self.ax.invert_yaxis()
            
    def _execute_command(self, parsed_response: Dict):
        """Execute parsed command on plot"""
        action = parsed_response['action']
        params = parsed_response.get('parameters', {})
        
        if action == 'add_title':
            self.ax.set_title(params['text'])
        elif action == 'change_axis':
            if params['axis'] == 'y':
                self.ax.set_ylim(float(params['min']), float(params['max']))
            else:
                self.ax.set_xlim(float(params['min']), float(params['max']))
        elif action == 'invert_axis':
            if params['axis'] == 'y':
                self.ax.invert_yaxis()
            else:
                self.ax.invert_xaxis()
        elif action == 'reset_view':
            self.ax.autoscale()
        
        # Refresh plot
        self.fig.canvas.draw_idle()

    def _on_enter(self, event):
        command = self.command_box.text
        if command:
            try:
                code = self.prompt_handler.generate_plot_code(command)
                error = self.prompt_handler.executor.run(code)
                
                if error:
                    print(f"Error: {error}")
                else:
                    print(f"Executed:\n{code}")
                    self.command_history.append({
                        'command': command,
                        'code': code,
                        'state': self._save_state()
                    })
                    
            except Exception as e:
                print(f"Error: {str(e)}")
                
            self.command_box.set_val('')
            
    def _on_undo(self, event):
        if self.command_history and self.current_state > 0:
            self.current_state -= 1
            if self.current_state > 0:
                previous_state = self.command_history[self.current_state-1]
                self._restore_state(previous_state['state'])
                print(f"Undid: {previous_state['command']}")
            else:
                # Restore to initial state
                self._restore_state(self._save_state())
                print("Restored to initial state")
            self.fig.canvas.draw_idle()

    def create_interactive_profile(self, y_column: str = 'Depth (meter)',
                                 x_columns: List[str] = None,
                                 title: str = None):
        # Create figure with space for controls
        self.fig = plt.figure(figsize=(15, 8))
        
        # Main plot area
        self.ax = self.fig.add_axes([0.1, 0.1, 0.6, 0.8])
        
        # Command input area
        command_ax = self.fig.add_axes([0.75, 0.4, 0.2, 0.05])
        self.command_box = TextBox(command_ax, 'Command:', initial='')
        
        # Enter button
        enter_ax = self.fig.add_axes([0.75, 0.3, 0.09, 0.05])
        self.enter_button = Button(enter_ax, 'Enter')
        self.enter_button.on_clicked(self._on_enter)
        
        # Undo button
        undo_ax = self.fig.add_axes([0.86, 0.3, 0.09, 0.05])
        self.undo_button = Button(undo_ax, 'Undo')
        self.undo_button.on_clicked(self._on_undo)
        
        # Plot data
        for col in x_columns:
            self.ax.plot(self.df[col], self.df[y_column], label=col)
            
        self.ax.set_ylabel(y_column)
        self.ax.set_xlabel(x_columns[0] if x_columns else '')
        self.axis_labels = {
            'x': x_columns[0] if x_columns else '',
            'y': y_column
        }
        
        if title:
            self.ax.set_title(title)
        self.ax.legend()
        return self.fig

    def get_axis_by_label(self, label: str) -> str:
        """Return 'x' or 'y' based on which axis contains the label"""
        label = label.lower()
        for axis, axis_label in self.axis_labels.items():
            if axis_label and label in axis_label.lower():
                return axis
        return None
    
    def set_axis_label(self, axis: str, label: str) -> None:
        """Set label for specified axis"""
        self.axis_labels[axis] = label
        if axis == 'x':
            self.ax.set_xlabel(label)
        else:
            self.ax.set_ylabel(label)
        self.fig.canvas.draw_idle()

    def invert_axis(self, axis: str) -> None:
        """Invert specified axis"""
        if axis == 'x':
            self.ax.invert_xaxis()
            self.axis_states['x'] = not self.axis_states['x']
        elif axis == 'y':
            self.ax.invert_yaxis()
            self.axis_states['y'] = not self.axis_states['y']
            
    def reset_parameter(self, parameter: str) -> None:
        """Reset parameter to original state"""
        if parameter == 'all':
            self.df = self.original_df.copy()
            self.parameter_states.clear()
        elif parameter in self.parameter_states:
            self.df[parameter] = self.original_df[parameter]
            del self.parameter_states[parameter]
        

    def add_filter_callback(self, column: str, callback: Callable):
        """Add callback for filtering data"""
        self.callbacks[column] = callback
        
    def _reset_view(self, event):
        """Reset plot to original view"""
        if self.ax:
            self.ax.relim()
            self.ax.autoscale_view()
            self.fig.canvas.draw_idle()
            
    def _update_depth_range(self, val):
        """Update depth range based on slider"""
        if self.ax:
            ymin, ymax = self.ax.get_ylim()
            self.ax.set_ylim(ymin, ymin + val)
            self.fig.canvas.draw_idle()
            
    def _on_pick(self, event):
        """Handle pick events on plot"""
        if event.artist:
            ind = event.ind[0]
            print(f"Selected point: {self.df.iloc[ind]}")