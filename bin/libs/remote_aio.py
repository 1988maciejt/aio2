from libs.udp import *
from libs.aio import *
from time import sleep
from tqdm import tqdm
from random import uniform

_RemoteAioServerListener = None
_RemoteAioListener = None
_RemoteAioBufferSize = 8 * 1024 * 1024
_RemoteAioMyIp = None
_RemoteAioServers = []
_RemoteAioServerId = 0
_RemoteAioWorking = 0

def _randId():
    return int(uniform(1, 10000000000000000))

def _myIP(Port = 3099) -> str:
    global _RemoteAioMyIp
    if _RemoteAioMyIp is None:
        ips = Aio.shellExecute("hostname -I").strip().split(" ")
        for ip in ips:
            try:
                UdpSender(Port, ip).send("ip_test")
                _RemoteAioMyIp = ip
                break
            except:
                pass
    return _RemoteAioMyIp
    

class _RemoteAioMessages:
    LOOKING_FOR_SERVERS = "LOOKING_FOR_SERVERS"  
    HELLO = "HELLO"   
    PING = "PING"  

class _RemoteAioMessage:
    __slots__ = ("Payload", "SenderIp", "Id", "ServerId")
    def __init__(self, Payload : str, Id = 0, ServerId = -1) -> None:
        global _RemoteAioServerId
        self.Payload = Payload
        self.SenderIp = ""
        self.Id = Id
        if ServerId < 0:
            self.ServerId = _RemoteAioServerId
        else:
            self.ServerId = ServerId
    def sendTo(self, Ip, Port):
        self.SenderIp = _myIP(Port)
        UdpSender(Port, Ip).send(pickle.dumps(self))
        print("SENT", self.Payload)
        
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
        
        
        

def _RemoteCallback(args):
    global _RemoteAioServers
    RawData = args[0]
    Port = args[2]
    Data = ""
    try:
        Data = pickle.loads(RawData)
    except:
        pass
    if Aio.isType(Data, "_RemoteAioMessage"):
        print("RECEIVED", RawData)
        Ip = Data.SenderIp
        ServerId = Data.ServerId
        if Data.Payload == _RemoteAioMessages.LOOKING_FOR_SERVERS:
            _RemoteAioMessage(_RemoteAioMessages.HELLO).sendTo(Ip, Port)
            print(f"RemoteAio: {Ip}:{Port} is looking for servers")
        elif Data.Payload == _RemoteAioMessages.PING:
            _RemoteAioMessage(_RemoteAioMessages.HELLO).sendTo(Ip, Port)
            print(f"RemoteAio: {Ip} is pinging")
        elif Data.Payload == _RemoteAioMessages.HELLO:
            Server = _RemoteAioServer(Ip, ServerId, Port)
            if Server not in _RemoteAioServers:
                _RemoteAioServers.append(Server)
                    




def lookForRemoteAioServers(Port = 3099):
    global _RemoteAioServers
    _RemoteAioServers = []
    ul = UdpListener(Port, ReturnString=0, Callback=_RemoteCallback, BindToIp=_myIP())
    ul.start()
    _RemoteAioMessage(_RemoteAioMessages.LOOKING_FOR_SERVERS).sendTo("255.255.255.255", Port)
    for i in tqdm(range(10), desc="Looking for RemoteAio servers"):
        sleep(0.2)
    print("Finished", _RemoteAioServers)
    ul.stop()
    del ul
    
     


def stopRemoteAio():
    global _RemoteAioServerListener, _RemoteAioListener, _RemoteAioServerSender, _RemoteAioServerId, _RemoteAioWorking
    _RemoteAioServerId = _randId()
    if _RemoteAioServerListener is not None:
        _RemoteAioServerListener.stop()
        del _RemoteAioServerListener
        _RemoteAioServerListener = None
    if _RemoteAioListener is not None:
        _RemoteAioListener.stop()
        del _RemoteAioListener
        _RemoteAioListener = None
    _RemoteAioWorking = 0
    
def startRemoteAio(Server = False, Port = 3099):
    global _RemoteAioServerListener, _RemoteAioListener, _RemoteAioBufferSize, _RemoteAioWorking
    stopRemoteAio()
    if Server:
        print(f"RemoteAio: server started Id {_RemoteAioServerId} started at {_myIP()}")
        _RemoteAioServerListener = UdpListener(Port, BufferSize=_RemoteAioBufferSize, Callback=_RemoteCallback, ReturnString=False)
        _RemoteAioServerListener.start()
        sleep(0.2)
        if _RemoteAioServerListener.isWorking():
            print(f"RemoteAio: server is available")
        else:
            Aio.printError(f"RemoteAio: SERVER IS NOT WORKING")
    _RemoteAioListener = UdpListener(Port, BufferSize=_RemoteAioBufferSize, Callback=_RemoteCallback, ReturnString=False, BindToIp=_myIP())
    _RemoteAioListener.start()
    sleep(0.2)
    if _RemoteAioListener.isWorking():
        print(f"RemoteAio: client is available")
    else:
        Aio.printError(f"RemoteAio: CLIENT IS NOT WORKING")
    _RemoteAioWorking = 1
    
def isRemoteAioWorking():
    global _RemoteAioWorking
    return _RemoteAioWorking
