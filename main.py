"""
Abstract Self-driving Lab (SDL) API
This is an example of an SDL API - a collection of multiple hardware
docstring [optional]:   if given, docstring will be attached to the prompt when using LLM
_helper_function:       function names start with "_" will not be displayed
types and default:      Types (str, float, bool) and default values are recommended
"""

import logging
import os
import sys
import time
from abc import ABC
import random

import sys
import os


from src.labview_server import LabVIEWServerDevice


class AbstractSDL(ABC):
    def __init__(self, pvd: LabVIEWServerDevice):
        self.chamber = pvd
        self.logger = logging.getLogger(f"logger_name")

    # @prefect.task
    def control_power_and_rate(self, power:float, flow:float) -> bool:
        param_dict = {
            "Power": power,
            "Flow": flow
        }
        chamber.send_json_to_labview(param_dict)
        self.logger.info("Deposition parameters set")
        return None


    # @prefect.task
    def simulate_error(self):
        raise ValueError("some error")

    def _send_command(self):
        """helper function"""
        pass

chamber = LabVIEWServerDevice()
sdl = AbstractSDL(chamber)

if __name__ == "__main__":
    
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
    import ivoryos
    ivoryos.run(__name__)