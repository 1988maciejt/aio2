
class bits:
    """Iterate through all bits from the right (LSB)"""
    _bs = ""
    _it = None
    def __init__(self, Number : int) -> None:
        self._bs = bin(Number)
    def __iter__(self):
        self._it = reversed(self._bs).__iter__()
        return self
    def __next__(self):
        return 1 if self._it.__next__()=="1" else 0

  