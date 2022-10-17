`debug = kwargs.get('debug', 0)
`inverters = kwargs.get('inverters', 0)

#include <iostream>
#include <string>
#include <vector>
#include "string_split.h"
 
using namespace std;

 
int main(int argc, char* argv[])
{
   if (argc < 2) {
      cout << "Too few arguments!" << endl;
      return 0;
   }
   
   // Taps database
   int Size = stoi(argv[1]);
   int TapsCount = argc - 2;
   int*** TapsBase = new int**[Size];
   for (int i = 0; i < Size; ++i) {
      TapsBase[i] = new int*[TapsCount];
   }
`if inverters:

   // Inverters database
   bool** InvertersBase = new bool*[TapsCount];
`endif
   
   // Parsing taps from argv
   vector<vector<int>> Taps;
   int TapIndex = 0;
   for (int i = 2; i < argc; ++i) {
      vector<string> TapStrings = stringSplit(argv[i], "_");   
`if inverters:
      bool* TapInverters = new bool[TapStrings.size()];
`endif
      int TapTableSize = TapStrings.size()+1;
      bool Destination = true;
      int NumPosition = 1;
      for (auto sNum : TapStrings) {
`if inverters:
         int iNum = stoi(sNum);
         int Num = ((iNum < 0) ? -iNum : iNum) % Size;
         TapInverters[NumPosition-1] = (iNum < 0);
`endif
`else:
         int Num = stoi(sNum) % Size;
`endif
         for (int Offset = 0; Offset < Size; ++Offset) {
            if (Destination) {
               int* Tap = new int[TapTableSize];
               Tap[0] = (Num + 1 + Offset) % Size;
               Tap[1] = TapTableSize;
               TapsBase[Offset][TapIndex] = Tap;
            } else {
               TapsBase[Offset][TapIndex][NumPosition] = (Num + Offset) % Size;
            }
         }
         NumPosition++;
         Destination = false;
      }
      TapIndex++;
`if inverters:
      InvertersBase[i-2] = TapInverters;
`endif
   }

`if debug:
   // print Taps database
   cout << endl << "TapsBase: " << endl;
   for (int Offset = 0; Offset < Size; ++Offset) {
      cout << "----- Offset " << Offset << "------" << endl;
      for (int TapIndex = 0; TapIndex < TapsCount; ++TapIndex) {
         int* Tap = TapsBase[Offset][TapIndex];
         cout << Tap[0] << " <- { ";
         int TapEnd = Tap[1];
         for (int i = 2; i < TapEnd; ++i) {
            cout << Tap[i] << " ";
         }
         cout << "}, ";
      } 
      cout << endl;
   }
   cout << "<Reversed_state> <OnesCount>" << endl;
`endif

   int* Value = new int[Size];
   int OneInFlop = 0;
   unsigned long long int Max = 1<<Size;
   unsigned long long int Period = 0;
   while (1) {
      for (int i = 0; i < Size; i++) {
         if (i == OneInFlop) Value[i] = 1;
         else Value[i] = 0;
      }
      int** TapsRow;
      int Offset = 0;
      unsigned int OnesCount = 1;
      Period = 0;
      for (unsigned long long int Step = 0; Step < Max; ++Step) {
         TapsRow = TapsBase[Offset];
         for (int TapIndex = 0; TapIndex < TapsCount; ++TapIndex) {
            int* Tap = TapsRow[TapIndex];
            int DestinationIndex = Tap[0];
            int TapMaxIndex = Tap[1];
            int AndResult = 1;
            for (int AIndex = 2; AIndex < TapMaxIndex; ++AIndex) {           
`if inverters:
               if (InvertersBase[TapIndex][AIndex-1]) {
                  AndResult &= !Value[Tap[AIndex]];
               } else {
                  AndResult &= Value[Tap[AIndex]];
               }
`endif
`else:
               AndResult &= Value[Tap[AIndex]];
`endif
            }
`if inverters:
            if (InvertersBase[TapIndex][0]) {
               AndResult = !AndResult;
            }
`endif
            int OldBit = Value[DestinationIndex];
            int NewBit = OldBit ^ AndResult;
            Value[DestinationIndex] = NewBit;
            if (OldBit != NewBit) {
               if (NewBit == 1) OnesCount++;
               else OnesCount--;
            }
         }
         Offset = (Offset+1) % Size;
         if (OnesCount <= 1) {
            if (Value[(Offset+OneInFlop) % Size] == 1) {
               Period = Step+1;
               break;
            }
`if not inverters:
            if (OnesCount == 0) {
               break;
            }
`endif
         }
`if debug:
         for (int i = 0; i < Size; ++i) {
            cout << Value[(i+Offset)%Size];
         }
         cout << "  " << OnesCount << endl;
`endif
      }
      if (Period <= 1) {
         if (OneInFlop != 1) {
            OneInFlop = 1;
         } else {
            break;
         }
      } else {
         break;
      }
   }

   cout << Period << " ";
}