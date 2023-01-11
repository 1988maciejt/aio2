from libs.udp import *
from libs.aio import *
from time import sleep
from tqdm import tqdm
from random import uniform
import netifaces
import pathos.multiprocessing as mp
import time
import _thread

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
_RemoteAioBufferSize = 64 * 1024 * 1024
_RemoteAioMyIp = None
_RemoteAioBroadcastIp = None
_RemoteAioServers = []
_RemoteAioServerId = 0
_RemoteAioWorking = False
_RemoteAioTasks = []
_RemoteAioServerIterator = 0
_RemoteAioExeLock = False

_RemoteAioJobs = []



class RemoteAioJob:
    __slots__ = ("_Id", "_Code", "_Result", "_Done","_CreationTIme", "_StopTime")
    def __init__(self, Id : int, Code) -> None:
        self._Id = Id
        self._Result = None
        self._Done = False
        self._Code = Code
        self._CreationTIme = -1
        self._StopTime = -1
    def _resetTimer(self):
        self._CreationTIme = -1
    def _setNewId(self, Id : int):
        self._Id = Id
    def __eq__(self, __o: object) -> bool:
        return self._Id == __o._Id
    def __neq__(self, __o: object) -> bool:
        return not (self == __o)
    def __len__(self) -> int:
        return len(self.Code)
    def __bool__(self) -> bool:
        return self._Done
    def isDone(self):
        return self._Done
    def getCode(self):
        return self._Code
    def getResult(self):
        return self._Result   
    def getAwaitingTime(self):
        if self._CreationTIme <= 0:
            return 0
        if self._StopTime >= 1:
            return self._StopTime - self._CreationTIme
        return time.time() - self._CreationTIme
    def getId(self):
        return self._Id
    

def _randId():
    return int(uniform(1, 10000000000000000))

def _myIP() -> str:
    global _RemoteAioMyIp
    if _RemoteAioMyIp is None:
        _RemoteAioMyIp = getMyIp()
    return _RemoteAioMyIp

def _myBroadcastIP() -> str:
    global _RemoteAioBroadcastIp
    if _RemoteAioBroadcastIp is None:
        _RemoteAioBroadcastIp = getMyBroadcastIp()
    return _RemoteAioBroadcastIp

class _RemoteAioMessages:
    LOOKING_FOR_SERVERS = "LOOKING_FOR_SERVERS"  
    HELLO = "HELLO"   
    PING = "PING"  
    EVAL_REQUEST = "EVAL_REQUEST"
    RESPONSE = "RESPONSE"
    REQUEST_STARTED = "REQUEST_STARTED"

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
    def sendTo(self, Ip, Port, Repetitions=1):
        self.SenderIp = _myIP()
        UdpSender(Port, Ip).send(pickle.dumps(self), Repeatitions=Repetitions)
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
        _RemoteAioMessage(_RemoteAioMessages.REQUEST_STARTED, self.Id, self.ServerId).sendTo(self.ServerIp, self.Port)
        R = eval(self.Code, globals(), locals())
        M = _RemoteAioMessage(_RemoteAioMessages.RESPONSE, self.Id, self.ServerId, R)
        M.sendTo(self.ServerIp, self.Port, Repetitions=2)
        print(f"RemoteAio: finished task {self.Id} for {self.ServerIp}")
    
    
def _requestRemoteAioEval(Code : str) -> RemoteAioJob:
    global _RemoteAioServers, _RemoteAioServerIterator, _RemoteAioJobs
    if len(_RemoteAioServers) <= 0:
        Aio.printError("No RemoteAio servers available!")
        return None
    Id = _RemoteAioServers[_RemoteAioServerIterator].requestEval(Code)
    _RemoteAioServerIterator = (_RemoteAioServerIterator + 1) % len(_RemoteAioServers)
    Job = RemoteAioJob(Id, Code)
    if Job in _RemoteAioJobs:
        _RemoteAioJobs.remove(Job)
    _RemoteAioJobs.append(Job)
    return Job
        

def _RemoteCallback(args):
    global _RemoteAioServers, _RemoteAioTasks, _RemoteAioServerId, _RemoteAioJobs
    RawData = args[0]
    Ip = args[1]
    Port = args[2]
    Data = ""
    #print(f"RECEIVED {Ip} {RawData}")
    try:
        Data = pickle.loads(RawData)
    except:
        pass
    if Aio.isType(Data, "_RemoteAioMessage"):
        #print("RECEIVED", RawData)
        #Ip = Data.SenderIp
        ServerId = Data.ServerId
        if Data.Payload == _RemoteAioMessages.LOOKING_FOR_SERVERS:
            print(f"RemoteAio: {Ip} is looking for servers")
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
            print(f"RemoteAio: Received task {Data.Id} from {Ip}")
            #_doRemoteAioTasks()
            _thread.start_new_thread(_doRemoteAioTasks, ())
        elif Data.Payload == _RemoteAioMessages.REQUEST_STARTED:
            for J in _RemoteAioJobs:
                if J._Id == Data.Id:
                    print(f"RemoteAio: Task {Data.Id} started on {Ip}")
                    J._CreationTIme = time.time()
        elif Data.Payload == _RemoteAioMessages.RESPONSE:
            for J in _RemoteAioJobs:
                if J._Id == Data.Id:
                    print(f"RemoteAio: Received result of task {Data.Id} from {Ip}")
                    J._Result = Data.Code
                    J._Done = True
                    J._StopTime = time.time()
                    _RemoteAioJobs.remove(J)
                    break
        else:
            print(f"RemoteAio: Received {Data.Payload} from {Ip}")
    else:
        print(f"RemoteAio: Received {RawData} from {Ip}")
                    
