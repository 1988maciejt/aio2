from libs.udp import *
from libs.aio import *
from time import sleep
from tqdm import tqdm
from random import uniform
import netifaces
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


_NOT_EMPTY_SCHEDULER = "NOT_EMPTY_SCHEDULER"
_READY_FOR_REQUESTS = "READY_FOR_REQUESTS"
_TASK = "TASK"
_RESPONSE = "RESPONSE"
_PING = "PING"


def _randomId() -> int:
    return int(uniform(1, 100000000000000000000))

class _NodeDiscarder:
    
    __slots__ = ("_Nodes")
    
    def __init__(self) -> None:
        self._Nodes = {}
        
    def discard(self, Ip, Port, Counter) -> bool:
        Counters = self._Nodes.get((Ip, Port), [])
        if Counter in Counters:
            #print(f"DISCARDED {Ip}:{Port}")
            return True
        return False
    
    def storeCounter(self, Ip, Port, Counter):
        Counters = self._Nodes.get((Ip, Port), [])
        if len(Counters) > 16:
            Counters.pop()
        Counters.insert(0, Counter)
        self._Nodes[(Ip, Port)] = Counters
    
    
    

class _RemoteAioMessage:
    
    __slots__ = ("Ip", "Port", "Command", "Data")
    
    def __init__(self, Ip : str, Port : int, Command : str, Data = None) -> None:
        self.Ip = Ip
        self.Port = Port
        self.Command = Command
        self.Data = Data
        
    def __bool__(self) -> bool:
        return True
    
    def __str__(self) -> str:
        return f"MESSAGE from {self.Ip}:{self.Port} - {self.Command}"
        
    @staticmethod
    def fromBytes(RawData : bytes):
        try:
            M = pickle.loads(RawData)
            if Aio.isType(M, "_RemoteAioMessage"):
                return M
        except:
            pass
        return None    
    
    def toBytes(self):
        return pickle.dumps(self)
    
    def send(self, Sender : UdpSender, Repetitions=1):
        #print(f"DEBUG: Sent {self.Command} to {self.Ip}:{self.Port}")
        Sender.send(self.toBytes(), self.Ip, self.Port, Repeatitions=Repetitions)
    
    
    
class RemoteAioTask:
    
    __slots__ = ("Id", "Code", "Response", "_done", "_Timestamp", "_Locked")
    
    def __init__(self, Id : int, Code : str) -> None:
        self.Id = Id
        self.Code = Code
        self.Response = None
        self._done = 0
        self._Timestamp = 0
        self._Locked = 0
        
    def __bool__(self) -> bool:
        return bool(self.isDone())
        
    def lock(self):
        self._Locked = 1
    
    def unlock(self):
        self._Locked = 0
        
    def isDone(self) -> bool:
        return self._done
    
    def isProcessed(self) -> bool:
        if self._Locked:
            return True
        if time.time() - self._Timestamp > 1.5:
            return False
        return True



