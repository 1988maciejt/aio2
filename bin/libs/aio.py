import shutil
import os
import re
import pickle
from libs.files import getAioPath
from ansi2html import *
import time
from libs.utils_str import *

class Aio:
  _transcript = "" 
  _sections = False
  _section_opened = False
  _subsection_opened = False
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
  def getTerminalColumns() -> int:
    return shutil.get_terminal_size()[0]
  def getTerminalRows() -> int:
    return shutil.get_terminal_size()[1]
  def getPath() -> str:
    return getAioPath()
  def printTranscriptEnable(FileName = "transcript.txt"):
    global transcript_file
    Aio._transcript = ""
    transcript_file = open(FileName, "w")
  def printTranscriptDisable():
    Aio._transcript = ""
    del transcript_file
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
    open(FileName, "w").write(html)
  def resetTranscript():
    Aio._transcript = ""    
    Aio._sections = False
    Aio._section_opened = False
    Aio._subsection_opened = False
  def print(*args):
    s = ""
    for arg in args:
      s += str(arg) + " "
    s += "\n"
    Aio._transcript += s
    if "transcript_file" in globals():
      Text = re.sub(r'(\033\[[0-9]+m)', '', s)
      transcript_file.write(Text)
      transcript_file.flush()
      os.fsync(transcript_file.fileno())
    print(*args)
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
  def printSection(*args):
    s = ""
    for arg in args:
      s += str(arg) + " "
    Aio.transcriptSectionBegin(s)
  def printSubsection(*args):
    s = ""
    for arg in args:
      s += str(arg) + " "
    Aio.transcriptSubsectionBegin(s)
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
  def transcriptSectionEnd():
    Aio._transcript += '</div>\n' 
    Aio._section_opened = False
    print("")    
    if "transcript_file" in globals():
      transcript_file.write("\n")
      transcript_file.flush()
      os.fsync(transcript_file.fileno())
  def transcriptSubsectionEnd():
    Aio._transcript += '</div>\n' 
    Aio._subsection_opened = False
    print("")
    if "transcript_file" in globals():
      transcript_file.write("\n")
      transcript_file.flush()
      os.fsync(transcript_file.fileno())
  def printError(*args):
    Aio.print(Str.color("ERROR:", 'red'),*args)
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
  def timeItCode(Code : str, Iterations = 1):
    SCode = ""
    for Line in Code.split("\n"):
      SCode += "  " + Line + "\n"
    TCode = f'dt = 0\nfor i in range({str(Iterations)}):\n  t0 = time.time()\n{SCode}\n  dt += time.time() - t0\nprint(dt/{str(Iterations)},"s")'
    return compile(TCode, 'dummy', 'exec')
    
class Tc:
  def step(name = "transcript.txt") -> None:
    global tc_step
    if not "tc_step" in globals():
      tc_step = 1
    Aio.print("STEP " + str(tc_step) + ":\t" + name)
  def diff(FileName : str) -> None:
    result = Aio.shellExecute("diff " + FileName + " ../references/" + FileName)
    print(result)
    
