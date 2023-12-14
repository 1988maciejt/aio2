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
    uint_fast64_t** TapsBase = new uint_fast64_t * [TapsCount];
    uint_fast64_t** InvBase = new uint_fast64_t * [TapsCount];

    // Variables
    uint_fast64_t Value;
    uint_fast64_t AuxValue;
    uint_fast64_t Max = uint_fast64_t(1) << uint_fast64_t(Size);
    uint_fast64_t Period = 0;
    uint_fast64_t V0;
    uint_fast64_t SizeMask = uint_fast64_t(1) << uint_fast64_t(Size - 1);
    uint_fast64_t OneInFlop = 0;


    // Parsing taps from argv
    vector<vector<int>> Taps;
    int TapIndex = 0;
    for (int i = 2; i < argc; ++i) {
        vector<string> TapStrings = stringSplit(argv[i], "_");
        int TapTableSize = TapStrings.size() + 1;
        bool Destination = true;
        int NumPosition = 1;
        for (auto sNum : TapStrings) {
            int iNum = stoi(sNum);
            int Num = ((iNum < 0) ? -iNum : iNum) % Size;
            if (Destination) {
                uint_fast64_t* Tap = new uint_fast64_t[TapTableSize];
                uint_fast64_t* TapInv = new uint_fast64_t[TapTableSize];
                Tap[0] = uint_fast64_t(1) << uint_fast64_t(Num % Size);
                TapInv[0] = (iNum < 0) ? 1 : 0;
                Tap[1] = uint_fast64_t(TapTableSize);
                TapInv[1] = uint_fast64_t(TapTableSize);
                TapsBase[TapIndex] = Tap;
                InvBase[TapIndex] = TapInv;
            }
            else {
                TapsBase[TapIndex][NumPosition] = uint_fast64_t(1) << uint_fast64_t(Num % Size);
                InvBase[TapIndex][NumPosition] = (iNum < 0) ? 1 : 0;
            }
            NumPosition++;
            Destination = false;
        }
        TapIndex++;
    }

    while (1) {
        Value = 1 << OneInFlop;
        V0 = Value;
        Period = 0;
        for (uint_fast64_t Step = 0; Step < Max; ++Step) {
            AuxValue = Value >> 1;
            if (Value & 1) {
                AuxValue |= SizeMask;
            }
            for (int TapIndex = 0; TapIndex < TapsCount; ++TapIndex) {
                uint_fast64_t* Tap = TapsBase[TapIndex];
                uint_fast64_t* Inv = InvBase[TapIndex];
                bool And = true;
                for (int SIndex = 2; SIndex < Tap[1]; ++SIndex) {
                    if (Inv[SIndex]) {
                        if (Tap[SIndex] & Value) {
                            And = false;
                            break;
                        }
                    }
                    else {
                        if (!(Tap[SIndex] & Value)) {
                            And = false;
                            break;
                        }
                    }
                }
                if (Inv[0]) {
                    if (!And) {
                        AuxValue ^= Tap[0];
                    }
                }
                else {
                    if (And) {
                        AuxValue ^= Tap[0];
                    }
                }
            }
            Value = AuxValue;
            if (Value == V0) {
                Period = Step + 1;
                break;
            }
        }
        if (Period <= 1) {
            if (OneInFlop != 1) {
                OneInFlop = 1;
            }
            else {
                break;
            }
        }
        else {
            break;
        }
    }
    cout << Period << " ";
}