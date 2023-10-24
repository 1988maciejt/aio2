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
    
    
class _RemoteNodes:
    
    __slots__ = ("_LastSeenDict", "_BusyDict")
    
    def __init__(self) -> None:
        self._LastSeenDict = {}
        self._BusyDict = {}
        
    def ping(self, Ip, Port):
        self._BusyDict[(Ip, Port)] = time.time()
        
    def ready(self, Ip, Port):
        self._LastSeenDict[(Ip, Port)] = time.time()
        
    def finishedTask(self, Ip, Port):
        self._BusyDict[Ip, Port] = 0
        self._LastSeenDict[Ip, Port] = 0
        self._BusyDict.pop((Ip, Port))
        self._LastSeenDict.pop((Ip, Port))
    
    def isBusy(self, Ip, Port):
        LastTime = self._BusyDict.get((Ip, Port), -10)
        if time.time() - LastTime <= 5:
            return True
        return False
    
    def isFree(self, Ip, Port):
        if not self.isBusy(Ip, Port):
            LastTime = self._LastSeenDict.get((Ip, Port), -10)
            if time.time() - LastTime <= 5:
                return True
        return False
    
    def getFreeNodes(self) -> list:
        Now = time.time()
        Result = []
        for key in list(self._LastSeenDict.keys()):
            if self.isFree(*key):
                Result.append(key)
        return Result        
    
    def sentTask(self, Ip, Port):
        self._BusyDict[(Ip, Port)] = time.time()
        
    def iterateOverFree(self):
        Now = time.time()
        for key in self.getFreeNodes():
            yield key
    
    
    
class RemoteAioTask:
    
    __slots__ = ("Id", "Code", "Response", "_done", "_Timestamp", "_Locked")
    
    def __init__(self, Id : int, Code : str, DefaultResponse = None) -> None:
        self.Id = Id
        self.Code = Code
        self.Response = DefaultResponse
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
        if time.time() - self._Timestamp < 10:
            return True
        return False



