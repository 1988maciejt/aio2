import os
if "rpi" in os.uname().nodename:

  from libs.aio import *
  import RPi.GPIO as rgpio

  rgpio.setwarnings(False)
  rgpio.setmode(rgpio.BCM)


  class rpiPin:
    
    __slots__ = ("_pin", "_val")
    
    def __init__(self, PinIndex : int, Output = False, Value = 0, PullUp = False, PullDown = False) -> None:
      self._pin = abs(int(PinIndex))
      self._val = 0
      if Output:
        self.setOutput()
        self.set(Value)
      else:
        self.setInput(PullUp, PullDown)
      
    def setOutput(self):
      rgpio.setup(self._pin, rgpio.OUT)
      
    def setInput(self, PullUp = False, PullDown = False):
      if PullDown:
        rgpio.setup(self._pin, rgpio.IN, pull_up_down=rgpio.PUD_DOWN)
      elif PullUp:
        rgpio.setup(self._pin, rgpio.IN, pull_up_down=rgpio.PUD_UP)
      else:
        rgpio.setup(self._pin, rgpio.IN, pull_up_down=rgpio.PUD_OFF)
      
    def set(self, Value = 1):
      if Value:
        rgpio.output(self._pin, 1)
        self._val = 1
      else:
        rgpio.output(self._pin, 0)
        self._val = 0
        
    def reset(self):
      rgpio.output(self._pin, 0)
      self._val = 0
      
    def toggle(self):
      self._val = 1 - self._val
      rgpio.output(self._pin, self._val)

    def read(self) -> int:
      return 1 if rgpio.input(self._pin) else 0
      
      
  def RpiCleanup():
    rgpio.cleanup()
    
  def rpiAvailable():
    return True
  
else:
  
  def rpiAvailable():
    return False