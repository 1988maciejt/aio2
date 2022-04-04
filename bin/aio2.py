import inspect
from asyncore import ExitNow
import os
import random
import re
import shutil
import sys
import plotext
from libs.aio import *
from libs.ca import *
from libs.cache import *
from libs.cas import *
from libs.database import *
from libs.eseries import *
from libs.files import *
from libs.flags import *
from libs.gcode import *
from libs.lfsr import *
from libs.logic import *
from libs.polynomial import *
from libs.ring_oscillator import *
from libs.stats import *
from libs.unitnumber import *
from libs.utils_array import *
from libs.utils_int import *
from libs.verilog import *


print()
print("Maciej Trawka's".center(Aio.getTerminalColumns()>>1))
print("All-In-One v2".center(Aio.getTerminalColumns()>>1))
print()

if len(sys.argv) > 1:
  os.chdir(sys.argv[1])

if len(sys.argv) > 2:
  SFile = str(sys.argv[2])
  if "driver.py" in SFile:
    shutil.rmtree("results", ignore_errors=True)
    os.makedirs("results")
    Aio.shellExecute("mkdir -p references")
    os.chdir("results")
    Aio.print ("Testcase mode. Output redirected to 'transcript.txt'")
    Aio.printTranscriptEnable()
  if os.path.isfile(SFile):
    exec(open(SFile).read())
  else:
    Aio.printError("No file '" + SFile + "'")



#========================================================
