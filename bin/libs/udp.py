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
    self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    self._socket.bind(("", self._port))
    self._continue = 0
    self._ret_str = bool(ReturnString)
    self._pool = mp.ThreadingPool()
    
  def _wait(self, dummy):
    #print("WAIT")
    data, addr = self._socket.recvfrom(self._buffer_size)
    if self._ret_str:
      data = data.decode("utf-8")
    if self._callback is None:
      print(f"{Str.color(f'{addr[0]}:{self._port}', 'blue')}: {data}")
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
      self._continue = 1
      if self._callback is None:
        print(f"{Str.color(f'Starting UDP monitor at port {self._port}', 'blue')}")
      self._pool.amap(self._wait, [0])
    
  def stop(self):
    self._continue = 0
    self._pool.terminate()
    
    

class UdpSender:
  
  __slots__ = ("_port", "_ip")
  
  def __init__(self, Port = None, DestinationIp = None) -> None:
    self._port = abs(int(Port))
    self._ip = DestinationIp
    
  def send(self, Message, IP = None, Port = None):
    if Aio.isType(Message, ""):
      Message = bytes(Message, "utf-8")
    _ip = self._ip
    _port = self._port
    if IP is not None:
      _ip = IP
    if Port is not None:
      _port = Port
    if _port is None:
      Aio.printError("Port not specified")
      return
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # UDP
    if _ip is None:
      _ip = "255.255.255.255"
      sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(Message, (_ip, _port))
    sock.close()
    
    
class UdpMonitor:
  
  __slots__ = ("_port_list", "_listeners", "_cbk", "_buffer_size")
  
  def __init__(self, PortList, Callback = None, BufferSize = 4096) -> None:
    self._port_list = PortList
    self._listeners = []
    self._cbk = Callback
    self._buffer_size = BufferSize
    
  def start(self):
    if len(self._listeners) > 0:
      self.stop()
    for p in self._port_list:
      l = UdpListener(p, Callback=self._cbk, BufferSize=self._buffer_size)
      self._listeners.append(l)
      l.start()
  
  def stop(self):
    for l in self._listeners:
      l.stop()
    self._listeners.clear()