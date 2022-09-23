from libs.aio import *
from libs.files import writeFile

class CppProgram:
  CppFileName = ""
  ExeFileName = ""
  _comp_error = ""
  Compiled = False
  def __init__(self, CppFileName : str, ExeFileName = "", Code = "") -> None:
    self.CppFileName = CppFileName
    if len(Code) > 1:
      writeFile(CppFileName, Code)
    if len(ExeFileName) < 1:
      self.ExeFileName = CppFileName + ".exe"
  def __str__(self) -> str:
    return f'{self.ExeFileName}'
  def __repr__(self) -> str:
    return f'CppProgram({self.CppFileName}, {self.ExeFileName})'
  def compile(self) -> bool:
    Cmd = f'g++ {self.CppFileName} -o {self.ExeFileName}'
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
  def run(self, Args = None) -> str:
    if not self.Compiled:
      self.compile()
    if not self.Compiled:
      return None
    Cmd = self.ExeFileName
    if Aio.isType(Args, []):
      for Arg in Args:
        Cmd += " " + str(Arg)
    elif not Aio.isType(Args, None):
      Cmd += str(Args)
    return Aio.shellExecute(Cmd)