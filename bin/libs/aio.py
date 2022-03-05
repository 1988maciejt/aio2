import shutil
import copy
import os
import re



class Aio:
  def getTerminalColumns() -> int:
    return shutil.get_terminal_size()[0]
  def getTerminalRows() -> int:
    return shutil.get_terminal_size()[1]
  def printTranscriptEnable():
    global transcript_file
    transcript_file = open("transcript.txt", "w")
  def printTranscriptDisable():
    del transcript_file
  def print(*args):
    if "transcript_file" in globals():
      s = ""
      for arg in args:
        s += str(arg) + " "
      s += "\n"
      transcript_file.write(s)
    print(*args)
  def printError(*args):
    Aio.print("ERROR:",*args)
  def shellExecute(ShellCommand : str) -> str:
    stream = os.popen(ShellCommand)
    return stream.read()
  def numToCompressedString(num : int) -> str:
    result = ""
    n = abs(num)
    while n > 0:
      x = n % 250
      n = n // 250
      result = chr(x+1) + result
    if num < 0:
      result += chr(252)
    return result
  def compressedStringToNum(cstring : str) -> int:
    result = 0
    for c in cstring:
      n = ord(c)
      if n == 252:
        result *= -1
      else:
        result = (result * 250) + (n-1)
    return result

    
class Tc:
  def step(name = "transcript.txt") -> None:
    global tc_step
    if not "tc_step" in globals():
      tc_step = 1
    Aio.print("STEP " + str(tc_step) + ":\t" + name)
  def diff(FileName : str) -> None:
    result = Aio.shellExecute("diff " + FileName + " ../references/" + FileName)
    print(result)