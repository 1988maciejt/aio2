from math import *
from random import *


class FloatUtils:
    
    @staticmethod
    def roundToResolution(Value : float, Resolution : float) -> float:
        result = round(Value / Resolution) * Resolution
        decimals = max(0, len(str(Resolution).split('.')[-1].rstrip('0')))
        return round(result, decimals)