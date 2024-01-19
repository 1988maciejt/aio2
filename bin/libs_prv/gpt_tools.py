import g4f
import asyncio
from libs.utils_str import *
from libs.aio import *

g4f.debug.logging = True  # Enable debug logging
g4f.debug.version_check = False  # Disable automatic version checking

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
  def askAQuestion(Question, Model="gpt-4", Provider=None, RealTimePrinting=True, TryToRemoveHeader=True):
    Msgs = []
    if TryToRemoveHeader:
      if Provider == g4f.Provider.Bing:
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
      print(Str.color("ASSISTANT: \t", "red"), end='')
      for R in Resp:
        print(R, flush=True, end='')
        response += R
      print()
    else:
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
    return str(response) 
  

class GptChat:
  
  __slots__ = ("_Model", "_Provider", "_Msgs", "_Stream")
  
  def __init__(self, Model="gpt-4", Provider=g4f.Provider.Bing, RealTimePrinting=True) -> None:
    self._Model = Model
    self._Provider = Provider
    self._Msgs = []
    self._Stream = bool(RealTimePrinting)
    
  def printChatHistory(self):
    for Msg in self._Msgs:
      Aio.print(GptUtils._msgToStr(Msg))
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
  
  def ask(self, Message : str) -> str:
    msg = GptUtils._makeMsg(str(Message), "user")
    self._Msgs.append(msg)
    R = GptUtils.askAQuestion(self._Msgs, self._Model, self._Provider, self._Stream)
    self._Msgs.append(GptUtils._makeMsg(str(R), "assistant"))
    return R
  
  def regenerate(self) -> str:
    if len(self._Model) < 2:
      return None
    self._Msgs = self._Msgs[:-1]
    R = GptUtils.askAQuestion(self._Msgs, self._Model, self._Provider, self._Stream)
    self._Msgs.append(GptUtils._makeMsg(str(R), "assistant"))
    return R
    
  