from libs.aio import *
import random
import math
import libs.mersenne_twister as mt

mt.mt_seed(random.randint(0, 0xFFFFFFFF))

class SimulationEvent:
    
    __slots__ = ('Time', 'Payload')
    
    def __init__(self, Time, Payload):
        self.Time = Time
        self.Payload = Payload
        
    def __str__(self):
        return f"Event at {self.Time} with payload {self.Payload}"
    
    def __repr__(self):
        return f"SimulationEvent({repr(self.Time)}, {repr(self.Payload)})"
    
    def __eq__(self, other):
        return self.Time == other.Time
    
    def __ne__(self, other):
        return self.Time != other.Time
    
    def __lt__(self, other):
        return self.Time < other.Time
    
    def __gt__(self, other):
        return self.Time > other.Time
    
    def __le__(self, other):
        return self.Time <= other.Time
    
    def __ge__(self, other):
        return self.Time >= other.Time

    


class SimulationEventList:
    
    __slots__ = ("EventList", "_sorted")
    
    def __init__(self, Events : list = None):
        self._sorted = 0
        self.EventList = []
        if Events is not None:
            for Event in Events:
                if type(Event) is SimulationEvent:
                    self.add(Event)
        
    def __repr__(self):
        return f"SimulationEventList({repr(self.EventList)})"
    
    def __str__(self):
        Result = "SIMULATION EVENTS ["
        for Event in self.EventList:
            Result += f"\n  {Event}"
        Result += "\n]"
        return Result
    
    def __len__(self):
        return len(self.EventList)
        
    def add(self, Event : SimulationEvent):
        self.EventList.append(Event)
        self._sorted = 0

    def popEvent(self) -> SimulationEvent:
        if len(self.EventList) > 0:
            if not self._sorted:
                self.EventList.sort()
                self._sorted = 1
            return self.EventList.pop(0)
        return None
    
    def popEvents(self) -> tuple:
        if len(self.EventList) > 0:
            if not self._sorted:
                self.EventList.sort()
                self._sorted = 1
            Result = []
            E0 = self.EventList.pop(0)
            Result.append(E0)
            while len(self.EventList) > 0 and self.EventList[0].Time == E0.Time:
                Result.append(self.EventList.pop(0))
            return tuple(Result)
        return None
    
    def __bool__(self):
        return len(self.EventList) > 0
        
    def getNextEventTime(self):
        if len(self.EventList) > 0:
            return self.EventList[0].Time
        return None
        
        
class SimulationUtils:
    
    _Lock = 0
    
    @staticmethod
    def randTrialsBasingOnEventProbability(Pevent : float, UseMersenneTwister : bool = False) -> float:
        if UseMersenneTwister:
            while(SimulationUtils._Lock):
                pass
            SimulationUtils._Lock = 1
            try:
                Result = math.log(mt.extract_number() / 0xFFFFFFFF) / math.log(1 - Pevent)
            except:
                Result = math.log(mt.extract_number() / 0xFFFFFFFF) / math.log(1 - Pevent)
            SimulationUtils._Lock = 0
        else:
            try:
                Result = math.log(random.uniform(0, 1)) / math.log(1 - Pevent)
            except:
                Result = math.log(random.uniform(0, 1)) / math.log(1 - Pevent)
        return Result