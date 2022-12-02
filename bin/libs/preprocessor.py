from libs.files import *
import re

def preprocessTextToPythonCode(Text : str, *args, **kwargs) -> str:
  Result = 'from aio import *\n'
  Result += f'args = {args}\n'
  Result += f'kwargs = {kwargs}\n'
  Result += 'global PreprocessingResult___\n'
  Result += 'PreprocessingResult___ = ""\n'
  Lines = Text.split('\n')
  Spaces = ""
  for Line in Lines:
    if len(Line) == 0:
      continue
    if re.match(r'^\s*`\s*end\s*\S*$', Line):
      if len(Spaces) > 0:
        Spaces = Spaces[0:-1]
      continue
    if (len(Line) >= 2) and re.match(r'^\s*`[^\(].*$', Line):
      Result += f'{Spaces}{Line.replace("`", "").strip()}\n'
      if Line.strip().endswith(":"):
        Spaces += " "
    else:
      CheckIfLineIsEmpty = False
      while True:
        reFound = re.search(r'([^\`]*)\`\(([^\`]*)\`\)(.*)', Line)
        if reFound:
          if len(reFound[1]) > 0:
            L2 = str(reFound[1]).replace('"', '\\"')
            Result += f'{Spaces}PreprocessingResult___ += "{L2}"\n'
          L2 = str(reFound[2]).replace('"', '\\"')
          Result += f'{Spaces}PreprocessingResult___ += str({L2})\n'
          Line = reFound[3]
          CheckIfLineIsEmpty = True
        else:
          break
      if (not CheckIfLineIsEmpty) or (CheckIfLineIsEmpty and len(Line) > 0):
        L2 = Line.replace('"', '\\"')
        Result += f'{Spaces}PreprocessingResult___ += """{L2}"""\n'
      Result += f'{Spaces}PreprocessingResult___ += "\\n"\n'
  return Result

def preprocessString(Text : str, *args, **kwargs) -> str:
  global PreprocessingResult___
  exec(preprocessTextToPythonCode(Text, *args, **kwargs))
  return PreprocessingResult___[0:-1]

def preprocessFile(InputFileName : str, OutputFileName : str, *args, **kwargs):
  Text = readFile(InputFileName)
  Text = preprocessString(Text, *args, **kwargs)
  writeFile(OutputFileName, Text)