class RemoteAioScheduler:
    
    __slots__ = ("_LocalExecution", "_Busy", "_OneTime", "_Port", "_MySender", "_MyMonitor", "_Enable", "TaskList", "_Servers")
    
    def _doLocal(self, Task :  RemoteAioTask):
        if self._Busy:
            return
        self._Busy = True
        Task.lock()
        try:
            Task.Response = eval(Task.Code)
        except Exception as inst:
            Aio.printError(f"// REMOTE_AIO_SCHEDULER: Error in task {Task.Id}: {inst}")
        Task._done = True
        self._Busy = False
    
    def _monCbk(self, args):
        while self._OneTime:
            sleep(0.01)
        if Aio.isType(args, ""):
            if args == _READY_FOR_REQUESTS:
                for i in range(len(self.TaskList)):
                    Task = self.TaskList.pop()
                    if Task.isProcessed():
                        self.TaskList.insert(0, Task)
                        continue
                    self._doLocal(Task)
                    self.TaskList.insert(0, Task)                
        self._OneTime = True
        FromIp = args[1]
        FromPort = args[2]
        RawData = args[0]
        Msg = _RemoteAioMessage.fromBytes(RawData)
        if Msg:
            Msg.Ip = FromIp
            Msg.Port = FromPort
            if Msg.Command == _READY_FOR_REQUESTS:
                #print(f"// REMOTE_AIO_SCHEDULER: {FromIp}:{FromPort} is ready for requests")
                Counter = Msg.Data[0]
                FromPort = Msg.Data[1]
                Msg.Port = Msg.Data[1]
                if not self._Servers.discard(FromIp, FromPort, Counter):
                    for i in range(len(self.TaskList)):
                        Task = self.TaskList.pop()
                        if Task.isProcessed():
                            self.TaskList.insert(0, Task)
                            continue
                        Msg.Command = _TASK
                        Msg.Data = Task
                        Msg.send(self._MySender)
                        self.TaskList.insert(0, Task)
                        self._Servers.storeCounter(FromIp, FromPort, Counter)
                        print(f"// REMOTE_AIO_SCHEDULER: Sent task {Task.Id} to {FromIp}:{FromPort}")
                        break
            elif Msg.Command == _RESPONSE:
                try:
                    Task = Msg.Data
                    for T in self.TaskList:
                        if T.Id == Task.Id:
                            print(f"// REMOTE_AIO_SCHEDULER: Received response {Task.Id} from {FromIp}:{FromPort}")
                            self.TaskList.remove(T)
                            T._done = 1
                            T.Response = Task.Response
                            break
                except:
                    print(f"// REMOTE_AIO_SCHEDULER: ERROR: Received broken response from {FromIp}:{FromPort}")
            elif Msg.Command == _PING:
                try:
                    Id = Msg.Data
                    for T in self.TaskList:
                        if T.Id == Id:
                            T._Timestamp = time.time()
                            break
                except Exception as inst:
                    print(f"// REMOTE_AIO_SCHEDULER: ERROR in _PING: {inst}")
        self._OneTime = False
    
    def _hello(self):
        while self._Enable:
            if len(self.TaskList) > 0:
                _RemoteAioMessage("", self._Port, _NOT_EMPTY_SCHEDULER).send(self._MySender)
            if self._LocalExecution and not self._Busy:
                self._monCbk(_READY_FOR_REQUESTS)        
            sleep(0.5)
    
    def __init__(self, Port = 3099, Enable = True, LocalExecution = True) -> None:
        self._Port = Port
        self._Enable = 0
        self.TaskList = []
        self._MySender = UdpSender(self._Port) 
        self._MyMonitor = UdpMonitor(Port, Callback=self._monCbk, BufferSize=64*1024*1024)
        self._Servers = _NodeDiscarder()
        self._OneTime = False
        self._Busy = False
        self._LocalExecution = LocalExecution
        if Enable:
            self.start()
        
    def __del__(self) -> None:
        self.stop()
        
    def start(self):
        self._Enable = 1
        self._OneTime = False
        _thread.start_new_thread(self._hello, ())
        self._MyMonitor.start()
        
    def stop(self):
        self._Enable = 0
        self._OneTime = True
        self._MyMonitor.stop()
        
    def addTask(self, Code : str) -> RemoteAioTask:
        Task = RemoteAioTask(_randomId(), Code)
        self.TaskList.insert(0, Task)
        return Task
    
    def map(self, CodeList) -> list:
        TaskList = []
        for Code in CodeList:
            TaskList.append(self.addTask(Code))
        AllDone = 0
        LastDone = -1
        while not AllDone:
            sleep(1)
            AllDone = 1
            Done = 0
            for T in TaskList:
                if T:
                    Done += 1
                else:
                    AllDone = 0
            if (LastDone != Done) or AllDone:
                print(f"// REMOTE_AIO_SCHEDULER: MAP STATUS: {Done}/{len(TaskList)}")
                LastDone = Done
        Results = []
        for T in TaskList:
            Results.append(copy.deepcopy(T.Response))
        TaskList.clear()
        sleep(0.1)
        print(f"// REMOTE_AIO_SCHEDULER: MAP FINISHED")
        return Results
    
    def mapGenerator(self, CodeList):
        TaskList = []
        for Code in CodeList:
            TaskList.append(self.addTask(Code))
        for T in TaskList:
            while not T:
                sleep(0.1)
            yield copy.deepcopy(T.Response)
        TaskList.clear()
    
    def mapUnorderedGenerator(self, CodeList):
        TaskList = []
        for Code in CodeList:
            TaskList.append(self.addTask(Code))
        while len(TaskList) > 0:
            sleep(0.01)
            for T in TaskList:
                if T:
                    yield copy.deepcopy(T.Response)
                    TaskList.remove(T)
                    break
        TaskList.clear()
                
        
    
    
    
