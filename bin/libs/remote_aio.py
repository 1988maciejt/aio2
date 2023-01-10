from libs.udp import *
from libs.aio import *
from time import sleep
from tqdm import tqdm
from random import uniform
import netifaces


_RemoteAioListener = None
_RemoteAioBufferSize = 8 * 1024 * 1024
_RemoteAioMyIp = None
_RemoteAioBroadcastIp = None
_RemoteAioServers = []
_RemoteAioServerId = 0
_RemoteAioWorking = False

def _randId():
    return int(uniform(1, 10000000000000000))

def _myIP() -> str:
    global _RemoteAioMyIp
    if _RemoteAioMyIp is None:
        interface = list(netifaces.gateways()['default'].values())[0][1]
        _RemoteAioMyIp = netifaces.ifaddresses(interface)[2][0]['addr']
    return _RemoteAioMyIp

def _myBroadcastIP() -> str:
    global _RemoteAioBroadcastIp
    if _RemoteAioBroadcastIp is None:
        interface = list(netifaces.gateways()['default'].values())[0][1]
        _RemoteAioBroadcastIp = netifaces.ifaddresses(interface)[2][0]['broadcast']
    return _RemoteAioBroadcastIp
    
    

class _RemoteAioMessages:
    LOOKING_FOR_SERVERS = "LOOKING_FOR_SERVERS"  
    HELLO = "HELLO"   
    PING = "PING"  
    REQUEST = "REQUEST"
    RESPONSE = "RESPONSE"

class _RemoteAioMessage:
    __slots__ = ("Payload", "SenderIp", "Id", "ServerId", "Code")
    def __init__(self, Payload : str, Id = 0, ServerId = -1) -> None:
        global _RemoteAioServerId
        self.Payload = Payload
        self.SenderIp = ""
        self.Id = Id
        if ServerId < 0:
            self.ServerId = _RemoteAioServerId
        else:
            self.ServerId = ServerId
        self.Code = ""
    def sendTo(self, Ip, Port):
        self.SenderIp = _myIP()
        UdpSender(Port, Ip).send(pickle.dumps(self))
        #print(f"SENT {Ip}:{Port}", self.Payload)
        
        
class _RemoteAioServer:
    __slots__ = ("Ip", "ServerId", "Port")
    def __init__(self, Ip, ServerId, Port = 3099) -> None:
        self.Ip = Ip
        self.ServerId = ServerId
        self.Port = Port
    def __eq__(self, __o: object) -> bool:
        return self.Ip == __o.Ip and self.ServerId == __o.ServerId
    def __neq__(self, __o: object) -> bool:
        return not (self == __o)
    def __repr__(self) -> str:
        return f"RemoteAioServer({self.Ip}, {self.ServerId})"
    def __str__(self) -> str:
        return repr(self)
        
def _getServer(Ip, Id) -> _RemoteAioServer:
    global _RemoteAioServers
    for s in _RemoteAioServers:
        if s.Ip == Ip and s.Id == Id:
            return s
    return None
        

def _RemoteCallback(args):
    global _RemoteAioServers
    RawData = args[0]
    Ip = args[1]
    Port = args[2]
    Data = ""
    try:
        Data = pickle.loads(RawData)
    except:
        pass
    if Aio.isType(Data, "_RemoteAioMessage"):
        #print("RECEIVED", RawData)
        #Ip = Data.SenderIp
        ServerId = Data.ServerId
        if Data.Payload == _RemoteAioMessages.LOOKING_FOR_SERVERS:
            _RemoteAioMessage(_RemoteAioMessages.HELLO).sendTo(Ip, Port)
        elif Data.Payload == _RemoteAioMessages.PING:
            _RemoteAioMessage(_RemoteAioMessages.HELLO).sendTo(Ip, Port)
        elif Data.Payload == _RemoteAioMessages.HELLO:
            Server = _RemoteAioServer(Ip, ServerId, Port)
            if Server not in _RemoteAioServers:
                _RemoteAioServers.append(Server)
                    




    
def getRemoteAioServers() -> list:
    global _RemoteAioServers
    return _RemoteAioServers


def stopRemoteAio():
    global _RemoteAioServerListener, _RemoteAioListener, _RemoteAioServerSender, _RemoteAioServerId, _RemoteAioWorking
    _RemoteAioServerId = 0
    if _RemoteAioListener is not None:
        _RemoteAioListener.stop()
        del _RemoteAioListener
        _RemoteAioListener = None
    _RemoteAioWorking = False
    
def startRemoteAio(Port = 3099):
    global _RemoteAioServerListener, _RemoteAioListener, _RemoteAioBufferSize, _RemoteAioWorking, _RemoteAioServerId
    stopRemoteAio()
    #_RemoteAioListener = UdpMonitor([Port, [Port, _myIP()]], BufferSize=_RemoteAioBufferSize, Callback=_RemoteCallback, ReturnString=False)
    _RemoteAioListener = UdpListener(Port, BufferSize=_RemoteAioBufferSize, Callback=_RemoteCallback, ReturnString=False, BindToIp=_myIP())
    _RemoteAioListener.start()
    sleep(0.2)
    if _RemoteAioListener.isWorking():
        _RemoteAioServerId = _randId()
        print(f"RemoteAio: is available, Server ip: {_myIP()}, ServerId: {_RemoteAioServerId}")
        _RemoteAioWorking = True
    else:
        Aio.printError(f"RemoteAio: NOT AVAILABLE")
        stopRemoteAio()
    
def isRemoteAioWorking():
    global _RemoteAioWorking
    return _RemoteAioWorking


def lookForRemoteAioServers(Port = 3099):
    global _RemoteAioServers, _RemoteAioWorking
    if not _RemoteAioWorking:
        startRemoteAio(Port)
    _RemoteAioServers = []
    _RemoteAioMessage(_RemoteAioMessages.LOOKING_FOR_SERVERS).sendTo(_myBroadcastIP(), Port)
    for i in range(1):
        sleep(1)
    print(f"RemoteAio: {len(_RemoteAioServers)} servers found")
    return _RemoteAioServers