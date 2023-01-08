import socket
from libs.aio import *
import pathos.multiprocessing as mp
from libs.utils_str import *

class UdpListener:
  
  __slots__ = ("_port", "_buffer_size", "_callback", "_socket", "_continue", "_pool", "_ret_str")
  
  def __init__(self, Port : int, Callback = None, BufferSize = 4096, ReturnString = True) -> None:
    self._port = abs(int(Port))
    self._buffer_size = abs(int(BufferSize))
    self._callback = Callback
    self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    self._continue = 0
    self._ret_str = bool(ReturnString)
    self._pool = mp.ThreadingPool()
    
  def _wait(self, dummy):
    data, addr = self._socket.recvfrom(self._buffer_size)
    if self._ret_str:
      data = data.decode("utf-8")
    if self._callback is None:
      print(f"{Str.color(f'{addr[0]}:{self._port}', 'blue')}: {data}", end='')
    else:
      self._callback((data, addr))
    if self._continue:
      self._pool.amap(self._wait, [0])
      
  def isActive(self) -> bool:
    return True if self._continue else False
    
  def start(self):
    if self._continue:
      Aio.printError("The UDP listener is stil running")
    else:
      self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
      self._socket.bind(("", self._port))
      self._continue = 1
      if self._callback is None:
        print(f"{Str.color(f'Starting UDP monitor at port {self._port}', 'blue')}")
      self._pool.amap(self._wait, [0])
    
  def stop(self):
    self._continue = 0
    self._pool.terminate()
    