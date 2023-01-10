import socket
from libs.aio import *
import pathos.multiprocessing as mp
from libs.utils_str import *
import select
import netifaces


def getMyIp() -> str:
  interface = list(netifaces.gateways()['default'].values())[0][1]
  return netifaces.ifaddresses(interface)[2][0]['addr']

def getMyBroadcastIp() -> str:
  interface = list(netifaces.gateways()['default'].values())[0][1]
  return netifaces.ifaddresses(interface)[2][0]['broadcast']


class UdpSender:
  
  __slots__ = ("_port", "_ip", "_bindip")
  
  def __init__(self, Port = None, DestinationIp = None) -> None:
    self._port = abs(int(Port))
    self._ip = DestinationIp
    
  def send(self, Message, IP = None, Port = None):
    if not Aio.isType(Message, bytes()):
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
      _ip = getMyBroadcastIp()
      sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(Message, (_ip, _port))
    sock.close()
    
    
class UdpMonitor:
  
  __slots__ = ("_port_list", "_listeners", "_callback", "_buffer_size", "_continue", "_ret_str", "_pool", "_working", "_bindip")
  
  def __init__(self, PortList, Callback = None, BufferSize = 4096, ReturnString = True, BindToIp="") -> None:
    self._port_list = [i for i in PortList]
    self._listeners = []
    self._callback = Callback
    self._buffer_size = BufferSize
    self._continue = 0
    self._ret_str = bool(ReturnString)
    self._pool = mp.ThreadingPool()
    self._working = False
    self._bindip = BindToIp
    
  def _wait(self, dummy):
    while self._continue:
      self._working = True
      readable, writable, exceptional = select.select(self._listeners, [], [])
      if not self._continue:
        self._working = False
        return
      for s in readable:
        data, addr = s.recvfrom(self._buffer_size)
        port = self._port_list[self._listeners.index(s)]
        if not Aio.isType(port, 0):
          port = port[0]
        if self._ret_str:
          data = data.decode("utf-8")
        if self._callback is None:
          print(f"{Str.color(f'{addr[0]}:{port}', 'blue')}: {data}")
        else:
          self._callback((data, addr[0], port))
      self._working = False

  def start(self):
    if len(self._listeners) > 0:
      self.stop()
    if self._callback is None:
      print(f"{Str.color(f'Starting UDP monitor', 'blue')}")
    for pi in self._port_list:
      p = pi
      a = self._bindip
      if not Aio.isType(pi, 0):
        p = pi[0]
        a = pi[1]
      _socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
      _socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      _socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
      _socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
      _socket.setblocking(0)
      try:
        _socket.bind((a, p))
      except:
        Aio.printError(f"Port {p} in use")
      self._listeners.append(_socket)
    self._continue = True
    self._pool.amap(self._wait, [0])  
  
  def stop(self):
    self._continue = False
    self._working = False
    self._listeners.clear()
    
  def isWorking(self):
    return self._working