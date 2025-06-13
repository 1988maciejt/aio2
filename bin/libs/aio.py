import shutil
import os
import re
import pickle
from libs.files import getAioPath, readFile
from ansi2html import *
import time
from libs.utils_str import *
from prompt_toolkit.shortcuts import *
import subprocess
import shlex

class Aio:
  _transcript = "" 
  _sections = False
  _section_opened = False
  _subsection_opened = False
  
  @staticmethod
  def printListing(FileName : str):
    Data = readFile(FileName)
    LNum = 1
    for Line in Data.split("\n"):
      Aio.print(f"{LNum}\t|{Line}")
      LNum += 1
  
  @staticmethod
  def getCpuCount() -> int:
    from multiprocessing import cpu_count
    return cpu_count()
  
  @staticmethod
  def getRamSizeGB() -> int:
    try:
      import psutil
      return (psutil.virtual_memory()[0] >> 30)
    except:
      return 4
      
  @staticmethod
  def getRamSize() -> int:
    try:
      import psutil
      return psutil.virtual_memory()[0]
    except:
      return 4000000
  def isType(Object, ItsType) -> bool:
    if "<class 'str'>" not in str(type(ItsType)):
      ItsType = str(type(ItsType))
    return ItsType in str(type(Object))
  def format(object, indent=0, Repr=False) -> str:
    result = ""
    if "list" in str(type(object)):
      result += " "*indent + "[\n"
      for i in object:
        result += Aio.format(i, indent+2, Repr)
      result += " "*indent + "]\n"
    elif "dict" in str(type(object)):
      result += " "*indent + "{\n"
      for key in object.keys():
        if Repr:
          result += " "*indent + "  " + repr(key) + ":\n"
        else:
          result += " "*indent + "  " + str(key) + ":\n"
        result += Aio.format(object[key], indent+4, Repr)
      result += " "*indent + "}\n"
    else: 
      if Repr:
        result = " "*indent + repr(object) + "\n"
      else:
        result = " "*indent + str(object) + "\n"
    return result
  @staticmethod
  def getTerminalColumns() -> int:
    return shutil.get_terminal_size()[0]
  @staticmethod
  def getTerminalRows() -> int:
    return shutil.get_terminal_size()[1]
  @staticmethod
  def getPath() -> str:
    return getAioPath()
  @staticmethod
  def printTranscriptEnable(FileName = "transcript.txt"):
    global transcript_file
    Aio._transcript = ""
    transcript_file = open(FileName, "w")
  @staticmethod
  def printTranscriptDisable():
    Aio._transcript = ""
    del transcript_file
  @staticmethod
  def transcriptToHTML(FileName = "transcript.html", Dark=True, WrapLines=False, Linkify=True):
    conv = Ansi2HTMLConverter(escaped=False, dark_bg=Dark, title="transcript", line_wrap=WrapLines, linkify=Linkify)
    text = Aio._transcript    
    if Aio._subsection_opened:
      text += "</div>"    
    if Aio._section_opened:
      text += "</div>"
    if Aio._sections:
      text += """
        <script>
        var coll = document.getElementsByClassName("collapsible");
        var collsub = document.getElementsByClassName("collapsiblesub");
        var i;

        for (i = 0; i < coll.length; i++) {
          coll[i].addEventListener("click", function() {
            this.classList.toggle("active");
            var content = this.nextElementSibling;
            if (content.style.display === "block") {
              content.style.display = "none";
            } else {
              content.style.display = "block";
            }
          });
        }
        for (i = 0; i < collsub.length; i++) {
          collsub[i].addEventListener("click", function() {
            this.classList.toggle("active");
            var content = this.nextElementSibling;
            if (content.style.display === "block") {
              content.style.display = "none";
            } else {
              content.style.display = "block";
            }
          });
        }
        </script>
      """
    html = conv.convert(text)
    html = re.sub(r'(\.ansi2html-content\s+)(\{)', '\g<1>{ font-family: "Lucida Console", Cascadia, Consolas, Monospace;', html)
    html = re.sub(r'(\*\s+)(\{)', '\g<1>{ font-family: "Lucida Console", Cascadia, Consolas, Monospace;', html)
    HtmlFile = open(FileName, "w")
    HtmlFile.write(html)
    HtmlFile.close()
  @staticmethod
  def resetTranscript():
    Aio._transcript = ""    
    Aio._sections = False
    Aio._section_opened = False
    Aio._subsection_opened = False
  @staticmethod
  def isTranscriptMode() -> bool:
    return "transcript_file" in globals()
  
  @staticmethod
  def printExcludingTerminal(*args):
    s = ""
    for arg in args:
      s += str(arg) + " "
    s += "\n"
    Aio._transcript += s
    if "transcript_file" in globals():
      Text = Str.removeEscapeCodes(s)
      #Text = re.sub(r'(\033\[[0-9]+m)', '', s)
      transcript_file.write(Text)
      transcript_file.flush()
      os.fsync(transcript_file.fileno())
  
  @staticmethod
  def print(*args):
    s = ""
    for arg in args:
      s += str(arg) + " "
    s += "\n"
    Aio._transcript += s
    if "transcript_file" in globals():
      Text = Str.removeEscapeCodes(s)
      #Text = re.sub(r'(\033\[[0-9]+m)', '', s)
      transcript_file.write(Text)
      transcript_file.flush()
      os.fsync(transcript_file.fileno())
    print(*args)
    
  @staticmethod
  def _add_collapsing_css():
    if not Aio._sections:
      Aio._sections = True
      Aio._transcript += """
        <style>
        .collapsible {
          background-color: #9999;
          color: white;
          cursor: pointer;
          padding: 12px;
          width: 100%;
          border: "solid";
          text-align: left;
          outline: none;
					font-size: 90%
        }
        .collapsiblesub {
          background-color: #AAAA;
          color: white;
          cursor: pointer;
          padding: 7px;
          width: 98%;
          border: none;
          text-align: left;
          outline: none;
					font-size: 100%;
					margin-left:1%;
					margin-top:3px;
					margin-bottom:3px
        }
        .active, .collapsible:hover {
          background-color: #555;
        }
        .active, .collapsiblesub:hover {
          background-color: #555;
        }
        .content {
          display: none;
          overflow: hidden;
					outline: dotted;
					margin-left:1%;
					margin-right:1%;
					margin-top:10px;
					margin-bottom:10px
        }      
        </style>
      """
  @staticmethod
  def printSection(*args):
    s = ""
    for arg in args:
      s += str(arg) + " "
    Aio.transcriptSectionBegin(s)
  @staticmethod
  def printSubsection(*args):
    s = ""
    for arg in args:
      s += str(arg) + " "
    Aio.transcriptSubsectionBegin(s)
  @staticmethod
  def transcriptSectionBegin(SectionName : str):
    Aio._add_collapsing_css()
    s = "=" * Aio.getTerminalColumns()
    s = "\n" + s + "\n" + str(SectionName) + "\n" + s + "\n"
    if Aio._subsection_opened:
      Aio.transcriptSubsectionEnd()
    if Aio._section_opened:
      Aio.transcriptSectionEnd()
    print(s)
    if "transcript_file" in globals():
      transcript_file.write(s)
      transcript_file.flush()
      os.fsync(transcript_file.fileno())
    Aio._transcript += '\n<button type="button" class="collapsible">' + str(SectionName) + '</button><div class="content">\n' 
    Aio._section_opened = True
  @staticmethod
  def transcriptSubsectionBegin(SectionName : str):
    Aio._add_collapsing_css()
    s = "-" * len(str(SectionName))
    s = "\n" + s + "\n" + str(SectionName) + "\n" + s + "\n"
    if Aio._subsection_opened:
      Aio.transcriptSubsectionEnd()
    print(s)
    if "transcript_file" in globals():
      transcript_file.write(s)
      transcript_file.flush()
      os.fsync(transcript_file.fileno())
    Aio._transcript += '\n<button type="button" class="collapsiblesub">' + str(SectionName) + '</button><div class="content">\n' 
    Aio._subsection_opened = True
  @staticmethod
  def transcriptSectionEnd():
    Aio._transcript += '</div>\n' 
    Aio._section_opened = False
    print("")    
    if "transcript_file" in globals():
      transcript_file.write("\n")
      transcript_file.flush()
      os.fsync(transcript_file.fileno())
  @staticmethod
  def transcriptSubsectionEnd():
    Aio._transcript += '</div>\n' 
    Aio._subsection_opened = False
    print("")
    if "transcript_file" in globals():
      transcript_file.write("\n")
      transcript_file.flush()
      os.fsync(transcript_file.fileno())
  @staticmethod
  def printError(*args):
    Aio.print(Str.color("ERROR:", 'red'),*args)
  @staticmethod
  def printTemp(*args):
    if len(args) == 0:
      print(" " * (Aio.getTerminalColumns()-1) + "\r", end="")
    else:
      wl = Aio.getTerminalColumns()
      txt = ""
      for arg in args:
        txt += str(arg) + " "
      if len(txt) > (wl-1):
        txt = txt[0:wl-2]
      txt += "\r"
      print(txt,end="")
      
  @staticmethod
  def advancedShellExecute(ShellCommand : str, PrintDynamically : bool = True, ReturnCapturedOutput = True, ReturnExitCode = False):
    import subprocess
    process = subprocess.Popen(ShellCommand, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    captured_output = ""
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            if PrintDynamically:
              Aio.print(output.strip())
            captured_output += output
    exit_code = process.poll()
    if ReturnCapturedOutput and ReturnExitCode:
      return captured_output, exit_code
    if ReturnCapturedOutput:
      return captured_output
    if ReturnExitCode:
      return exit_code
    return None

  @staticmethod
  def shellExecute(ShellCommand : str, StdOut = True, StdErr = False) -> str:
    from subprocess import PIPE, Popen
    p = Popen(ShellCommand, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    Result = ""
    if StdOut:
      Result += stdout.decode('utf-8')
      if StdErr:
        Result += "\n"
    if StdErr:
      Result += stderr.decode('utf-8')
    return Result
  
  @staticmethod
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
  
  @staticmethod
  def compressedStringToNum(cstring : str) -> int:
    result = 0
    for c in cstring:
      n = ord(c)
      if n == 252:
        result *= -1
      else:
        result = (result * 250) + (n-1)
    return result
  
  @staticmethod
  def timeItCode(Code : str, Iterations = 1):
    SCode = ""
    for Line in Code.split("\n"):
      SCode += "  " + Line + "\n"
    TCode = f'dt = 0\nfor i in range({str(Iterations)}):\n  t0 = time.time()\n{SCode}\n  dt += time.time() - t0\nprint(dt/{str(Iterations)},"s")'
    return compile(TCode, 'dummy', 'exec')
  
  @staticmethod
  def msgBox(Title : str, Text : str, YesNo = False):
    if YesNo:
      return yes_no_dialog(title=str(Title), text=str(Text)).run()
    else:
      message_dialog(title=str(Title), text=str(Text)).run()
    return None
  
  @staticmethod
  def inputBox(Title : str, Text : str, Default = "", Password = False):
    return input_dialog(title=str(Title), text=str(Text), password=bool(Password), default=str(Default)).run()
  
  @staticmethod
  def chooseBox(Title : str, Text : str, Values : list, Default : int = 0) -> int:
    vals = [(i, str(v)) for i,v in enumerate(Values)]
    return radiolist_dialog(title=str(Title), text=str(Text), values=vals, default=int(Default)).run()
    
class Tc:
  def step(name = "transcript.txt") -> None:
    global tc_step
    if not "tc_step" in globals():
      tc_step = 1
    Aio.print("STEP " + str(tc_step) + ":\t" + name)
  def diff(FileName : str) -> None:
    result = Aio.shellExecute("diff " + FileName + " ../references/" + FileName)
    print(result)
    

class AioShell:
  
  _bool_cache = {}
  _int_cache = {}
  _float_cache = {}
  
  @staticmethod
  def getWidth() -> int:
    return Aio.getTerminalColumns()
  
  @staticmethod
  def getHeight() -> int:
    return Aio.getTerminalRows()
  
  @staticmethod
  def removeLastLine():
    print()
    print("\033[F" + " " * Aio.getTerminalColumns()+ "\033[F")
    print("\033[F" + " " * Aio.getTerminalColumns()+ "\033[F")
  
  @staticmethod
  def input(Prompt : str, Default : str = None, AcceptableTypes : list = None, ForceAnswer = True):
    P = Prompt 
    if Default is not None:
      P += f" (Default: {Default})"
    P += " : "
    Res = input(P)
    if Res == "" and Default is not None:
      Res = Default
    Iterables = [tuple, list, set]
    if AcceptableTypes is not None:
      while 1:
        for T in AcceptableTypes:
          if T in Iterables:
            Aux = eval(Res)
            if type(Aux) not in Iterables:
              Aux = tuple([Aux])
            try:
              return T(Aux)
            except:
              pass
          elif T is bool:
            Aux = Res.lower()
            Aux.strip()
            if len(Aux) > 0:
              if Aux[0] in ["1", "t", "y"]:
                return True
              elif Aux[0] in ["0", "f", "n"]:
                return False
          else:
            try:
              return T(eval(Res))
            except:
              pass
        if ForceAnswer:
          AioShell.removeLastLine()
          Res = input(P)
        else:
          return None
    return Res
  
  @staticmethod
  def inputYN(Prompt : str, Default : bool = None, UseCache = True):
    if UseCache:
      Cached = AioShell._bool_cache.get(Prompt, None)
      if Cached is not None:
        Default = Cached
    if Default is not None:
      Default = bool(Default)
      DefStr = "Yes" if Default else "No"
    else:
      DefStr = None
    Res = None
    while Res is None:
      Res = AioShell.input(Prompt + " [Y|N]", DefStr, [bool], ForceAnswer=False)
      if Res is None and Default is not None:
        return Default
      if Res is None:
        AioShell.removeLastLine()
    if UseCache:
      AioShell._bool_cache[Prompt] = Res
    return Res    
  inputBool = inputYN
  
  @staticmethod
  def inputInt(Prompt : str, Default : int = None, Min : int = None, Max : int = None, UseCache = True):
    if UseCache:
      Cached = AioShell._int_cache.get(Prompt, None)
      if Cached is not None:
        Default = Cached
    if Default is not None:
      Default = int(Default)
      DefStr = str(Default)
    else:
      DefStr = None
    Res = None
    MinMax = ""
    if Min is not None and Max is not None:
      MinMax = f" [{Min}-{Max}]"
    elif Min is not None:
      MinMax = f" [ >={Min}]"
    elif Max is not None:
      MinMax = f" [ <={Max}]"
    while Res is None:
      Res = AioShell.input(Prompt + MinMax, DefStr, [int], ForceAnswer=False)
      if Res is None and Default is not None:
        return Default
      if Res is None:
        AioShell.removeLastLine()
      elif (Min is not None and Res < Min) or (Max is not None and Res > Max):
        AioShell.removeLastLine()
        Res = None
    if UseCache:
      AioShell._int_cache[Prompt] = Res
    return Res    
  
  @staticmethod
  def inputFloat(Prompt : str, Default : float = None, Min : float = None, Max : float = None, UseCache = True):
    if UseCache:
      Cached = AioShell._float_cache.get(Prompt, None)
      if Cached is not None:
        Default = Cached
    if Default is not None:
      Default = float(Default)
      DefStr = str(Default)
    else:
      DefStr = None
    Res = None
    MinMax = ""
    if Min is not None and Max is not None:
      MinMax = f" [{Min}-{Max}]"
    elif Min is not None:
      MinMax = f" [ >={Min}]"
    elif Max is not None:
      MinMax = f" [ <={Max}]"
    while Res is None:
      Res = AioShell.input(Prompt + MinMax, DefStr, [float], ForceAnswer=False)
      if Res is None and Default is not None:
        return Default
      if Res is None:
        AioShell.removeLastLine()
      elif (Min is not None and Res < Min) or (Max is not None and Res > Max):
        AioShell.removeLastLine()
        Res = None
    if UseCache:
      AioShell._float_cache[Prompt] = Res
    return Res    
  
  @staticmethod
  def runCommand(command, PrintOutput=True):
    """Returns (stdout, stderr, returncode)
    """
    try:
      process = subprocess.Popen(
        shlex.split(command),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
      )
      stdout, stderr = "", ""
      while 1:
          line = process.stdout.readline()
          if not line:
              break
          if PrintOutput:
              print(line, end="")
          stdout += line
      stderr = process.stderr.read()
      if PrintOutput and stderr:
          print(stderr, end="")
      returncode = process.wait()
      return stdout, stderr, returncode
    except Exception as e:
      if PrintOutput:
        print(f"Error running command '{command}': {e}")
      return "", str(e), -1
  
  @staticmethod
  def runCommandsInParallel(Commands, ReturnCodes=True, ReturnStdOuts=False, ReturnStdErr=False, MultiThreading=True) -> list:
    from functools import partial
    Result = []
    if MultiThreading:
      from p_tqdm import p_imap
      for Res in p_imap(partial(AioShell.runCommand, PrintOutput=False), Commands):
        stdout, stderr, returncode = Res
        Row = []
        if ReturnCodes:
          Row.append(returncode)
        if ReturnStdOuts:
          Row.append(stdout)
        if ReturnStdErr:
          Row.append(stderr)
        if len(Row) > 0:
          Result.append(Row)
    else:
      from tqdm import tqdm
      for Command in tqdm(Commands):
        stdout, stderr, returncode = AioShell.runCommand(Command, PrintOutput=False)
        Row = []
        if ReturnCodes:
          Row.append(returncode)
        if ReturnStdOuts:
          Row.append(stdout)
        if ReturnStdErr:
          Row.append(stderr)
        if len(Row) > 0:
          Result.append(Row)
    AioShell.removeLastLine()  
    return Result    