from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

@dataclass
class GasParameters:
    min_concentration: float
    max_concentration: float
    rsd_threshold: float
    unit: str = "ppm"

@dataclass
class SubOceanMetadata:
    concentration_cal1: float
    concentration_cal2: float
    title: str
    start_time: datetime
    end_time: datetime
    hydrostatic_pressure_coef1: float
    hydrostatic_pressure_coef2: float
    latitude: float
    gas_type: bool
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SubOceanMetadata':
        return cls(
            concentration_cal1=float(data["Concentration coefficient calibration 1"]),
            concentration_cal2=float(data["Concentration coefficient calibration 2"]),
            title=data["Title of the experiment"],
            start_time=datetime.strptime(data["Start time"], "%Y-%m-%d %H:%M:%S"),
            end_time=datetime.strptime(data["End time"], "%Y-%m-%d %H:%M:%S"),
            hydrostatic_pressure_coef1=float(data["Hydrostatic Pressure coefficient 1"]),
            hydrostatic_pressure_coef2=float(data["Hydrostatic Pressure coefficient 2"]),
            latitude=float(data["Latitude"]),
            gas_type=bool(data["Type of gas"])
        )
    def to_dict(self) -> dict:
        """Convert metadata to NetCDF-compatible dict"""
        metadata_dict = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                metadata_dict[key] = value.isoformat()
            elif isinstance(value, bool):
                metadata_dict[key] = int(value)  # Convert bool to int (0/1)
            elif isinstance(value, str):
                metadata_dict[key] = str(value)  # Ensure string type
            elif isinstance(value, (int, float)):
                metadata_dict[key] = value  # Numeric types are compatible
            else:
                metadata_dict[key] = str(value)  # Convert other types to string
        return metadata_dict