class RemoteAioNode:
    
    __slots__ = ("_LastChangedCounterTimeStamp", "_CustomServers", "_Port", "_MySender", "_MyMonitor", "_Enable", "_Locked", "_MsgBuffer", "_MyMsg", "_MyCounter")
    
    def _ping(self):
        while self._Enable:
            sleep(0.4)
            if self._Locked and (self._MyMsg is not None):
                self._MyMsg.send(self._MySender)
            if not self._Locked:
                for CS in self._CustomServers:
                    try:
                        _RemoteAioMessage(CS[0], CS[1], _READY_FOR_REQUESTS, [self._MyCounter, self._Port]).send(self._MySender)
                    except:
                        Aio.printError(f"RemoteAioNode: problem with Custom Server {CS}")
                if time.time() - self._LastChangedCounterTimeStamp > 5:
                    self._MyCounter = _randomId()
                    self._LastChangedCounterTimeStamp = time.time()
    
    def _monCbk(self, args):
        if self._Locked:
            return
        FromIp = args[1]
        FromPort = args[2]
        RawData = args[0]
        Msg = _RemoteAioMessage.fromBytes(RawData)
        if Msg:
            Msg.Ip = FromIp
            Msg.Port = FromPort
            if Msg.Command == _NOT_EMPTY_SCHEDULER:
                NotFound = 1
                for CS in self._CustomServers:
                    if CS[0] == FromIp and CS[1] == FromPort:
                        NotFound = 0
                        break
                if NotFound:
                    #print(f"// REMOTE_AIO_NODE: {FromIp}:{FromPort} has not empty queue")
                    Msg.Command = _READY_FOR_REQUESTS
                    Msg.Data = [self._MyCounter, self._Port]
                    sleep(uniform(0.05, 0.2))
                    Msg.send(self._MySender)
            elif Msg.Command == _TASK:
                try:
                    #self._MyMonitor.stop()
                    Task = Msg.Data
                    Id = Task.Id
                    for CS in self._CustomServers:
                        if CS[0] == FromIp:
                            FromPort = CS[1]
                            Msg.Port = FromPort
                            break
                    self._MyMsg = _RemoteAioMessage(FromIp, FromPort, _PING, Id)
                    self._Locked = 1
                    print(f"// REMOTE_AIO_NODE: Received task {Id} from {FromIp}:{FromPort}")
                    try:
                        Result = eval(Task.Code)
                    except Exception as inst2:
                        Result = None
                        print(f"// REMOTE_AIO_NODE: INVALID TASK: {inst2}")
                    Task.Code = None
                    Task.Response = Result
                    del self._MyMsg
                    self._MyMsg = None
                    self._Locked = 9
                    Msg.Command = _RESPONSE
                    Msg.Data = Task
                    Msg.send(self._MySender)
                    print(f"// REMOTE_AIO_NODE: Sent response {Id} to {FromIp}:{FromPort}")
                except Exception as inst:
                    print(f"// REMOTE_AIO_NODE: ERROR: {inst}")                
                self._MyCounter = _randomId()
                self._LastChangedCounterTimeStamp = time.time()
                self._Locked = 0
                self._MyMsg = None
                #if self._Enable:
                #    self._MyMonitor.start()
                    
    def __init__(self, Port = 3099, CustomServers = [], Enable = True) -> None:
        self._Port = Port
        self._Enable = 0
        self._Locked = 0
        self._MsgBuffer = []
        self._MyMsg = None
        self._MyCounter = _randomId()
        self._LastChangedCounterTimeStamp = time.time()
        self._MySender = UdpSender(self._Port) 
        self._CustomServers = []
        for CS in CustomServers:
            try:
                if Aio.isType(CS, []) or Aio.isType(CS, ()):
                    self.addCustomServer(CS[0], CS[1])
                else:
                    self.addCustomServer(CS, self._Port)
            except Exception as inst:
                Aio.printError(f"RemoteAioNode - invalid custom server {CS}: {inst}")
        self._MyMonitor = UdpMonitor(Port, Callback=self._monCbk, BufferSize=64*1024*1024)
        if Enable:
            self.start()
            
    def __del__(self) -> None:
        self.stop()
        
    def start(self):
        self._Enable = 1
        _thread.start_new_thread(self._ping, ())
        self._MyMonitor.start()
        
    def stop(self):
        self._Enable = 0
        self._MyMonitor.stop()
        
    def addCustomServer(self, Ip : str, Port : int):
        self._CustomServers.append((Ip, Port))