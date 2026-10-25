# cython: language_level=3, boundscheck=False, wraparound=False

import cython
from bitarray import bitarray





cpdef void build_fast_sim_array_cython(object self, bint NotFull = False):
    cdef object oldVal = self._baValue.copy()
    cdef int size = self._size
    cdef int i, r, c, FirstOne, index
    
    # Inicjalizacja macierzy w Pythonie
    FSA = [[None for _ in range(size)] for _ in range(size)]
    
    cdef list rowm1 = FSA[0]
    cdef object baValue = self._baValue
    cdef object next1_func = self._next1
    
    for i in range(size):
        baValue.setall(0)
        baValue[i] = 1
        rowm1[i] = next1_func().copy()
        
    cdef object One = bitarray('1')
    cdef list row
    cdef object res
    cdef object row_c
    
    if not NotFull:
        for r in range(1, size):
            row = FSA[r]
            for c in range(size):
                row_c = rowm1[c]
                FirstOne = row_c.find(One)
                res = rowm1[FirstOne].copy()
                for index in row_c.search(One, FirstOne + 1):
                    res ^= rowm1[index]
                row[c] = res
            rowm1 = row
            
    self._ba_fast_sim_array = FSA
    self._baValue = oldVal