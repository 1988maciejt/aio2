#include <iostream>
#include <string>
#include <vector>
 
using namespace std;
 
// Split proc for arg
vector<string> split (string s, string delimiter) {
    size_t pos_start = 0, pos_end, delim_len = delimiter.length();
    string token;
    vector<string> res;
    while ((pos_end = s.find (delimiter, pos_start)) != string::npos) {
        token = s.substr (pos_start, pos_end - pos_start);
        pos_start = pos_end + delim_len;
        res.push_back (token);
    }
    res.push_back (s.substr (pos_start));
    return res;
}
 
int main(int argc, char* argv[])
{
   if (argc < 2) {
      cout << "Too few arguments!" << endl;
      return 1;
   }
   
   int Size = stoi(argv[1]);
   int TapsCount = argc - 2;
   int*** TapsBase = new int**[Size];
   for (int i = 0; i < Size; ++i) {
      TapsBase[i] = new int*[TapsCount];
   }
   
   // Parsing taps from argv
   vector<vector<int>> Taps;
   int TapIndex = 0;
   for (int i = 2; i < argc; ++i) {
      cout << argv[i] << " ";
      vector<string> TapStrings = split(argv[i], "-");    
      int TapTableSize = TapStrings.size()+1;
      bool Destination = true;
      int NumPosition = 1;
      for (auto Num : TapStrings) {
         for (int Offset = 0; Offset < Size; ++Offset) {
            if (Destination) {
               int* Tap = new int[TapTableSize];
               Tap[0] = (stoi(Num) + 1 + Offset) % Size;
               Tap[1] = TapTableSize;
               TapsBase[Offset][TapIndex] = Tap;
            } else {
               TapsBase[Offset][TapIndex][NumPosition] = (stoi(Num) + Offset) % Size;
            }
         }
         NumPosition++;
         Destination = false;
      }
      TapIndex++;
   }
   int* Value = new int[Size];
   for (int i = 0; i < Size; i++) {
      if (i == 0) Value[i] = 1;
      else Value[i] = 0;
   }
   int** TapsRow;
   int Offset = 0;
   unsigned int OnesCount = 1;
   unsigned long long int Period = 0;
   unsigned long long int Max = 1;
   Max <<= Size;
   for (unsigned long long int Step = 0; Step < Max; ++Step) {
      TapsRow = TapsBase[Offset];
      for (int TapIndex = 0; TapIndex < TapsCount; ++TapIndex) {
         int* Tap = TapsRow[TapIndex];
         int DestinationIndex = Tap[0];
         int TapMaxIndex = Tap[1];
         int AndResult = 1;
         for (int AIndex = 2; AIndex < TapMaxIndex; ++AIndex) {
            AndResult &= Value[Tap[AIndex]];
         }
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
         if (Value[Offset] == 1) {
            Period = Step+1;
            break;
         }
         if (OnesCount == 0) {
            break;
         }
      }
if debug:
      for (int i = 0; i < Size; ++i) {
         cout << Value[(i+Offset)%Size];
      }
      cout << "  " << OnesCount << "  " << Offset << endl;*/
   }
   cout << ";" << Period;
}