import docx
from libs.utils_int import *
import os
from libs.files import *
import shutil
from libs.utils_str import *

class Docx:
  
  @staticmethod
  def splitIntoSections(Document : docx.Document) -> list:
    Result = []
    SectionName = ""
    SectionLevel = 0
    Section = []
    for P in Document.paragraphs:
      _, Level = Int.splitLettersAndInt(P.style.name)
      if Level > 0:
        if len(Section) > 0 or len(SectionName) > 0:
          Result.append([SectionName, SectionLevel, Section])
        SectionName = P.text
        Section = [P]    
        SectionLevel = Level
      else:
        Section.append(P)
    if len(Section) > 0 or len(SectionName) > 0:
      Result.append([SectionName, SectionLevel, Section])
    return Result
      
  @staticmethod
  def splitDocxFileIntoSectionTextFiles(DocxFile, MaxFileLen = 0, Overlap = 32) -> dict:
    DocxFile = os.path.abspath(DocxFile)
    d = docx.Document(DocxFile)
    ODir = DocxFile + "_splitted"
    try:
      Dir.make(ODir)
    except:
      try:
        shutil.rmtree(ODir)
        Dir.make(ODir)
      except:
        ODir += str(random.randint(1, 10000))         
        Dir.make(ODir)
    Result = {}
    Index = 0
    ss = Docx.splitIntoSections(d)
    for s in ss:
      SList = s[2]
      if len(SList) < 2:
        continue
      SName = s[0]
      Text = ""
      Second = 0
      for si in SList:
        if Second: Text += "\n"
        else: Second = 1
        Text += si.text
      if MaxFileLen > 0:
        SubIntex = 0
        for T in Str.splitIntoSections(Text, MaxFileLen, Overlap):
          FileName = f"{ODir}/{Index}_{SubIntex}.txt"
          File.write(FileName, T)
          Result[FileName] = SName
          SubIntex += 1
      else:
        FileName = f"{ODir}/{Index}.txt"
        File.write(FileName, Text)
        Result[FileName] = SName
      Index += 1
    return Result
    
    
    