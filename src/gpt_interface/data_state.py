class DataState:
    def __init__(self, df):
        self.original_df = df.copy()
        self.current_df = df.copy()
        self.operations = []
        self.operation_registry = {
            'filter': self._apply_filter,
            'rsd': self._calculate_rsd,
            'moving_average': self._apply_moving_average,
            'gradient': self._calculate_gradient
        }
        
    def add_operation(self, operation_type: str, params: dict):
        """Add operation to history"""
        self.operations.append({
            'type': operation_type,
            'params': params
        })
        
    def get_current_state(self) -> str:
        """Get description of current data state"""
        return "\n".join([
            f"- {op['type']}: {op['params']}" 
            for op in self.operations
        ])