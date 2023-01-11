import socket
from libs.aio import *
import pathos.multiprocessing as mp
from libs.utils_str import *
import select
import netifaces
from libs.utils_list import *
from random import uniform
import gzip


_FragmentedMessages = {}


def _randId():
    return int(uniform(1, 10000000000000000))


class _UdpFragmenterMessage:
  __slots__ = ("Payload", "Id", "Index", "MaxIndex")
  def __init__(self, Payload : bytes, Id : int, Index : int, MaxIndex : int) -> None:
    self.Payload = Payload
    self.Index = Index
    self.MaxIndex = MaxIndex
    self.Id = Id
    
class _UdpFragmenterConcatenator:
  __slots__ = ("_messages", "_parts")
  def __init__(self, FirstMessage : _UdpFragmenterMessage) -> None:
    self._messages = {}
    self._parts = FirstMessage.MaxIndex
    self._messages[FirstMessage.Index] = FirstMessage.Payload
  def isComplete(self) -> bool:
    return self._parts == len(self._messages)
  def addMessage(self, Message : _UdpFragmenterMessage):
    self._messages[Message.Index] = Message.Payload
  def getMessage(self) -> bytes:
    try:
      Msg = bytes()
      for i in range(1, self._parts+1):
        Msg += self._messages[i]
      return Msg
    except:
      Aio.printError("UDP MONITOR: Fragmented message is not complete")
    
    



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
    
  def _send(self, sock, Message, _ip, _port) -> bool:
    try:
      sock.sendto(Message, (_ip, _port))
    except Exception as inst:
      Aio.printError("UdpSender - sending error!", inst)
      return False
    return True
    
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
    if _ip is None or len(_ip) < 7:
      _ip = getMyBroadcastIp()
      sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    if len(Message) > 1024:
      Id = _randId()
      SubMessages = List.splitIntoSublists(gzip.compress(Message), 800)
      MaxIndex = len(SubMessages)
      Index = 1
      for subMessage in SubMessages:
        Frag = _UdpFragmenterMessage(subMessage, Id, Index, MaxIndex)
        self._send(sock, pickle.dumps(Frag), _ip, _port)
        #print(f"Sent {Id} \t{Index}/{MaxIndex}")
        Index += 1
    else:
      self._send(sock, Message, _ip, _port)
    sock.close()
    
    
class UdpMonitor:
  
  __slots__ = ("_port_list", "_listeners", "_callback", "_buffer_size", "_continue", "_ret_str", "_pool", "_working", "_bindip")
  
  def __init__(self, PortList, Callback = None, BufferSize = 4096, ReturnString = False, BindToIp="") -> None:
    if Aio.isType(PortList, 0):
      self._port_list = [PortList, [PortList,getMyIp()]]
    else:
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
    global _FragmentedMessages
    while self._continue:
      self._working = True
      readable, writable, exceptional = select.select(self._listeners, [], [])
      if not self._continue:
        self._working = False
        return
      for s in readable:
        data, addr = s.recvfrom(1024)
        port = self._port_list[self._listeners.index(s)]
        try:
          Fragment = pickle.loads(data)
          if Aio.isType(Fragment, "_UdpFragmenterMessage"):
            Id = Fragment.Id
            #print(f"Message {Id} \t{Fragment.Index}/{Fragment.MaxIndex}")
            MCat = _FragmentedMessages.get(Id, None)
            if MCat is None:
              MCat = _UdpFragmenterConcatenator(Fragment)
              _FragmentedMessages[Id] = MCat
            else:
              MCat.addMessage(Fragment)
            if MCat.isComplete():
              data = gzip.decompress(MCat.getMessage())
              _FragmentedMessages.pop(Id)
            else:
              continue
        except:
          pass
        if not Aio.isType(port, 0):
          port = port[0]
        if self._ret_str:
          data = data.decode("utf-8")
        if self._callback is None:
          print(f"{Str.color(f'{addr[0]}:{port}', 'blue')}: {data}")
        else:
          #print(f"{Str.color(f'{addr[0]}:{port}', 'blue')}: {data}")
          self._callback((data, addr[0], port))
          #print("END OF CBK")
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
      if len(a) < 7:
        _socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
      _socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self._buffer_size)
      _socket.setblocking(0)
      try:
        _socket.bind((a, p))
      except Exception as inst:
        Aio.printError(f"Port {p}:", inst)
      self._listeners.append(_socket)
    self._continue = True
    self._pool.amap(self._wait, [0])  
  
  def stop(self):
    self._continue = False
    self._working = False
    self._listeners.clear()
    
  def isWorking(self):
    return self._working