import subprocess
from libs.aio import *
import os

class Nist:
  def sp800_22_execute(FileName : str) -> str:
    try:
      
      #result = Aio.shellExecute("python3 ~/nist/sp800_22_tests/sp800_22_tests.py " + str(os.path.abspath(FileName)))
      result = subprocess.run(["python3", os.path.expanduser("~/nist/sp800_22_tests/sp800_22_tests.py"), os.path.abspath(FileName)])
      return result
    except:
      Aio.printError("No SP800-22 test suite installed. Install using the script from aio2/utils/nist.")
  def sp800_90b_execute(FileName : str, iid = True) -> str:
    try:
      if iid:
        #result = Aio.shellExecute("~/nist/SP800-90B_EntropyAssessment/cpp/ea_iid " + str(os.path.abspath(FileName))
        result = subprocess.run([os.path.expanduser("~/nist/SP800-90B_EntropyAssessment/cpp/ea_iid"), os.path.abspath(FileName)])
      else:
        #result = Aio.shellExecute("~/nist/SP800-90B_EntropyAssessment/cpp/ea_non_iid " + str(os.path.abspath(FileName)))
        result = subprocess.run([os.path.expanduser("~/nist/SP800-90B_EntropyAssessment/cpp/ea_non_iid"), os.path.abspath(FileName)])
      return result
    except:
      Aio.printError("No SP800-90b test suite installed. Install using the script from aio2/utils/nist.")
