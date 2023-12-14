from libs.aio import *
from random import uniform
import os
from libs.preprocessor import *
from aio_config import *

class CppProgram:
  CppFileName = ""
  ExeFileName = ""
  PreprocessedSourceFileName = ""
  _comp_error = ""
  _args = ()
  _kwargs = {}
  Compiled = False
  HeaderFileNames = []
  def __init__(self, CppFileName : str, *args, **kwargs) -> None:
    self._args = args
    self.HeaderFileNames = []
    self._kwargs = kwargs
    rand = str(int(uniform(100000000, 999999999)))
    self.CppFileName = os.path.abspath(CppFileName)
    self.ExeFileName = os.path.abspath('/tmp/' + os.path.basename(CppFileName) + f'.{rand}.exe')
    self.PreprocessedSourceFileName = os.path.abspath('/tmp/' + os.path.basename(CppFileName) + f'.{rand}.preprocessed.cpp')
  def __str__(self) -> str:
    return f'{self.ExeFileName}'
  def __repr__(self) -> str:
    return f'CppProgram({self.CppFileName}, {self.ExeFileName})'
  def setKwarg(self, Kwarg, Value):
    if self._kwargs.get(Kwarg, None) != Value:
      self.Compiled = False
      self._kwargs[Kwarg] = Value
  def getKwarg(self, Kwarg, DefaultValue):
    return self._kwargs.get(Kwarg, DefaultValue)
  def getExePath(self) -> str:
    if not self.Compiled:
      self.compile()
    return self.ExeFileName
  def compile(self) -> bool:
    preprocessFile(self.CppFileName, self.PreprocessedSourceFileName, *self._args, **self._kwargs)
    SourceFiles = self.PreprocessedSourceFileName
    for H in self.HeaderFileNames:
      preprocessFile(H+".h", '/tmp/'+os.path.basename(H)+".h", *self._args, **self._kwargs)
      preprocessFile(H+".cpp", '/tmp/'+os.path.basename(H)+".cpp", *self._args, **self._kwargs)
      SourceFiles += " " + '/tmp/'+os.path.basename(H)+".cpp"
    Cmd = f'{shell_config.getCppCompiler()} {SourceFiles} -o {self.ExeFileName} -std=c++11 -O3'
    Result = Aio.shellExecute(Cmd, StdErr=True)
    if len(Result) > 5:
      self._comp_error = Result
      self.Compiled = False
      Aio.print(Result)
      Aio.print('Command for debugging:\n  ', Cmd)
    else:
      self._comp_error = ""
      self.Compiled = True
    return self.Compiled
  def isCompiled(self) -> bool:
    return bool(self.Compiled)
  def run(self, *args) -> str:
    if not self.Compiled:
      self.compile()
    if not self.Compiled:
      return None
    Cmd = self.ExeFileName
    for Arg in args:
      Cmd += " " + str(Arg)
    return Aio.shellExecute(Cmd)
  def redefinePreprocessingArgs(self, *args, **kwargs):
    self._args = args
    self._kwargs = kwargs
    self.Compiled = False
  def addHeader(self, FileName):
    """Give FileName without extension.
    
    Compiler expect two files: 
    <FileName>.h
    <FileName>.cpp
    """
    self.HeaderFileNames.append(os.path.abspath(FileName))
    
class CppPrograms:
  _ready = 0
  NLSFRPeriodCounter = CppProgram('junk')
  NLSFRPeriodCounterInvertersAllowed = CppProgram('junk')
  NLSFRPeriodCounterInvertersAllowed64b = CppProgram('junk')
  NLSFRGetSequence64b = CppProgram('junk')
  def debug(State = True):
    for F in [CppPrograms.NLSFRPeriodCounter,
              CppPrograms.NLSFRPeriodCounterInvertersAllowed,
              CppPrograms.NLSFRPeriodCounterInvertersAllowed64b,
              CppPrograms.NLSFRGetSequence64b]:
      F.setKwarg('debug', State)
        
  

if not CppPrograms._ready:
  CppPrograms._ready = 1
  CppPrograms.NLSFRPeriodCounter = CppProgram(Aio.getPath() + 'cpp/non_linear_ring_generator_period_counter.cpp')
  CppPrograms.NLSFRPeriodCounter.addHeader(Aio.getPath() + 'cpp/libs/string_split')
  CppPrograms.NLSFRPeriodCounterInvertersAllowed = CppProgram(Aio.getPath() + 'cpp/non_linear_ring_generator_period_counter.cpp', inverters=1)
  CppPrograms.NLSFRPeriodCounterInvertersAllowed.addHeader(Aio.getPath() + 'cpp/libs/string_split')
  CppPrograms.NLSFRPeriodCounterInvertersAllowed64b = CppProgram(Aio.getPath() + 'cpp/non_linear_ring_generator_period_counter_64b.cpp', inverters=1)
  CppPrograms.NLSFRPeriodCounterInvertersAllowed64b.addHeader(Aio.getPath() + 'cpp/libs/string_split')
  CppPrograms.NLSFRGetSequence64b = CppProgram(Aio.getPath() + 'cpp/non_linear_ring_generator_sequence_64b.cpp', inverters=1)
  CppPrograms.NLSFRGetSequence64b.addHeader(Aio.getPath() + 'cpp/libs/string_split')