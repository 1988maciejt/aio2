import multiprocessing
from libs.aio import *
import time
import pathos

class MultiTasks:
  def __init__(self, label = "MultiTasks", quiet = False) -> None:
    self._tasks = []
    self._n = 0
    self._quiet = quiet
    self.lbl = label
  def _task(self, Task):
    fname = Task[0]
    args = Task[1]
    self._res.append(fname(*args))
    if not self._quiet:
      cnt = len(self._res)
      if cnt % self._e == 0:
        perc = round(cnt * 100 / self._n, 1)
        Aio.printTemp(" ",self.lbl,":",perc,"%                ")
  def addTask(self, fname, *args):
    self._tasks.append([fname, args])
    self._n += 1
  def run(self):
    man = multiprocessing.Manager()
    self._e = int(round(self._n / 1000, 0))
    if self._e < 1: 
      self._e = 1
    self._res = man.list()
    pool = multiprocessing.Pool()
    pool.map_async(self._task, self._tasks)
    pool.close()
    pool.join()
    tr = list(self._res)
    del self._res
    if not self._quiet:
      Aio.printTemp("                          ")
    return tr