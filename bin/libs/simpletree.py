from libs.aio import *

class SimpleTree:
    pass
class SimpleTree:
    
    __slots__ = ("_root")
    
    def __init__(self) -> None:
        self._root = [{}, None]
        
    def __repr__(self) -> str:
        return "SimpleTree()"
    
    def copy(self) -> SimpleTree:
        Result = SimpleTree()
        Result._root = self._root.copy()
        return Result
    
    def _iterStr(self, Prefix = "") -> str:
        Result = ""
        SB = self.getBranchIdentifiers([])
        for Id in SB:
            Item = self.get([Id])
            if Item is not None:
                Result += f'{Prefix}{Id} : {Item}\n'
            Sub = self.getSubTree([Id])
            Result += Sub._iterStr(f"{Prefix}{Id}.")
        return Result        
    
    def __str__(self) -> str:
        return self._iterStr()
    
    def print(self):
        Aio.print(str(self))
    
    def getSubTree(self, Path : list) -> SimpleTree:
        Node = self._root
        for PathPosition in Path:
            if Node[0].get(PathPosition, None) is None:
                return None
            Node = Node[0][PathPosition]
        Result = SimpleTree()
        Result._root = Node
        return Result
        
    def add(self, Item, Path : list):
        Node = self._root
        for PathPosition in Path:
            if Node[0].get(PathPosition, None) is None:
                Node[0][PathPosition] = [{}, None]
            Node = Node[0][PathPosition]
        Node[1] = Item
    
    def remove(self, Path : list):
        Node = self._root
        for PathPosition in Path:
            if Node[0].get(PathPosition, None) is None:
                return False
            Node = Node[0][PathPosition]
        Node[1] = None
    
    def get(self, Path):
        Node = self._root
        for PathPosition in Path:
            if Node[0].get(PathPosition, None) is None:
                return None
            Node = Node[0][PathPosition]
        return Node[1]
    
    def removeBranch(self, Path : list):
        Node = self._root
        for PathPosition in Path:
            if Node[0].get(PathPosition, None) is None:
                return False
            Node = Node[0][PathPosition]
        Node[0] = {}
        Node[1] = None
    
    def getBranchIdentifiers(self, Path : list) -> list:
        Node = self._root
        for PathPosition in Path:
            if Node[0].get(PathPosition, None) is None:
                return []
            Node = Node[0][PathPosition]
        return list(Node[0].keys())
    
    def getLevelItems(self, Level : int = 0) -> list:
        Result = []
        if Level < 0:
            return []
        elif Level == 0:
            for Id in self.getBranchIdentifiers([]):
                Item = self.get([Id])
                if Item is not None:
                    Result.append(tuple([[Id], Item]))
        else:
            for Id in self.getBranchIdentifiers([]):
                Tree = self.getSubTree([Id])
                SubResult = Tree.getLevelItems(Level-1)
                for Pos in SubResult:
                    Result.append(tuple([[Id] + Pos[0], Pos[1]]))
        return Result            