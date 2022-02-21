def parityOf(int_type : int) -> int:
  parity = 0
  while (int_type):
    parity = 1 - parity
    int_type = int_type & (int_type - 1)
  return(parity)

def mersenne(index : int) -> int:
  return ((1 << index) - 1)