from asyncore import ExitNow
import os
import random
import shutil
import sys
from libs.database import *
from libs.files import *
from libs.lfsr import *
from libs.polynomial import *
from libs.printing import *
from libs.utils_array import *
from libs.utils_int import *

def getTerminalColumns():
  return shutil.get_terminal_size()[0]

def getTerminalRows():
  return shutil.get_terminal_size()[1]

print()
print("Maciej Trawka's".center(getTerminalColumns()>>1))
print("All-In-One v2".center(getTerminalColumns()>>1))
print()

if len(sys.argv) > 1:
  SFile = str(sys.argv[1])
  if "driver.py" in SFile:
    os.removedirs("results")
    os.makedirs("results")
    os.chdir("results")
  if os.path.isfile(SFile):
    exec(open(SFile).read())
  else:
    print_error("No file '" + SFile + "'")
