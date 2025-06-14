import g4f
from libs.utils_str import *
from libs.aio import *
import gensim
import nltk
from libs.files import *
import re
from p_tqdm import *
from functools import partial
from libs.utils_list import *
from tqdm import *
from libs.utils_docx import *
#from libs.utils_pdf import *

#g4f.debug.logging = True  # Enable debug logging
g4f.debug.version_check = False  # Disable automatic version checking


class GptChat:
  pass
class GptChat:
  pass


class GptUtils:

  @staticmethod
  def _makeMsg(Content, Role = "user"):
    return {"role" : Role, "content": Content}
  
  @staticmethod
  def _msgToStr(Message : dict) -> str:
    if Message["role"] == "user":
      Result = Str.color("QUESTION", "green")
    else:
      Result = Str.color("RESPONSE", "red")
    Result += f" \t{Message['content']}"  
    return Result
      
  @staticmethod
  def askAQuestion(Question, Model="gpt-4", Provider=None, RealTimePrinting=True, TryToRemoveHeader=True, StreamLikeProgressBar=False):
    Msgs = []
    if TryToRemoveHeader:
      if Provider == g4f.Provider.bing:
        Msgs.append(GptUtils._makeMsg("Witaj"))
        Msgs.append(GptUtils._makeMsg("Witaj, to jest Bing.", "assistant"))
    if type(Question) not in (list, tuple):
      Msgs.append(GptUtils._makeMsg(str(Question))) 
    else:
      for Q in Question:      
        if type(Q) is dict:
          Msgs.append(Q)
        else:
          Msgs.append(GptUtils._makeMsg(str(Q)))
    if RealTimePrinting:
      response = ""
      Counter = 2
      while Counter > 0:
        try:
          if Provider is None:
            Resp = g4f.ChatCompletion.create(
              model=Model,
              messages=Msgs,
              stream=True
            )
          else:
            Resp = g4f.ChatCompletion.create(
              model=Model,
              messages=Msgs,
              provider=Provider,
              stream=True
            )
            break
        except:
          Counter -= 1
      Counter = 2
      while Counter > 0:
        if not StreamLikeProgressBar:
          print(Str.color("ASSISTANT: \t", "red"), end='')
        try:
          response = ""
          for R in Resp:
            response += R
            if StreamLikeProgressBar:
              LineSDisp = Str.color(Str.color(Str.toRight(response.replace('\n', ' '), Aio.getTerminalColumns() // 2), "back blue"), "white bright")
              print(LineSDisp, flush=True, end='\r')
            else:
              print(R, flush=True, end='')
          print()
          break
        except:
          pass
      if StreamLikeProgressBar:
        #print()
        AioShell.removeLastLine()
    else:
      Counter = 2
      while Counter > 0:
        try:
          response = ""
          if Provider is None:
            response = g4f.ChatCompletion.create(
              model=Model,
              messages=Msgs
            )
          else:
            response = g4f.ChatCompletion.create(
              model=Model,
              messages=Msgs,
              provider=Provider
            )
          break
        except:
          Counter -= 1
    return str(response) 
  
  @staticmethod
  def nltkPrepare():
    nltk.download("punkt")
    nltk.download("pl196x")
  
  @staticmethod
  def text2Tokens(Text):
    return nltk.word_tokenize(Text)
  
  @staticmethod
  def createWordEmbeddings(ListOfInputFileNames : list, RemoveTokensShorterThan = 3, Size=100, Window=5, MinCount=2) -> gensim.models.Word2Vec:
    sentences = []
    for FileName in ListOfInputFileNames:
      text = File.read(FileName).lower()
      sen_tokens = nltk.sent_tokenize(text)
      for st in sen_tokens:
        t = nltk.word_tokenize(st)
        tokens = []
        for ti in t:
          if len(ti) >= RemoveTokensShorterThan:
            tokens.append(ti)
        sentences.append(tokens)
    model = gensim.models.Word2Vec(sentences, vector_size=Size, window=Window, min_count=MinCount)
    return model
  
  @staticmethod
  def createDocsEmbeddings(ListOfInputFileNames : list, RemoveTokensShorterThan = 3, Size=100, Window=5, MinCount=2) -> gensim.models.Doc2Vec:
    docs = []
    for FileName in ListOfInputFileNames:
      text = Str.removePunctuation(File.read(FileName).lower())
      sen_tokens = nltk.sent_tokenize(text)
      for st in sen_tokens:
        t = nltk.word_tokenize(st)
        tokens = []
        for ti in t:
          if len(ti) >= RemoveTokensShorterThan:
            tokens.append(ti)
        docs.append(gensim.models.doc2vec.TaggedDocument(tokens, [FileName]))
    model = gensim.models.Doc2Vec(docs, vector_size=Size, window=Window, min_count=MinCount)
    return model
  
  @staticmethod
  def getMostSimilarDocuments(Question : str, model : gensim.models.Doc2Vec, RemoveTokensShorterThan = 3, IncludeSimilarityFactors=False):
    t = nltk.word_tokenize(Str.removePunctuation(Question.lower()))
    tokens = []
    for ti in t:
      if len(ti) >= RemoveTokensShorterThan:
        tokens.append(ti)
    nv = model.infer_vector(tokens)
    msim = model.docvecs.most_similar(nv)
    if not IncludeSimilarityFactors:
      Result = []
      for ms in msim:
        Result.append(ms[0])
      return Result
    return msim
  
  @staticmethod
  def createContextFilesForChat(ListOfInputFileNames : list, SingleFileSize = 1024, Overlap = 256) -> list:
    Result = []
    for FileName in ListOfInputFileNames:
      Texts = Str.splitIntoSections(File.read(FileName), SingleFileSize, Overlap)
      for i in range(len(Texts)):
        OFName = f"{FileName}.part{i}"
        File.write(OFName, Texts[i])
        Result.append(OFName)
    return Result
  
  @staticmethod
  def findKeywordsUsingChat(Question : str, Model="gpt-4", Provider = g4f.Provider.bing, RealTimePrinting = True) -> list:
    cb = GptChat(Model, Provider, RealTimePrinting=RealTimePrinting, SingleLinePrinting=1)
    cb.addSystemMessage("Podaj odpowiedź w postaci długiej listy krótkich pojęć. Nie stosuj notacji markdown. Nie wyjaśniaj akronimów.")
    try:
      KW = cb.ask("Wypisz syntetyczną listę słów kluczowych dla tekstu:\n" + Question)
    except:
      try:
        KW = cb.ask("Wypisz syntetyczną listę słów kluczowych dla tekstu:\n" + Question)
      except:
        return None
    KWL = KW.split("\n")
    KWS = set()
    for Line in KWL:
      R = re.search(r'\-\s*([^:()*]{1,35})\s*\-\s*', Line)
      if R:
        KWS.add(R.group(1).lower().replace("*", ""))
        continue
      R = re.search(r'^\s*[0-9-]+\s*[,.:-]*\s+([^:()*]{1,35})\s*', Line)
      if R:
        KWS.add(R.group(1).lower().replace("*", ""))
        continue
      R = re.search(r'[0-9]+[,.:-]+\s*([^:()]{1,35}})\s\-\s', Line)
      if R:
        KWS.add(R.group(1).lower())
        continue
      R = re.search(r'\*(.{1,35})\*', Line)
      if R:
        KWS.add(R.group(1).lower())
        continue
    return list(KWS)
      
  @staticmethod
  def findKeywoardsForFile(FileName : list, Model="gpt-4", Provider = g4f.Provider.bing, RealTimePrinting = False) -> tuple:
    T = File.read(FileName)
    return FileName, GptUtils.findKeywordsUsingChat(T, Model, Provider, RealTimePrinting)
  
  @staticmethod
  def findKeywoardsForFiles(FileNamesList : list, Model="gpt-4", Provider = g4f.Provider.bing, ExtendKeywords=1) -> dict:
    ResDict = {}
    if 0:
      for FileName, KeyWords in p_uimap(partial(GptUtils.findKeywoardsForFile, Model=Model, Provider=Provider), FileNamesList):
        for kw in KeyWords:
          Lst = ResDict.get(kw, [])
          Lst.append(FileName)
          Lst = set(Lst)
          ResDict[kw] = list(Lst)
      return ResDict
    for FileName in FileNamesList:
      T = File.read(FileName)
      KeyWords = GptUtils.findKeywordsUsingChat(T, Model, Provider)
      if ExtendKeywords:
        KeyWords = GptUtils.extendKeywords(KeyWords)
      for kw in KeyWords:
        Lst = ResDict.get(kw, [])
        Lst.append(FileName)
        ResDict[kw] = Lst
    return ResDict
  
  @staticmethod
  def extendKeywords(Keywords : list) -> list:
    Result = []
    for kw in Keywords:
      kwl = kw.split(" ")
      if len(kwl) > 1:        
        for kx in kwl:
          if len(kx) > 2:
            Result.append(kx)
        kwll = [kwl for _ in range(len(kwl))]
        for perm in List.getPermutationsPfManyListsGenerator(kwll):
          if len(perm) == 0:
            break
          if List.onlyUniquesAreIncluded(perm[0]):
            Second = 0
            nkw = ""
            for p in perm[0]:
              if Second:
                nkw += " "
              else:
                Second = 1
              nkw += p
            Result.append(nkw)
      else:
        Result.append(kw)
    return Result
  
  @staticmethod
  def getMessageStr(Message : dict, WindowWidth : int, Indentation = 5) -> str:
    MessageWidth = WindowWidth - Indentation
    Message['content'] = Str.latexToPlainText(Message['content'])
    if Message['role'] == 'user':
      return Str.booble(Message['content'], MessageWidth, 'bright white', 'bright black')
    elif Message['role'] == 'system':
      return Str.indent(Str.booble(Message['content'], MessageWidth, 'red', 'bright white'), Indentation)
    else:
      return Str.indent(Str.booble(Message['content'], MessageWidth, 'blue', 'bright white'), Indentation)
  
  @staticmethod
  def printMessage(Message : dict, WindowWidth : int):
    Aio.print(GptUtils.getMessageStr(Message, WindowWidth))
  



class GptSynonyms:
  
  __slots__ = ("_dict", "_filename")
  
  def __init__(self, FileName : str = None) -> None:
    self._filename = FileName
    self._dict = {}
    try:
      d = File.readObject(FileName)
      if type(d) is dict:
        self._dict = d
    except:
      pass

  def getSynonyms(self, Term : str, References : list) -> list:
    Result = self._dict.get(Term, None)
    if Result is None:
      Result = []
      if type(References) is List:
        Iter = References
      elif type(References) is dict:
        Iter = References.keys()
      else:
        Iter = list(References)
      for Ref in Iter:
        if Str.similarity(Term, Ref) >= 0.8:
          Result.append(Ref)
      self._dict[Term] = Result
      if self._filename is not None:
        File.writeObject(self._filename, self._dict)
    return Result
  
  def extendKeyWords(self, KWList : list, References : list) -> list:
    Result = set()
    for KW in KWList:
      Result.add(KW)
      Syn = self.getSynonyms(KW, References)
      for S in Syn:
        Result.add(S)
    return list(Result)


class GptDataBase:
  
  __slots__ = ("_dict", "_embd", "_synonyms")
  
  def __init__(self, SourceDocFileList : list, IndexfileName : str, IncludeSynonyms : bool = True) -> None:
    FetchedFromFile = True
    HASH = SourceDocFileList
    try:
      Data = File.readObject(IndexfileName + ".dat")
      self._dict = Data[0]
      _hash = Data[1]
      if type(self._dict) is not dict:
        FetchedFromFile = False
      if _hash != HASH:
        FetchedFromFile = False
      self._embd = gensim.models.Doc2Vec.load(IndexfileName + ".doc2vec")
    except:
      FetchedFromFile = False
    if not FetchedFromFile:
      Files = []
      for Doc in tqdm(SourceDocFileList, desc="Splitting source files"):
        if str(Doc).lower().endswith(".docx"):
          Files += list(Docx.splitDocxFileIntoSectionTextFiles(Doc, 2900, 512).keys())
        #elif str(Doc).lower().endswith(".pdf"):
        #  Files += Pdf.splitIntoTextFiles(Doc, 2900, 512)
      self._embd = GptUtils.createDocsEmbeddings(Files)
      self._embd.save(IndexfileName + ".doc2vec")
      self._dict = GptUtils.findKeywoardsForFiles(Files, Provider=g4f.Provider.bing)
      File.writeObject(IndexfileName + ".dat", [self._dict, HASH])
    if IncludeSynonyms:
      self._synonyms = GptSynonyms(IndexfileName + ".synonyms")
    else:
      self._synonyms = None

  def getContextFiles(self, Question : str, BasedOnKW = 3, BasedOnEmbeddings = 3) -> list:
    Result = []
    KeyWords = GptUtils.findKeywordsUsingChat(Question)
    KeyWords = GptUtils.extendKeywords(KeyWords)
    if self._synonyms is not None:
      KeyWords = self._synonyms.extendKeyWords(KeyWords, self._dict)
    if BasedOnKW > 0:
      ContFiles = {}
      for kw in KeyWords:
        F = self._dict.get(kw, None)
        if F is not None:
          for FName in F:
            i = ContFiles.get(FName, 0)
            ContFiles[FName] = i+1
      ProposedFiles = [Item for Item in ContFiles.items()]
      ProposedFiles.sort(key = lambda x: x[1], reverse=1)
      ContentFiles = [Item[0] for Item in ProposedFiles]
      Result += ContentFiles[:BasedOnKW]
    if BasedOnEmbeddings > 0:
      KWString, Second = "", 0
      for KW in KeyWords:
        if Second: KWString += " "
        else: Second = 1
        KWString += KW
      EmbeddingFiles = GptUtils.getMostSimilarDocuments(Question + " " + KWString, self._embd)
      Result += EmbeddingFiles[:BasedOnEmbeddings]
    return Result



class GptChat:
  
  __slots__ = ("_Model", "_Provider", "_Msgs", "_Stream", "_db", "_single_line_printing")
  
  def __init__(self, Model="gpt-4", Provider=g4f.Provider.bing, DataBase : GptDataBase = None, RealTimePrinting=True, SingleLinePrinting=False) -> None:
    self._Model = Model
    self._Provider = Provider
    self._Msgs = []
    self._Stream = bool(RealTimePrinting)
    self._db = DataBase
    self._single_line_printing = SingleLinePrinting
    self.clear()
    
  def printChatHistory(self, Width = 100):
    for Msg in self._Msgs:
      GptUtils.printMessage(Msg, Width)
      Aio.print()
      
  print = printChatHistory
    
  def getResponses(self) -> list:
    Result = []
    for Msg in self._Msgs:
      if Msg['role'] == "assistant":
        Result.append(Msg['content'])
    return Result
  
  def getQuestions(self) -> list:
    Result = []
    for Msg in self._Msgs:
      if Msg['role'] == "user":
        Result.append(Msg['content'])
    return Result
  
  def clear(self):
    self._Msgs = []
    
  def getLastResponse(self) -> str:
    Resps = self.getResponses()
    if len(Resps) < 1:
      return None
    return Resps[-1]
    
  def getLastQuestion(self) -> str:
    Quests = self.getQuestions()
    if len(Quests) < 1:
      return None
    return Quests[-1]
  
  def addSystemMessage(self, Text : str):
    self._Msgs.append(GptUtils._makeMsg(Text, "system"))
    
  def addUserMessage(self, Text : str):
    self._Msgs.append(GptUtils._makeMsg(Text, "user"))
    
  def addAssistantMessage(self, Text : str):
    self._Msgs.append(GptUtils._makeMsg(Text, "assistant"))
  
  def ask(self, Message : str, ContextFileList : list = None) -> str:
    if type(ContextFileList) is list:
      for FileName in ContextFileList:
        self._Msgs.append(GptUtils._makeMsg(File.read(FileName), "system"))
    if self._db is not None:
      CFs = self._db.getContextFiles(Message)
      for FileName in CFs:
        self._Msgs.append(GptUtils._makeMsg(File.read(FileName), "system"))
    msg = GptUtils._makeMsg(str(Message), "user")
    self._Msgs.append(msg)
    for _ in range(3):
      R = GptUtils.askAQuestion(self._Msgs, self._Model, self._Provider, self._Stream, True, self._single_line_printing)
      if len(R) > 1:
        break
    self._Msgs.append(GptUtils._makeMsg(str(R), "assistant"))
    return R
  
  def regenerate(self) -> str:
    if len(self._Model) < 2:
      return None
    self._Msgs = self._Msgs[:-1]
    R = GptUtils.askAQuestion(self._Msgs, self._Model, self._Provider, self._Stream)
    self._Msgs.append(GptUtils._makeMsg(str(R), "assistant"))
    return R
  
  def chat(self, PrintChatHistory=False):
    W = 100
    Waux = Aio.getTerminalColumns() - 2
    if W > Waux:
      W = Waux
    if PrintChatHistory:
      self.printChatHistory(W)
    Stream = self._Stream
    SingleLine = self._single_line_printing
    self._Stream = True
    self._single_line_printing = True
    while(1):
      Question = input(f"{Str.color('> ', 'green')}")
      Aio.print()
      if len(Question) < 1:
        break
      try:
        self.ask(Question)
        GptUtils.printMessage(self._Msgs[-1], W)
        Aio.print()
      except:
        Aio.printError("Unexpected error")
        break
    self._Stream = Stream
    self._single_line_printing = SingleLine
    
  
