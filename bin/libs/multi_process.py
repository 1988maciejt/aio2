import multiprocessing
from statistics import multimode
from libs.aio import *
import time
import pathos

task_list = []
task_pool = pathos.multiprocessing.ThreadingPool()

class TaskMonitor:
  pass

class Task:
  _args = []
  _fname = None
  _result = None
  _done = False
  _my_monitor = None
  def __init__(self, fname, *args) -> None:
    self._args = args
    self._fname = fname
  def run(self, dummy=None):
    self._result = self._fname(*self._args)
    self._done = True
    if self._my_monitor != None:
      self._my_monitor._finished += 1
  def ready(self):
    return self._done
  def getResult(self):
    return self._result

class TaskMonitor:
  """This is a class for Task Monitor.
  Use this to monitor bunch of tasks scheduled by createMonitoredTask.
  """
  _tasks = []
  _count = 0
  _finished = 0
  def count(self) -> int:
    return self._count
  def ready(self, index = None) -> bool:
    if index != None:
      return self._tasks[index].ready()
    return (self._count == self._finished)
  def finished(self) -> int:
    return self._finished
  def percent(self) -> bool:
    return self._finished * 100. / self._count
  def getResult(self, index : int()):
    return self._tasks[index].getResult()
  def addTask(self, t : Task):
    self._tasks.append(t)
    self._count += 1
    t._my_monitor = self
  def clear(self):
    self._tasks.clear()
    self._count = 0
    self._finished = 0

def createTask(fname, *args):
  """Adds a created task to be executed asynchronously.

  Args:
      fname (function pointer): pointer to a function to be called
      *args: function args
      
  Returns:
      Task: a Task object
  """
  global task_list
  t = Task(fname,*args)
  task_list.append(t)
  return t

def createMonitoredTask(Monitor: TaskMonitor, fname, *args):
  """Adds a created task to be executed asynchronously.
  Also adds this task to the specified TaskMonitor object

  Args:
      Monitor: TaskMonitor object
      fname (function pointer): pointer to a function to be called
      *args: function args
      
  Returns:
      Task: a Task object
  """
  t = createTask(fname, *args)
  Monitor.addTask(t)
  return t

def tasks_agent(dummy=None):
  global task_list
  global task_pool
  while True:
    while len(task_list) > 0:
      t = task_list[0]
      task_pool.amap(t.run, [0])
      task_list.remove(t)
    time.sleep(0.05)
  
task_pool.amap(tasks_agent, [0])

