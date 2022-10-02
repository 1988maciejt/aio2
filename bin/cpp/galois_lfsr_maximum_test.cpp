#include <iostream>
#include <string>

using namespace std;

/*
  mask, number0, number1, ..., numbern
*/
int main(int argc, char* argv[])
{
  if (argc < 2) {
      cout << "Too few arguments!" << endl;
      return 0;
  }

  // Size
  int Size = argv[1].length();

  // Galois LFSR mask
  int* Mask = new int[Size]
  for (int i = 0; i < Size; ++i) {
    Mask[i] = argv[0][i] - '0'
  }

  // Main table
  int*** MainTable = new int**[Size];
  for (int i = 0; i < Size; ++i) {
    MainTable[i] = new int*[Size]
    for (int j = 0; j < Size; ++j) {
      MainTable[i][j] = new int[Size]
    }
  }

  // First row
  for (int i = 0; i < Size; ++i) {
    for (int bit = 0; bit < Size; ++bit) {
      MainTable[0][i][bit] = 0;
    }
    MainTable[0][i][(i-1)%Size] = 1
    MainTable[0][0][i] ^= Mask[i]
  }
  
  // Filling the rest of table


  // Testing
  int* Value = new int[Size]
  for (int ai = 2; ai < argc; ++ai) {
    for (int i = 0; i < Size; ++i) {
      Value[i] = 0
    }

  }


  return 1;
}