class RemoteAioScheduler:
    
    __slots__ = ("_Verbose", "_Nodes", "_InfoTimeStamp", "_LocalExecution", "_Busy", "_OneTime", "_Port", "_MySender", "_MyMonitor", "_Enable", "TaskList")
    
    def _doLocal(self, Task :  RemoteAioTask):
        while self._OneTime:
            sleep(0.01)  
        self._OneTime = True
        self._Busy = True
        Task.lock()
        if self._Verbose:
            print(Str.color(f"// REMOTE_AIO_SCHEDULER: Starting local execution of task {Task.Id}", 'blue'))
        self._OneTime = False
        try:
            Task.Response = eval(Task.Code)
        except Exception as inst:
            Aio.printError(f"// REMOTE_AIO_SCHEDULER: Error in task {Task.Id}: {inst}")
        Task._done = True
        while self._OneTime:
            sleep(0.01)  
        self._OneTime = True
        if self._Verbose:
            print(Str.color(f"// REMOTE_AIO_SCHEDULER: Finished local execution of task {Task.Id}", 'blue'))
        self._Busy = False
        self._OneTime = False
    
    def _monCbk(self, args):
        while self._OneTime:
            sleep(0.01)     
        self._OneTime = True
        FromIp = args[1]
        FromPort = args[2]
        RawData = args[0]
        Msg = _RemoteAioMessage.fromBytes(RawData)
        if Msg:
            Msg.Ip = FromIp
            Msg.Port = FromPort
            if Msg.Command == _READY_FOR_REQUESTS:
                FromPort = Msg.Data[1]
                self._Nodes.ready(FromIp, FromPort)
            elif Msg.Command == _RESPONSE:
                try:
                    Task = Msg.Data
                    TaskList = self.TaskList.copy()
                    for T in TaskList:
                        if T.Id == Task.Id:
                            if self._Verbose:
                                print(Str.color(f"// REMOTE_AIO_SCHEDULER: Received response {Task.Id} from {FromIp}:{FromPort}", 'yellow'))
                                sleep(0.01)
                            self.TaskList.remove(T)
                            T._done = 1
                            T.Response = Task.Response
                            self._Nodes.finishedTask(FromIp, FromPort)
                            break
                except Exception as inst:
                    Aio.printError(f"// REMOTE_AIO_SCHEDULER: Received broken response from {FromIp}:{FromPort} : {inst}")
            elif Msg.Command == _PING:
                try:
                    Id = Msg.Data[0]
                    FromPort = Msg.Data[1]
                    self._Nodes.ping(FromIp, FromPort)
                    TaskList = self.TaskList.copy()
                    for T in TaskList:
                        if T.Id == Id:
                            T._Timestamp = time.time()
                            break
                except Exception as inst:
                    Aio.printError(f"// REMOTE_AIO_SCHEDULER: _PING: {inst}")
        self._OneTime = False
    
    def _hello(self):
        try:
            while self._Enable:
                while self._OneTime:
                    sleep(0.01)  
                if len(self.TaskList) > 0:
                    _RemoteAioMessage("", self._Port, _NOT_EMPTY_SCHEDULER).send(self._MySender)
                    if time.time() - self._InfoTimeStamp >= 60:
                        if self._Verbose:
                            print(Str.color(f"// REMOTE_AIO_SCHEDULER: Queue: {len(self.TaskList)} tasks", 'green'))
                        self._InfoTimeStamp = time.time()
                for IpPort in self._Nodes.iterateOverFree():
                    Ip = IpPort[0]
                    Port = IpPort[1]
                    TaskList = self.TaskList.copy()
                    for Task in TaskList:
                        if Task.isProcessed():
                            continue
                        _RemoteAioMessage(Ip, Port, _TASK, Task).send(self._MySender)
                        if self._Verbose:
                            print(Str.color(f"// REMOTE_AIO_SCHEDULER: Sent task {Task.Id} to {Ip}:{Port}", 'yellow'))
                        Task._Timestamp = time.time()
                        sleep(0.1)
                        break       
                if self._LocalExecution and not self._Busy:
                    self._OneTime = True   
                    TaskList = self.TaskList.copy()
                    for Task in TaskList:
                        if Task.isProcessed():
                            continue
                        _thread.start_new_thread(self._doLocal, tuple([Task]))  
                        break       
                self._OneTime = False 
                sleep(1)
        except Exception as inst:
            Aio.printError(f"// REMOTE_AIO_SCHEDULER: 'hello' process: {inst}")
    
    def __init__(self, Port = 3099, Enable = True, LocalExecution = False) -> None:
        self._Port = Port
        self._Enable = 0
        self.TaskList = []
        self._MySender = UdpSender(self._Port) 
        self._MyMonitor = UdpMonitor(Port, Callback=self._monCbk, BufferSize=64*1024*1024)
        self._OneTime = False
        self._Busy = False
        self._LocalExecution = LocalExecution
        self._InfoTimeStamp = 0
        self._Verbose = 1
        self._Nodes = _RemoteNodes()
        if Enable:
            self.start()
        
    def __del__(self) -> None:
        self.stop()
        
    def clearTasks(self):
        self.TaskList.clear()
        
    def printAvailableNodes(self) -> None:
        _RemoteAioMessage("", self._Port, _NOT_EMPTY_SCHEDULER).send(self._MySender)
        sleep(1)
        Nodes = self._Nodes.getFreeNodes()
        for Node in Nodes:
            print(f"{Node[0]}:{Node[1]}")
        
    def start(self):
        self._Enable = 1
        self._OneTime = False
        _thread.start_new_thread(self._hello, ())
        self._MyMonitor.start()
        print(f"// REMOTE_AIO_SCHEDULER: Started. My address: {getMyIp()}, port: {self._Port}")
        
    def stop(self):
        self._Enable = 0
        self._OneTime = True
        self._MyMonitor.stop()
        
    def addTask(self, Code : str, DefaultResponse = None) -> RemoteAioTask:
        Task = RemoteAioTask(_randomId(), Code, DefaultResponse)
        self.TaskList.append(Task)
        return Task
    
    def map(self, CodeList, DefaultResponse = None) -> list:
        TaskList = []
        for Code in CodeList:
            TaskList.append(self.addTask(Code, DefaultResponse))
        AllDone = 0
        LastDone = -1
        while not AllDone and len(self.TaskList) > 0:
            sleep(1)
            AllDone = 1
            Done = 0
            for T in TaskList:
                if T:
                    Done += 1
                else:
                    AllDone = 0
            if (LastDone != Done) or AllDone:
                print(Str.color(f"// REMOTE_AIO_SCHEDULER: MAP STATUS: {Done}/{len(TaskList)}", 'green'))
                LastDone = Done
        Results = []
        for T in TaskList:
            Results.append(copy.deepcopy(T.Response))
        TaskList.clear()
        sleep(0.1)
        print(Str.color(f"// REMOTE_AIO_SCHEDULER: MAP FINISHED", 'green'))
        return Results
    
    def mapGenerator(self, CodeList, ShowStatus = False, DefaultResponse = None):
        if ShowStatus:
            self._Verbose = 0
        InfoTimeStamp = 0
        TaskList = []
        for Code in CodeList:
            TaskList.append(self.addTask(Code, DefaultResponse))
        for T in TaskList:
            if len(self.TaskList) == 0:
                break
            while not T:
                if ShowStatus:
                    if time.time() - InfoTimeStamp >= 1:
                        self._printTasksStatus(TaskList)
                        InfoTimeStamp = time.time()
                sleep(0.1)
            yield copy.deepcopy(T.Response)
        TaskList.clear()
        if ShowStatus:
            self._Verbose = 1
            print("\nRemoteAio finished the loop.\n")
    imap = mapGenerator
    
    def mapUnorderedGenerator(self, CodeList, ShowStatus = False, DefaultResponse = None):
        if ShowStatus:
            self._Verbose = 0
        InfoTimeStamp = 0
        TaskList = []
        for Code in CodeList:
            TaskList.append(self.addTask(Code, DefaultResponse))
        if ShowStatus:
            InfoTaskList = TaskList.copy()
        while len(TaskList) > 0:
            if len(self.TaskList) == 0:
                break
            if ShowStatus:
                if time.time() - InfoTimeStamp >= 1:
                    self._printTasksStatus(InfoTaskList)
                    InfoTimeStamp = time.time()
            sleep(0.01)
            for T in TaskList:
                if T:
                    yield copy.deepcopy(T.Response)
                    TaskList.remove(T)
                    break
        TaskList.clear()
        if ShowStatus:
            self._Verbose = 1
            print("\nRemoteAio finished the loop.\n")
    uimap = mapUnorderedGenerator
                
    def _printTasksStatus(self, TaskList):
        Result = "--- RemoteAio mapping status ---\n"
        j = 0
        lcount = 3
        Max = int(Aio.getTerminalColumns() / 8)
        for i in range(len(TaskList)):
            if j == 0:
                Result += "\n"
                lcount += 1
            Task = TaskList[i]
            if Task.isDone():
                Result += Str.color(f"[{i}]\t", 'green')
            elif Task.isProcessed():
                Result += Str.color(f"[{i}]\t", 'yellow')
            else:
                Result += Str.color(f"[{i}]\t", 'black')
            j = (j + 1) % Max
        for _ in range(lcount, Aio.getTerminalRows()):
            Result += "\n"
        print(Result)
        
    
    
    
