
import fitz
import os
from libs.files import *
import shutil
from libs.utils_str import *


class Pdf:
  
  @staticmethod
  def splitIntoTextFiles(PdfFile, MaxFileLen = 0, Overlap = 32) -> list:
    PdfFile = os.path.abspath(PdfFile)
    ODir = PdfFile + "_splitted"
    try:
      Dir.make(ODir)
    except:
      try:
        shutil.rmtree(ODir)
        Dir.make(ODir)
      except:
        ODir += str(random.randint(1, 10000))         
        Dir.make(ODir)
    Result = []
    with fitz.open(PdfFile) as doc:
      Text = ""
      for page in doc:
        Text += page.get_text()
      SubIntex = 0
      for T in Str.splitIntoSections(Text, MaxFileLen, Overlap):
        FileName = f"{ODir}/{SubIntex}.txt"
        File.write(FileName, T)
        Result.append(FileName)
        SubIntex += 1
    return Result