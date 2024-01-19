import g4f
import asyncio

g4f.debug.logging = True  # Enable debug logging
g4f.debug.version_check = False  # Disable automatic version checking

class GptUtils:

  @staticmethod
  def _makeMsg(Content, Role = "user"):
    return {"role" : Role, "content": Content}

  @staticmethod
  def askAQuestion(Question, Model="gpt-4", Provider=None):
    Msgs = []
    if type(Question) not in (list, tuple):
      Msgs.append(GptUtils._makeMsg(str(Question))) 
    else:
      for Q in Question:      
        if type(Q) is dict:
          Msgs.append(Q)
        else:
          Msgs.append(GptUtils._makeMsg(str(Q)))
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
  
  __slots__ = ("_Model", "_Provider", "_Msgs")
  
  def __init__(self, Model="gpt-4", Provider=g4f.Provider.Bing) -> None:
    self._Model = Model
    self._Provider = Provider
    self._Msgs = []
    
  def printChatHistory(self):
    for Msg in self._Msgs:
      print(f"{Msg['role']}:\t{Msg['content']}")
    
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
    R = GptUtils.askAQuestion(self._Msgs, self._Model, self._Provider)
    self._Msgs.append(GptUtils._makeMsg(str(R), "assistant"))
    return R
  
  def regenerate(self) -> str:
    if len(self._Model) < 2:
      return None
    self._Msgs = self._Msgs[:-1]
    R = GptUtils.askAQuestion(self._Msgs, self._Model, self._Provider)
    self._Msgs.append(GptUtils._makeMsg(str(R), "assistant"))
    return R
    
  