def _doRemoteAioTasks(dummy = None):
    global _RemoteAioTasks, _RemoteAioWorking, _RemoteAioExeLock
    while _RemoteAioExeLock:
        sleep(0.3)
    _RemoteAioExeLock = True
    while _RemoteAioWorking and len(_RemoteAioTasks) > 0:
        T = _RemoteAioTasks[0]
        T.exe()
        _RemoteAioTasks.remove(T)
        del T
    if not _RemoteAioWorking:
        _RemoteAioTasks.clear()
    _RemoteAioExeLock = False



    
def _getRemoteAioServers() -> list:
    global _RemoteAioServers
    return _RemoteAioServers




def _stopRemoteAio():
    global _RemoteAioListener, _RemoteAioServerId, _RemoteAioWorking, _RemoteAioTasks, _RemoteAioJobs, _RemoteAioMyIp, _RemoteAioBroadcastIp
    _RemoteAioServerId = 0
    if _RemoteAioListener is not None:
        _RemoteAioListener.stop()
        del _RemoteAioListener
        _RemoteAioListener = None
    _RemoteAioTasks.clear()
    _RemoteAioJobs.clear()
    _RemoteAioWorking = False
    _RemoteAioMyIp = None
    _RemoteAioBroadcastIp = None
    
def _startRemoteAio(Port = 3099):
    global _RemoteAioListener, _RemoteAioBufferSize, _RemoteAioWorking, _RemoteAioServerId, _RemoteAioTasks, _RemoteAioServerIterator
    _stopRemoteAio()
    _RemoteAioListener = UdpMonitor(Port, BufferSize=_RemoteAioBufferSize, Callback=_RemoteCallback, ReturnString=False)
    _RemoteAioListener.start()
    sleep(0.2)
    if _RemoteAioListener.isWorking():
        _RemoteAioServerId = _randId()
        print(f"RemoteAio: is available, Server ip: {_myIP()}, ServerId: {_RemoteAioServerId}")
        _RemoteAioServerIterator = 0
        _RemoteAioWorking = True
    else:
        Aio.printError(f"RemoteAio: NOT AVAILABLE")
        _stopRemoteAio()
    
def _isRemoteAioWorking():
    global _RemoteAioWorking
    return _RemoteAioWorking


def _lookForRemoteAioServers(Port = 3099):
    global _RemoteAioServers, _RemoteAioWorking
    if not _RemoteAioWorking:
        _startRemoteAio(Port)
    _RemoteAioServers = []
    _RemoteAioMessage(_RemoteAioMessages.LOOKING_FOR_SERVERS).sendTo("", Port)
    for i in range(1):
        sleep(1.5)
    print(f"RemoteAio: {len(_RemoteAioServers)} servers found")
    return _RemoteAioServers



class RemoteAio:
    
    Port = 3099
    RefreshEvery = 30
    _LastTimeOfRefresh = -1000
    
    @staticmethod
    def start() -> bool:
        _lookForRemoteAioServers(RemoteAio.Port)
        return _isRemoteAioWorking()
        
    @staticmethod
    def restart() -> bool:
        _lookForRemoteAioServers(RemoteAio.Port)
        return _isRemoteAioWorking()
    
    @staticmethod
    def stop():
        _stopRemoteAio()
        RemoteAio._LastTimeOfRefresh = -1000
    
    @staticmethod
    def refreshServers() -> int:
        _lookForRemoteAioServers(RemoteAio.Port)
        RemoteAio._LastTimeOfRefresh = -1000
        return len(_getRemoteAioServers())
    
    @staticmethod
    def getServerList() -> list:
        return _getRemoteAioServers()
    
    @staticmethod
    def isRunning() -> bool:
        return _isRemoteAioWorking()
    
    @staticmethod
    def getAwaitingJobs(Timeout = 0) -> list:
        global _RemoteAioJobs
        Results = []
        for J in _RemoteAioJobs:
            if J.getAwaitingTime() >= Timeout:
                Results.append(J)
        return Results
    
    @staticmethod
    def requestEval(Code : str):
        if not _isRemoteAioWorking():
            _lookForRemoteAioServers(RemoteAio.Port)
            RemoteAio._LastTimeOfRefresh = time.time()
        else:
            t = time.time() 
            if t - RemoteAio._LastTimeOfRefresh > RemoteAio.RefreshEvery:
                RemoteAio._LastTimeOfRefresh = t
                _lookForRemoteAioServers(RemoteAio.Port)
        if _isRemoteAioWorking():
            Job = _requestRemoteAioEval(Code)
            return Job
        else:
            Aio.printError("RemoteAio is not running!")
            return None
    
    