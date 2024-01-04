from libs.aio import *
import sys

class shell_config:
  header = f"""
{"Maciej Trawka's".center(Aio.getTerminalColumns()>>1)}
{"All-In-One v2".center(Aio.getTerminalColumns()>>1)}
{f'Python: {sys.version}'.center(Aio.getTerminalColumns()>>1)}
"""
  
  def printHeader():
    print(shell_config.header)
  
  def useDC():
    return False
  
  def useQuesta():
    return False
  
  def getCppCompiler():
    return "g++"
  
  def priv():
    return True