class RemoteAioNode:
    
    __slots__ = ("_LastChangedCounterTimeStamp", "_CustomServers", "_Port", "_MySender", "_MyMonitor", "_Enable", "_Locked", "_MsgBuffer", "_MyMsg", "_MyCounter", "_LastTaskId", "_LastTaskTime")
    
    def _ping(self):
        while self._Enable:
            t0 = time.time()
            while time.time() - t0 < 1:
                pass
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
        from libs.aio_auto import AioAuto
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
                    if (self._LastTaskId != Id) or (time.time() - self._LastTaskTime > 5):
                        self._LastTaskId = Id
                        for CS in self._CustomServers:
                            if CS[0] == FromIp:
                                FromPort = CS[1]
                                Msg.Port = FromPort
                                break
                        self._MyMsg = _RemoteAioMessage(FromIp, FromPort, _PING, [Id, self._Port])
                        self._Locked = 1
                        print(Str.color(f"// REMOTE_AIO_NODE: Received task {Id} from {FromIp}:{FromPort}", 'yellow'))
                        try:
                            Result = eval(Task.Code)
                        except Exception as inst2:
                            Result = Task.Response # the default one
                            Aio.printError(f"// REMOTE_AIO_NODE: INVALID TASK: {inst2}")
                        #AioAuto.atExit()
                        Task.Code = None
                        Task.Response = Result
                        del self._MyMsg
                        self._MyMsg = None
                        #self._Locked = 9
                        Msg.Command = _RESPONSE
                        Msg.Data = Task
                        Msg.send(self._MySender)
                        print(Str.color(f"// REMOTE_AIO_NODE: Sent response {Id} to {FromIp}:{FromPort}", 'yellow'))
                        sleep(0.1)
                except Exception as inst:
                    Aio.printError(f"// REMOTE_AIO_NODE: {inst}")                
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
        self._LastTaskId = -1
        self._LastTaskTime = -10
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