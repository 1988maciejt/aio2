`debug = kwargs.get('debug', 0)
`inverters = kwargs.get('inverters', 0)

#include <iostream>
#include <string>
#include <sstream>
#include <vector>
#include "string_split.h"
#include <fstream>

using namespace std;

const char* to_cstr(std::string&& s)
{
    static thread_local std::string sloc;
    sloc = std::move(s);
    return sloc.c_str();
}

int main(int argc, char* argv[])
{

    if (argc < 3) {
        cout << "Too few arguments!" << endl;
        return 0;
    }

    // Taps database
    int Size = stoi(argv[2]);
    int TapsCount = argc - 3;
    uint_fast64_t** TapsBase = new uint_fast64_t * [TapsCount];
    uint_fast64_t** InvBase = new uint_fast64_t * [TapsCount];

    std::ofstream** File = new std::ofstream * [Size];
    for (int i = 0; i < Size; i++) {
        std::stringstream fname;
        fname << argv[1] << "." << i;
        File[i] = new std::ofstream(to_cstr(fname.str()), std::ios::binary);
        if (!File[i]->is_open()) {
            cout << "ERROR" << endl;
            return -1;
        }
    }

    // Variables
    uint_fast64_t Value;
    uint_fast64_t AuxValue;
    uint_fast64_t Max = uint_fast64_t(1) << uint_fast64_t(Size);
    uint_fast64_t Period = 0;
    uint_fast64_t V0;
    uint_fast64_t SizeMask = uint_fast64_t(1) << uint_fast64_t(Size - 1);
    uint_fast64_t OneInFlop = 0;
    char* sequence = new char[Size];
    for (uint_fast64_t i = 0; i < Size; i++) {
        sequence[i] <<= 0;
    }
    char seq_cntr;
    uint_fast64_t sequence_mask = 0;

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
    seq_cntr = 0;
    for (uint_fast64_t Step = 0; Step < Max; ++Step) {
        seq_cntr++;
        AuxValue = Value >> 1;
        sequence_mask = 1;
        for (uint_fast64_t i = 0; i < Size; i++) {
            sequence[i] <<= 1;
            if (Value & sequence_mask) {
                sequence[i] |= 1;
            }
            sequence_mask <<= 1;
        }
        if (Value & 1) {
            AuxValue |= SizeMask;
        }
        if (seq_cntr == 8) {
            for (uint_fast64_t i = 0; i < Size; i++) {
                File[i]->write(reinterpret_cast<const char*>(&sequence[i]), 1);
            }
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

    for (uint_fast64_t i = 0; i < Size; i++) {
        if (seq_cntr > 0) {
            if (seq_cntr < 8) {
                sequence[i] <<= (8 - seq_cntr);
            }
            File[i]->write(reinterpret_cast<const char*>(&sequence[i]), 1);
        }
    }

    for (uint_fast64_t i = 0; i < Size; i++) {
        File[i]->close();
    }
    cout << Period << " ";
}
