from libs.flags import *
from libs.interactive_menu import *
from libs.temp_transcript import *
import _thread
from time import sleep
from libs.generators import *
from libs.aio import Aio

KEY_BINDING_FLAGS = Flags()
# 0:  main flag; reset it to stop keybinding thread
# 1:  TempTranscript menu
# 2:  Menu
# 3:  Pause

_STARTED = None
_EVENT = None

def setEvent(event):
  global _EVENT
  _EVENT = event

def _KeyBindingThread():
  global KEY_BINDING_FLAGS, _EVENT
  #print("Thread started")
  while(KEY_BINDING_FLAGS.test(0)):
    if KEY_BINDING_FLAGS.test(1):
      if not Aio.isTranscriptMode():
        if _EVENT is not None:
          _EVENT.cli.current_buffer.reset()
          _EVENT.cli.current_buffer.insert_text("TempTranscript.menu()")
          _EVENT.current_buffer.validate_and_handle()
          _EVENT = None
      KEY_BINDING_FLAGS.reset(1)
    elif KEY_BINDING_FLAGS.test(2):
      if not Aio.isTranscriptMode():
        if _EVENT is not None:
          _EVENT.cli.current_buffer.reset()
          _EVENT.cli.current_buffer.insert_text("menu()")
          _EVENT.current_buffer.validate_and_handle()
          _EVENT = None
      KEY_BINDING_FLAGS.reset(2)
    elif KEY_BINDING_FLAGS.test(3):
      if generatorsPaused():
        print("RESUMED")
        pauseGenerators(0)
        if _EVENT is not None:
          _EVENT.current_buffer.validate_and_handle()
      else:
        print()
        print("PAUSED    (Press [Ctrl+P] to resume...)")
        pauseGenerators(1)
        _EVENT = None
      KEY_BINDING_FLAGS.reset(3)
    time.sleep(0.35)
  
def startKeyBindingThread():
  global _STARTED, KEY_BINDING_FLAGS
  if _STARTED is None:
    KEY_BINDING_FLAGS.set(0)
    _thread.start_new_thread(_KeyBindingThread, ())
    _STARTED = True