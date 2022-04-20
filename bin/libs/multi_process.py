import multiprocessing
from libs.aio import *
import time
import pathos

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
    tp = pathos.multiprocessing.ThreadingPool()
    xp = tp.apipe(self._fname, self._args)
    xp.wait()
    self._result = xp.getResult()
    #self._result = self._fname(*self._args)
    self._done = True
    if self._my_monitor != None:
      self._my_monitor._add()
  def ready(self):
    return self._done
  def getResult(self):
    return self._result

class Tasks:
  _tasks = []
  _count = 0
  _finished = 0
  _name = ""
  _pool = None
  _poolres = None
  def __init__(self, name="") -> None:
    self._name = name
    self.clear()
  def _add(self):
    print("ADD")
    self._finished += 1
  def create(self, fname, *args):
    t = Task(fname, *args)
    t._my_monitor = self
    self._count += 1
    self._tasks.append(t)
  def getCount(self) -> int:
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
    print("Added")
  def clear(self):
    self._my_pool = None
    self._tasks.clear()
    self._count = 0
    self._finished = 0

def runTasks(tasks):
  pool = pathos.pools.ProcessPool()
  for t in tasks._tasks:
    pool.apipe(t.run)
  while not tasks.ready():
    pass
  print("HERE")
  
