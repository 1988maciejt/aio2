import _thread
from time import sleep
from libs.aio import *

class SimpleThreadingTask:
  __slots__ = ("_done", "_result")
  def __init__(self):
    self._done = False
    self._result = None
  def __bool__(self):
    return self._done
  def getResult(self):
    return self._result
  def isDone(self):
    return self._done
  
def _simple_thread(MyTask : SimpleThreadingTask, Function, args, kwargs):
  while SimpleThread._parallel_jobs >= SimpleThread.MaxParallelJobs:
    sleep(0.001)
  SimpleThread._parallel_jobs += 1
  try:
    MyTask._result = Function(*args, **kwargs)
  except Exception as inst:
    Aio.printError(f"SimpleThread: {inst}")
  SimpleThread._parallel_jobs -= 1
  MyTask._done = True


class SimpleThread:
  
  MaxParallelJobs = 32
  _parallel_jobs = 0
  
  @staticmethod  
  def single(Function, *args, **kwargs):
    Task = SimpleThreadingTask()
    _thread.start_new_thread(_simple_thread, tuple([Task, Function, args, kwargs]))
    return Task

  @staticmethod
  def uimap(Function, Iterable):
    Tasks = []
    for I in Iterable:
      if SimpleThread._parallel_jobs < SimpleThread.MaxParallelJobs:
        Tasks.append(SimpleThread.single(Function, I))
      elif len(Tasks) > 0:
        for T in Tasks:
          if T:
            Tasks.remove(T)
            yield T.getResult()
            break
        sleep(0.001)
    while len(Tasks) > 0:
      for T in Tasks:
        if T:
          Tasks.remove(T)
          yield T.getResult()
          break
      sleep(0.001)
      
  @staticmethod
  def imap(Function, Iterable):
    Tasks = []
    for I in Iterable:
      if SimpleThread._parallel_jobs < SimpleThread.MaxParallelJobs:
        Tasks.append(SimpleThread.single(Function, I))
      elif len(Tasks) > 0:
        T = Tasks[0]
        if T:
          yield T.getResult()
          Tasks.remove(T)
        else:
          sleep(0.001)
    while len(Tasks) > 0:
      T = Tasks[0]
      if T:
        yield T.getResult()
        Tasks.remove(T)
      else:
        sleep(0.001)
