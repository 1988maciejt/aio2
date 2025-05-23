import _thread
from time import sleep
from libs.aio import *

class SimpleThread:
  pass

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
  
def _simple_thread(MyTask : SimpleThreadingTask, SimpleThreadObject : SimpleThread, Force, Function, args, kwargs):
  if not Force:
    while SimpleThreadObject._parallel_jobs >= SimpleThreadObject.MaxParallelJobs:
      sleep(0.001)
    SimpleThreadObject._parallel_jobs += 1
  try:
    MyTask._result = Function(*args, **kwargs)
  except Exception as inst:
    Aio.printError(f"SimpleThread: {inst}")
  if not Force:
    SimpleThreadObject._parallel_jobs -= 1
  MyTask._done = True


class SimpleThread:
  
  __slots__ = ('MaxParallelJobs', '_parallel_jobs')
  
  def __init__(self, MaxParallelJobs = 32) -> None:
    self.MaxParallelJobs = MaxParallelJobs
    self._parallel_jobs = 0
  
  def single(self, Function, *args, **kwargs):
    Task = SimpleThreadingTask()
    _thread.start_new_thread(_simple_thread, tuple([Task, self,False, Function, args, kwargs]))
    return Task
  
  def _single_forced(self, Function, *args, **kwargs):
    Task = SimpleThreadingTask()
    _thread.start_new_thread(_simple_thread, tuple([Task, self, True, Function, args, kwargs]))
    return Task

  def uimap(self, Function, Iterable):
    Tasks = []
    for I in Iterable:
      if self._parallel_jobs < self.MaxParallelJobs:
        Tasks.append(self._single_forced(Function, I))
        self._parallel_jobs += 1
      elif len(Tasks) > 0:
        for T in Tasks:
          if T:
            Tasks.remove(T)
            self._parallel_jobs -= 1
            yield T.getResult()
            break
        sleep(0.001)
    while len(Tasks) > 0:
      for T in Tasks:
        if T:
          Tasks.remove(T)
          self._parallel_jobs -= 1
          yield T.getResult()
          break
      sleep(0.001)
      
  def imap(self, Function, Iterable):
    Tasks = []
    for I in Iterable:
      while 1:
        if self._parallel_jobs < self.MaxParallelJobs:
          print("START")
          Tasks.append(self._single_forced(Function, I))
          self._parallel_jobs += 1
          break
        elif len(Tasks) > 0:
          T = Tasks[0]
          if T:
            yield T.getResult()
            print("END")
            Tasks.remove(T)
            self._parallel_jobs -= 1
          else:
            sleep(0.001)
    while len(Tasks) > 0:
      T = Tasks[0]
      if T:
        yield T.getResult()
        print("END")
        Tasks.remove(T)
        self._parallel_jobs -= 1
      else:
        sleep(0.001)
        
  def map(self, Function, Iterable) -> list:
    Tasks = []
    Result = []
    for I in Iterable:
      while 1:
        if self._parallel_jobs < self.MaxParallelJobs:
          Tasks.append(self._single_forced(Function, I))
          self._parallel_jobs += 1
          break
        elif len(Tasks) > 0:
          T = Tasks[0]
          if T:
            Result.append(T.getResult())
            Tasks.remove(T)
            self._parallel_jobs -= 1
          else:
            sleep(0.001)
    while len(Tasks) > 0:
      T = Tasks[0]
      if T:
        Result.append(T.getResult())
        Tasks.remove(T)
        self._parallel_jobs -= 1
      else:
        sleep(0.001)
    return Result
  
class SimpleThreadInterval:

  __slots__ = ('Interval', '_enabled', '_function', '_args', '_kwargs', '_next_time', "_add_later")

  def __init__(self, Interval : float, function, *args, **kwargs):
    self.Interval = Interval
    self._enabled = False
    self._function = function
    self._args = args
    self._kwargs = kwargs
    self._next_time = 0
    self._add_later = 0
  
  def setAddingType(self, Later : bool = False):
    self._add_later = Later

  def _action(self):
    self._next_time = time.time()
    while self._enabled:
      if time.time() >= self._next_time:
        if not self._add_later:
          self._next_time += self.Interval
        try:
          self._function(*self._args, **self._kwargs)
        except Exception as inst:
          Aio.printError(f"SimpleThreadInterval: {inst}")
        if self._add_later:
          self._next_time += self.Interval
      sleep(0.001)

  def run(self):
    self._enabled = True
    SimpleThread(1).single(self._action)

  start = run

  def stop(self):
    self._enabled = False

  def getTimeToNext(self) -> float:
    return self._next_time - time.time()
