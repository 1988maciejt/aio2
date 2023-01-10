from libs.udp import *
from libs.aio import *
from time import sleep
from tqdm import tqdm
from random import uniform
import netifaces
import pathos.multiprocessing as mp

import ast
import shutil
import copy
import gc
import os
import inspect
import collections
import multiprocess
from p_tqdm import p_map
import imp
#import numba
from asyncore import ExitNow
import random
import re
import sys
import plotext
import time
import openpyxl
import openpyxl.styles
import pickle
import xlsxwriter
import numpy
import zlib
import gzip
import statistics
import pathlib
import fileinput
import tempfile
import shelve
import dbm
from libs.asci_drawing import *
from libs.bent_function import *
from libs.binstr import *
from libs.binstream import *
from libs.ca import *
from libs.cas import *
from libs.cpp_program import *
from libs.database import *
from libs.eseries import *
from libs.files import *
from libs.gcd import *
from libs.lfsr import *
from libs.nlfsr import *
from libs.phaseshifter import *
from libs.pandas_table import *
from libs.polynomial import *
from libs.preprocessor import *
from libs.programmable_lfsr import *
from libs.simplecommandparser import *
import libs.PolynomialsArithmetic as PolynomialsArithmetic
from libs.ring_oscillator import *
from libs.stats import *
from libs.unitnumber import *
from libs.utils_array import *
from libs.utils_bitarray import *
from libs.utils_int import *
from libs.generators import *
from libs.utils_serial import *
from libs.utils_str import *
from libs.verilog import *
from libs.verilog_creator import *
import bitarray.util
from bitarray import *
import pandas
from sympy import *
import libs.jt as JT
import re
from libs.utils_list import *



_RemoteAioListener = None
_RemoteAioBufferSize = 8 * 1024 * 1024
_RemoteAioMyIp = None
_RemoteAioBroadcastIp = None
_RemoteAioServers = []
_RemoteAioServerId = 0
_RemoteAioWorking = False
_RemoteAioTasks = []
_RemoteAioServerIterator = 0
_RemoteAioResults = {}

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
    EVAL_REQUEST = "EVAL_REQUEST"
    RESPONSE = "RESPONSE"

class _RemoteAioMessage:
    __slots__ = ("Payload", "SenderIp", "Id", "ServerId", "Code")
    def __init__(self, Payload : str, Id = 0, ServerId = -1, Code = None) -> None:
        global _RemoteAioServerId
        self.Payload = Payload
        self.SenderIp = ""
        self.Id = Id
        self.Code = Code
        if ServerId < 0:
            self.ServerId = _RemoteAioServerId
        else:
            self.ServerId = ServerId
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
    def sendMessage(self, Payload : str, Id = 0, Code = None):
        _RemoteAioMessage(Payload, Id, self.ServerId, Code).sendTo(self.Ip, self.Port)
    def requestEval(self, Code : str) -> int:
        Id = _randId()
        self.sendMessage(_RemoteAioMessages.EVAL_REQUEST, Id, Code)
        return Id
    
    
class _RemoteAioTask:
    __slots__ = ("Type", "ServerIp", "Port", "Code", "Id", "ServerId")
    def __init__(self, Type : str, Id : int, ServerId : int, ServerIp : str, Port : str, Code : str) -> None:
        self.Type = Type
        self.Id = Id
        self.ServerIp = ServerIp
        self.ServerId = ServerId
        self.Port = Port
        self.Code = Code
    def exe(self):
        print(f"RemoteAio: executing task {self.Id} for {self.ServerIp}")
        R = eval(self.Code, globals(), locals())
        M = _RemoteAioMessage(_RemoteAioMessages.RESPONSE, self.Id, self.ServerId, R)
        M.sendTo(self.ServerIp, self.Port)
        print(f"RemoteAio: finished task {self.Id} for {self.ServerIp}")
    
    
def requestRemoteAioEval(Code : str) -> int:
    global _RemoteAioServers, _RemoteAioServerIterator
    Id = _RemoteAioServers[_RemoteAioServerIterator].requestEval(Code)
    _RemoteAioServerIterator = (_RemoteAioServerIterator + 1) % len(_RemoteAioServers)
    return Id
        
def _getServer(Ip, Id) -> _RemoteAioServer:
    global _RemoteAioServers
    for s in _RemoteAioServers:
        if s.Ip == Ip and s.Id == Id:
            return s
    return None
        

def _RemoteCallback(args):
    global _RemoteAioServers, _RemoteAioTasks, _RemoteAioServerId, _RemoteAioResults
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
        elif Data.Payload == _RemoteAioMessages.EVAL_REQUEST:
            T = _RemoteAioTask("eval", Data.Id, _RemoteAioServerId, Ip, Port, Data.Code)
            _RemoteAioTasks.append(T)
            print(f"RemoteAio: Received task {Data.Id} for {Ip}")
            _doRemoteAioTasks()
        elif Data.Payload == _RemoteAioMessages.RESPONSE:
            print(f"RemoteAio: Received result of task {Data.Id} from {Ip}")
            _RemoteAioResults[Data.Id] = pickle.dumps(Data.Code)
                    
def _doRemoteAioTasks(dummy = None):
    global _RemoteAioTasks, _RemoteAioWorking
    while _RemoteAioWorking and len(_RemoteAioTasks) > 0:
        T = _RemoteAioTasks[0]
        T.exe()
        _RemoteAioTasks.remove(T)
        del T
    if not _RemoteAioWorking:
        _RemoteAioTasks.clear()



    
def getRemoteAioServers() -> list:
    global _RemoteAioServers
    return _RemoteAioServers

def getRemoteAioResult(Id : int):
    global _RemoteAioResults
    Data = _RemoteAioResults.get(Id, None)
    if Data is None:
        return None
    Ob = pickle.loads(Data)
    _RemoteAioResults[Id] = None
    return Ob


def stopRemoteAio():
    global _RemoteAioListener, _RemoteAioResults, _RemoteAioServerId, _RemoteAioWorking, _RemoteAioTasks, _RemoteAioResults
    _RemoteAioServerId = 0
    if _RemoteAioListener is not None:
        _RemoteAioListener.stop()
        del _RemoteAioListener
        _RemoteAioListener = None
    _RemoteAioTasks.clear()
    _RemoteAioResults.clear()
    _RemoteAioWorking = False
    
def startRemoteAio(Port = 3099):
    global _RemoteAioListener, _RemoteAioBufferSize, _RemoteAioWorking, _RemoteAioServerId, _RemoteAioTasks, _RemoteAioServerIterator
    stopRemoteAio()
    _RemoteAioListener = UdpMonitor([Port, [Port, _myIP()]], BufferSize=_RemoteAioBufferSize, Callback=_RemoteCallback, ReturnString=False)
    _RemoteAioListener.start()
    sleep(0.2)
    if _RemoteAioListener.isWorking():
        _RemoteAioServerId = _randId()
        print(f"RemoteAio: is available, Server ip: {_myIP()}, ServerId: {_RemoteAioServerId}")
        _RemoteAioServerIterator = 0
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
    _RemoteAioMessage(_RemoteAioMessages.LOOKING_FOR_SERVERS).sendTo("", Port)
    for i in range(1):
        sleep(1)
    print(f"RemoteAio: {len(_RemoteAioServers)} servers found")
    return _RemoteAioServers

def getServers():
    global _RemoteAioServers
    return _RemoteAioServers

def _getTasks():
    global _RemoteAioTasks
    return _RemoteAioTasks

    
