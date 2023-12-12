`debug = kwargs.get('debug', 0)
`inverters = kwargs.get('inverters', 0)

#include <iostream>
#include <string>
#include <vector>
#include "string_split.h"
#include <fstream>

using namespace std;

int main(int argc, char* argv[])
{

    if (argc < 3) {
        cout << "Too few arguments!" << endl;
        return 0;
    }

    std::ofstream File(argv[1], std::ios::binary);

    if (!File.is_open()) {
        cout << "ERROR" << endl;
        return -1;
    }

    // Taps database
    int Size = stoi(argv[2]);
    int TapsCount = argc - 3;
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
    char sequence;
    char seq_cntr;

    // Parsing taps from argv
    vector<vector<int>> Taps;
    int TapIndex = 0;
    for (int i = 3; i < argc; ++i) {
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

    Value = 1 << OneInFlop;
    V0 = Value;
    Period = 0;
    sequence = 0;
    seq_cntr = 0;
    for (uint_fast64_t Step = 0; Step < Max; ++Step) {
        sequence <<= 1;
        seq_cntr++;
        AuxValue = Value >> 1;
        if (Value & 1) {
            AuxValue |= SizeMask;
            sequence |= 1;
        }
        if (seq_cntr == 8) {
            File.write(reinterpret_cast<const char*>(&sequence), sizeof(sequence));
            seq_cntr = 0;
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

    if (seq_cntr > 0) {
        File.write(reinterpret_cast<const char*>(&sequence), sizeof(sequence));
    }
    File.close();
    cout << Period << " ";
}
