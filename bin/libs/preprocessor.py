from libs.files import *
import re

def preprocessTextToPythonCode(Text : str, *args) -> str:
  Result = 'from aio import *\n'
  Result += 'global PreprocessingResult___\n'
  Result += 'PreprocessingResult___ = ""\n'
  Lines = Text.split('\n')
  for Line in Lines:
    LineStripped = Line.strip()
    if (len(LineStripped) >= 2) and (LineStripped[0] == "`" and LineStripped[1] != '('):
      Result += f'{Line[1::]}\n'
    else:
      CheckIfLineIsEmpty = False
      while True:
        reFound = re.search(r'([^\`]*)\`\(([^\`]*)\`\)(.*)', Line)
        if reFound:
          if len(reFound[1]) > 0:
            Result += f'PreprocessingResult___ += "{reFound[1]}"\n'
          Result += "PreprocessingResult___ += str(" + reFound[2] + ")\n"
          Line = reFound[3]
          CheckIfLineIsEmpty = True
        else:
          break
      if (not CheckIfLineIsEmpty) or (CheckIfLineIsEmpty and len(Line) > 0):
        Result += f'PreprocessingResult___ += "{Line}"\n'
      Result += f'PreprocessingResult___ += "\\n"\n'
  return Result

def preprocessString(Text : str, *args) -> str:
  global PreprocessingResult___
  exec(preprocessTextToPythonCode(Text, *args))
  return PreprocessingResult___[0:-1]

def preprocessFile(InputFileName : str, OutputFileName : str, *args):
  Text = readFile(InputFileName)
  Text = preprocessString(Text, args)
  writeFile(OutputFileName, Text)