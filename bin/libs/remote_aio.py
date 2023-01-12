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


_NOT_EMPTY_SCHEDULER = "NOT_EMPTY_SCHEDULER"
_READY_FOR_REQUESTS = "READY_FOR_REQUESTS"
_TASK = "TASK"
_RESPONSE = "RESPONSE"


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
        Sender.send(self.toBytes(), self.Ip, self.Port, Repeatitions=Repetitions)
    
    
    
class RemoteAioTask:
    
    __slots__ = ("Id", "Code", "Response", "_done")
    
    def __init__(self, Id : int, Code : str) -> None:
        self.Id = Id
        self.Code = Code
        self.Response = None
        self._done = 0
        
    def __bool__(self) -> bool:
        return bool(self.isDone())
        
    def isDone(self) -> bool:
        return self._done



class RemoteAioScheduler:
    
    __slots__ = ("_Port", "_MySender", "_MyMonitor", "_Enable", "TaskList")
    
    def _monCbk(self, args):
        FromIp = args[1]
        FromPort = args[2]
        RawData = args[0]
        Msg = _RemoteAioMessage.fromBytes(RawData)
        if Msg:
            Msg.Ip = FromIp
            Msg.Port = FromPort
            if Msg.Command == _READY_FOR_REQUESTS:
                #print(f"// REMOTE_AIO_SCHEDULER: {FromIp}:{FromPort} is ready for requests")
                if len(self.TaskList) > 0:
                    Msg.Command = _TASK
                    Task = self.TaskList.pop()
                    Msg.Data = Task
                    Msg.send(self._MySender)
                    self.TaskList.insert(0, Task)
                    print(f"// REMOTE_AIO_SCHEDULER: Sent task {Task.Id} to {FromIp}:{FromPort}")
            elif Msg.Command == _RESPONSE:
                try:
                    Task = Msg.Data
                    for T in self.TaskList:
                        if T.Id == Task.Id:
                            print(f"// REMOTE_AIO_SCHEDULER: Received response {Task.Id} from {FromIp}:{FromPort}")
                            self.TaskList.remove(T)
                            T._done = 1
                            T.Response = Task.Response
                except:
                    print(f"// REMOTE_AIO_SCHEDULER: ERROR: Received broken response from {FromIp}:{FromPort}")
    
    def _hello(self):
        while self._Enable:
            if len(self.TaskList) > 0:
                _RemoteAioMessage("", self._Port, _NOT_EMPTY_SCHEDULER).send(self._MySender)
            sleep(0.5)
    
    def __init__(self, Port = 3099, Enable = True) -> None:
        self._Port = Port
        self._Enable = 0
        self.TaskList = []
        self._MySender = UdpSender(self._Port) 
        self._MyMonitor = UdpMonitor(Port, Callback=self._monCbk, BufferSize=64*1024*1024)
        if Enable:
            self.start()
        
    def __del__(self) -> None:
        self.stop()
        
    def start(self):
        self._Enable = 1
        _thread.start_new_thread(self._hello, ())
        self._MyMonitor.start()
        
    def stop(self):
        self._Enable = 0
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
    
    
    
class RemoteAioNode:
    
    __slots__ = ("_Port", "_MySender", "_MyMonitor", "_Enable", "_Locked", "_MsgBuffer")
    
    def _monCbk(self, args):
        FromIp = args[1]
        FromPort = args[2]
        RawData = args[0]
        Msg = _RemoteAioMessage.fromBytes(RawData)
        if Msg:
            Msg.Ip = FromIp
            Msg.Port = FromPort
            if Msg.Command == _NOT_EMPTY_SCHEDULER:
                print(f"// REMOTE_AIO_NODE: {FromIp}:{FromPort} has not empty queue")
                Msg.Command = _READY_FOR_REQUESTS
                Msg.send(self._MySender)
            elif Msg.Command == _TASK:
                try:
                    Task = Msg.Data
                    Id = Task.Id
                    self._Locked = 1
                    self._MyMonitor.stop()
                    print(f"// REMOTE_AIO_NODE: Received task {Id} from {FromIp}:{FromPort}")
                    try:
                        Result = eval(Task.Code)
                    except Exception as inst2:
                        Result = None
                        print(f"// REMOTE_AIO_NODE: INVALID TASK: {inst2}")
                    Task.Code = None
                    Task.Response = Result
                    Msg.Command = _RESPONSE
                    Msg.Data = Task
                    Msg.send(self._MySender)
                    print(f"// REMOTE_AIO_NODE: Sent response {Id} to {FromIp}:{FromPort}")
                except Exception as inst:
                    print(f"// REMOTE_AIO_NODE: ERROR: {inst}")
                self._Locked = 0
                if self._Enable:
                    self._MyMonitor.start()
                    
    def __init__(self, Port = 3099, Enable = True) -> None:
        self._Port = Port
        self._Enable = 0
        self._Locked = 0
        self._MsgBuffer = []
        self._MySender = UdpSender(self._Port) 
        self._MyMonitor = UdpMonitor(Port, Callback=self._monCbk, BufferSize=64*1024*1024)
        if Enable:
            self.start()
            
    def __del__(self) -> None:
        self.stop()
        
    def start(self):
        self._Enable = 1
        self._MyMonitor.start()
        
    def stop(self):
        self._Enable = 0
        self._MyMonitor.stop()