from numba import cuda
import numpy

@cuda.jit
def cuda_transposeto64(input, output):
  pos = cuda.grid(1)
  bsize = cuda.gridsize(1)
  while pos * 64 < input.size:
    IWordIdx = pos * 64
    Words = output[pos]
    OWMask = numpy.int64(1)
    for i in range(64):
      if IWordIdx >= input.size:
        break
      IWord = input[IWordIdx]
      for j in range(Words.size):
        if IWord & 1:
          Words[j] |= OWMask
        IWord >>= 1
      OWMask <<= 1
      IWordIdx += 1
    pos += bsize
    
#blocks = any,
#threads = number of columns
@cuda.jit
def cuda_onesCount64(input):
  block = cuda.blockIdx.x
  thread = cuda.threadIdx.x
  bsize = 1024
  while block < input.size:
    rlocal = 0
    w = input[block][thread]
    for _ in range(64):
      if w & 1:
        rlocal += 1
      w >>= 1
    input[block][thread] = rlocal
    block += bsize
    
#blocks = any,
#threads = number of columns
@cuda.jit
def cuda_sumColumns64(input):
  block = cuda.blockIdx.x
  thread = cuda.threadIdx.x
  bsize = 1024
  if block == 0:
    for Row in range(1, input.size):
      input[Row][thread] += input[Row-1][thread] 
      
      
      
from libs.cpp_program import *
class CudaCProgram (CppProgram):
  
  def __init__(self, CuFileName : str, *args, **kwargs) -> None:
    self._args = args
    self.HeaderFileNames = []
    self._kwargs = kwargs
    rand = str(int(uniform(100000000, 999999999)))
    self.CppFileName = os.path.abspath(CuFileName)
    self.ExeFileName = os.path.abspath('/tmp/' + os.path.basename(CuFileName) + f'.{rand}.exe')
    self.PreprocessedSourceFileName = os.path.abspath('/tmp/' + os.path.basename(CuFileName) + f'.{rand}.preprocessed.cu')
    
  def __repr__(self) -> str:
    return f'CudaCProgram({self.CppFileName}, {self.ExeFileName})'
  
  def compile(self) -> bool:
    preprocessFile(self.CppFileName, self.PreprocessedSourceFileName, *self._args, **self._kwargs)
    SourceFiles = self.PreprocessedSourceFileName
    for H in self.HeaderFileNames:
      preprocessFile(H+".h", '/tmp/'+os.path.basename(H)+".h", *self._args, **self._kwargs)
      preprocessFile(H+".c", '/tmp/'+os.path.basename(H)+".c", *self._args, **self._kwargs)
      SourceFiles += " " + '/tmp/'+os.path.basename(H)+".c"
    Cmd = f'nvcc {SourceFiles} -o {self.ExeFileName} -std=c++11 -O3'
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