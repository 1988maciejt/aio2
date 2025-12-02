from math import *
from random import *


class FloatUtils:
    
    @staticmethod
    def roundToDecimalPlacesAsInAnotherFloat(Value : float, ReferenceFloat : float) -> float:
        decimals = max(0, len(str(ReferenceFloat).split('.')[-1].rstrip('0')))
        return round(Value, decimals)
    
    @staticmethod
    def roundToResolution(Value : float, Resolution : float) -> float:
        if Resolution == 0:
            return Value
        result = round(Value / Resolution) * Resolution
        decimals = max(0, len(str(Resolution).split('.')[-1].rstrip('0')))
        return round(result, decimals)