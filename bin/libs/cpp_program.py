from libs.aio import *
from random import uniform
import os
from libs.preprocessor import *

class CppProgram:
  CppFileName = ""
  ExeFileName = ""
  PreprocessedSourceFileName = ""
  _comp_error = ""
  _args = ()
  _kwargs = {}
  Compiled = False
  def __init__(self, CppFileName : str, *args, **kwargs) -> None:
    self._args = args
    self._kwargs = kwargs
    rand = str(int(uniform(100000000, 999999999)))
    self.CppFileName = os.path.abspath(CppFileName)
    self.ExeFileName = os.path.abspath(os.path.basename(CppFileName) + f'.{rand}.exe')
    self.PreprocessedSourceFileName = os.path.abspath(os.path.basename(CppFileName) + f'.{rand}.preprocessed.cpp')
  def __str__(self) -> str:
    return f'{self.ExeFileName}'
  def __repr__(self) -> str:
    return f'CppProgram({self.CppFileName}, {self.ExeFileName})'
  def compile(self) -> bool:
    preprocessFile(self.CppFileName, self.PreprocessedSourceFileName, *self._args, **self._kwargs)
    Cmd = f'g++ {self.PreprocessedSourceFileName} -o {self.ExeFileName}'
    Result = Aio.shellExecute(Cmd)
    if len(Result) > 2:
      self._comp_error = Result
      self.Compiled = False
    else:
      self._comp_error = ""
      self.Compiled = True
    return self.Compiled
  def isCompiled(self) -> bool:
    return self.Compiled
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