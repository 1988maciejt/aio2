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