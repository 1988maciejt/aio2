from libs.files import *
import re

def preprocessTextToPythonCode(Text : str, *args) -> str:
  Result = 'from aio import *\n'
  Result += 'global PreprocessingResult___\n'
  Result += 'PreprocessingResult___ = ""\n'
  Lines = Text.split('\n')
  Spaces = ""
  for Line in Lines:
    if len(Line) == 0:
      if len(Spaces) > 0:
        Spaces = Spaces[0:-1]
      continue
    if (len(Line) >= 2) and (Line[0] == "`" and Line[1] != '('):
      Result += f'{Line[1::]}\n'
      if Line.strip().endswith(":"):
        Spaces += " "
    else:
      CheckIfLineIsEmpty = False
      while True:
        reFound = re.search(r'([^\`]*)\`\(([^\`]*)\`\)(.*)', Line)
        if reFound:
          if len(reFound[1]) > 0:
            Result += f'{Spaces}PreprocessingResult___ += "{reFound[1]}"\n'
          Result += Spaces + "PreprocessingResult___ += str(" + reFound[2] + ")\n"
          Line = reFound[3]
          CheckIfLineIsEmpty = True
        else:
          break
      if (not CheckIfLineIsEmpty) or (CheckIfLineIsEmpty and len(Line) > 0):
        Result += f'{Spaces}PreprocessingResult___ += "{Line}"\n'
      Result += f'{Spaces}PreprocessingResult___ += "\\n"\n'
  return Result

def preprocessString(Text : str, *args) -> str:
  global PreprocessingResult___
  exec(preprocessTextToPythonCode(Text, *args))
  return PreprocessingResult___[0:-1]

def preprocessFile(InputFileName : str, OutputFileName : str, *args):
  Text = readFile(InputFileName)
  Text = preprocessString(Text, args)
  writeFile(OutputFileName, Text)