#include <cuda.h>
#include <iostream>
#include <ctime>
#include <algorithm>
#include <vector>
#include <bitset>
    
`cpu_debug = kwargs.get('cpu_debug', False)
`scan_length = kwargs.get('scan_length', 16)
`scan_count = kwargs.get('scan_count', 8)
`cuda_blocks = kwargs.get('cuda_blocks', 64)
`cuda_threads = kwargs.get('cuda_threads', 64)
`cuda_grid_size = cuda_blocks * cuda_threads
`compactor_registers = kwargs.get('compactor_registers', [])
`global_xor_exists = ([0, 0] in compactor_registers)
`compactor_registers_count = len(kwargs.get('compactor_registers', []))
`compactor_register_size = kwargs.get('scan_length', 16)+kwargs.get('scan_count', 8)
`compactor_register_words = (compactor_register_size-1) // 16 + 1
`compactor_given_result = kwargs.get('compactor_value', None)
`if compactor_given_result is None:
`   Aio.print("Compactor value not given!!!!")
`endif
`shift_register_size = scan_count
`shift_register_words = (shift_register_size-1) // 16 + 1
    
// max tree branches for host/dev:  200000000
#define TREE_BRANCHES               `(kwargs.get('max_tree_branches', 20000000)`) 
#define MAX_LUT_SIZE                `(kwargs.get('max_lut_size', 4000000)`) 

#define SCAN_LENGTH                 `(scan_length`)
#define SCAN_REGISTER_WORDS         `((scan_length-1) // 16 + 1`)
#define SCAN_COUNT                  `(scan_count`)

#define COMPACTOR_REGISTERS_COUNT   `(compactor_registers_count`)
#define COMPACTOR_REGISTER_SIZE     `(compactor_register_size`)
#define COMPACTOR_REGISTER_WORDS    `(compactor_register_words`)

#define MAX_TOTAL_FAIL_COUNT        `(kwargs.get('max_total_fails', 8)`)
#define FAILS_PER_CLOCK_CYCLE       `(kwargs.get('max_fails_per_clock_cycle', 3)`)
#define FAILS_HORIZONTAL_DISTANCE   `(kwargs.get('max_fails_horizontal_distance', 5)`)
#define FAILS_VERTICAL_DISTANCE     `(kwargs.get('max_fails_vertical_distance', 5)`)
    
using namespace std;


    
struct TreeItem {
    short ScanMinIndex = -1;
    short ScanMaxIndex = -1;
    short FailMap[SCAN_LENGTH];
};

struct LUTRow {
    short First = -1;
    short Last = -1;
    short FailCount = 0;
    short LUT[FAILS_PER_CLOCK_CYCLE];
};

// COMPACTOR REGISTERS
struct CompactorRegister {
    unsigned short Reg[COMPACTOR_REGISTER_WORDS];
};
struct CompactorRegisters {
    short Length = 0;
    CompactorRegister Regs[COMPACTOR_REGISTERS_COUNT];
};
void printCompactorRegisters(CompactorRegisters* Regs) {
    for (int i = 0; i < COMPACTOR_REGISTERS_COUNT; i++) {
        cout << " - REG " << i << ":\\t";
        for (int j = COMPACTOR_REGISTER_WORDS-1; j >= 0; j--) {
            cout << bitset<16>(Regs->Regs[i].Reg[j]);
            if (j > 0) cout << "";
        }
        cout << "      ";
        for (int j = COMPACTOR_REGISTER_WORDS-1; j >= 0; j--) {
            cout << (Regs->Regs[i].Reg[j]);
            if (j > 0) cout << ",";
        }
        cout << endl;
    }
}
__host__ __device__
short getCompactorBit(CompactorRegisters* Regs, short& RegIndex, short& BitIndex) {
    if ((Regs->Regs[RegIndex].Reg[BitIndex / 16]) & (1 << (BitIndex % 16))) return 1;
    return 0;
}
__host__ __device__
void setCompactorBit(CompactorRegisters* Regs, short& RegIndex, short& BitIndex, short BitValue) {
    if (BitValue) {
        Regs->Regs[RegIndex].Reg[BitIndex / 16] |= (1 << (BitIndex % 16));
    } else {
        Regs->Regs[RegIndex].Reg[BitIndex / 16] &= ~(1 << (BitIndex % 16));
    }
}
__host__ __device__
void pushCompactorValue(CompactorRegisters* Regs, short* BitValues) {
    for (short ri = 0; ri < COMPACTOR_REGISTERS_COUNT; ri++) {
        setCompactorBit(Regs, ri, Regs->Length, BitValues[ri]);
    }
    Regs->Length++;
    if (Regs->Length > COMPACTOR_REGISTER_SIZE)
        Regs->Length--;
}
__host__ __device__
void clearCompactorRegisters(CompactorRegisters* Regs) {
    Regs->Length = 0;
    for (short ri = 0; ri < COMPACTOR_REGISTERS_COUNT; ri++) {
        for (short i = 0; i < COMPACTOR_REGISTER_WORDS; i++) {
            Regs->Regs[ri].Reg[i] = 0;
        }
    }
}
__host__ __device__
bool areCompactorsEqual(CompactorRegisters* SimComp, CompactorRegisters* Reference) {
    for (short cindex = 0; cindex < SimComp->Length; cindex++) {
        for (short ri = 0; ri < COMPACTOR_REGISTERS_COUNT; ri++) {
            if (getCompactorBit(SimComp, ri, cindex) != getCompactorBit(Reference, ri, cindex)) {
                return false;
            }
        }
    }
    return true;
}
    
// SHIFT REGISTER
struct ShiftRegister {
    unsigned short Reg[`(shift_register_words`)];
};
__host__ __device__ 
void setShiftRegisterBit(ShiftRegister* Reg, short& BitIndex, short& BitValue) {
    if (BitValue) {
        Reg->Reg[BitIndex / 16] |= (1 << (BitIndex % 16));
    } else {
        Reg->Reg[BitIndex / 16] &= ~(1 << (BitIndex % 16));
    }
}
__host__ __device__
short getShiftRegisterBit(ShiftRegister* Reg, short BitIndex) {
    if ((Reg->Reg[BitIndex / 16]) & (1 << (BitIndex % 16))) return 1;
    return 0;
}
__host__ __device__
void shiftShiftRegister(ShiftRegister* Reg) {
    for (short i =  `(shift_register_words-1`); i >= 0; i--) {
        Reg->Reg[i] <<= 1;
        if ((i > 0) && (Reg->Reg[i-1] & (1<<15))) {
            Reg->Reg[i] |= 1;
        }
    }
}
__host__ __device__
void clearShiftRegister(ShiftRegister* Reg) {
    for (short i = 0; i < `(shift_register_words`); i++) {
        Reg->Reg[i] = 0;
    }
}
__host__ __device__
void flipShiftRegisterBit(ShiftRegister* Reg, short& BitIndex) {
    Reg->Reg[BitIndex / 16] ^= (1 << (BitIndex % 16));
}
void printShiftRegister(ShiftRegister* Reg) {
    for (int j = `(shift_register_words`)-1; j >= 0; j--) {
        cout << bitset<16>(Reg->Reg[j]);
        if (j > 0) cout << "";
    }
    cout << "      ";
    for (int j = `(shift_register_words`)-1; j >= 0; j--) {
        cout << (Reg->Reg[j]);
        if (j > 0) cout << ",";
    }
    cout << endl;
}
    
// SEARCHING TREE
__host__ __device__
TreeItem getCopiedTreeItem(TreeItem* MyTree, int Index) {
    TreeItem NewItem;
    NewItem.ScanMinIndex = MyTree[Index].ScanMinIndex;
    NewItem.ScanMaxIndex = MyTree[Index].ScanMaxIndex;
    for (int i = 0; i < SCAN_LENGTH; i++) {
        NewItem.FailMap[i] = MyTree[Index].FailMap[i];
    }
    return NewItem;
}
__host__ __device__
TreeItem getCopiedTreeItem(TreeItem* TItem) {
    TreeItem NewItem;
    NewItem.ScanMinIndex = TItem->ScanMinIndex;
    NewItem.ScanMaxIndex = TItem->ScanMaxIndex;
    for (int i = 0; i < SCAN_LENGTH; i++) {
        NewItem.FailMap[i] = TItem->FailMap[i];
    }
    return NewItem;
}
__host__ __device__
void addFailToTreeBranch(TreeItem* TreeBranch, int FailIndex, int& LutIndex, LUTRow* Lut) {
    TreeBranch->FailMap[FailIndex] = LutIndex;
    if (Lut[LutIndex].FailCount > 0) {
        if (TreeBranch->ScanMinIndex < 0 || Lut[LutIndex].First < TreeBranch->ScanMinIndex) {
            TreeBranch->ScanMinIndex = Lut[LutIndex].First;
        }
        if (Lut[LutIndex].Last > TreeBranch->ScanMaxIndex) {
            TreeBranch->ScanMaxIndex = Lut[LutIndex].Last;
        }
    }
}
__host__ __device__
void copyTreeItem(TreeItem* MyTree, int Src, int Dst) {
    MyTree[Dst].ScanMinIndex = MyTree[Src].ScanMinIndex;
    MyTree[Dst].ScanMaxIndex = MyTree[Src].ScanMaxIndex;
    for (int i = 0; i < SCAN_LENGTH; i++) {
        MyTree[Dst].FailMap[i] = MyTree[Src].FailMap[i];
    }
}
__host__ __device__
void copyTreeItem(TreeItem* MyTree, TreeItem* Src, int Dst) {
    MyTree[Dst].ScanMinIndex = Src->ScanMinIndex;
    MyTree[Dst].ScanMaxIndex = Src->ScanMaxIndex;
    for (int i = 0; i < SCAN_LENGTH; i++) {
        MyTree[Dst].FailMap[i] = Src->FailMap[i];
    }
}
__host__ __device__
void disableTreeBranch(TreeItem* MyTree, int& Index) {
    MyTree[Index].ScanMinIndex = -2;
}
__host__ __device__
void cleanTree(TreeItem* MyTree, int* TreeSize) {
    bool DidSomething = true;
    while (DidSomething) {
        int i = 0;
        DidSomething = false;
        while (i < *TreeSize) {
            if (MyTree[i].ScanMinIndex < -1) {
                copyTreeItem(MyTree, (*TreeSize)-1, i);
                (*TreeSize)--;
                DidSomething = true;
            }
            i++;
        }
    }
}
void printTreeItem(TreeItem& MyTree) {
    cout << "TreeItem >> ";
    cout << "Min: " << MyTree.ScanMinIndex << " ";
    cout << "Max: " << MyTree.ScanMaxIndex << " ";
    cout << "Fails: ";
    for (int i = 0; i < SCAN_LENGTH; i++) {
        cout << MyTree.FailMap[i] << " ";
    }
    cout << endl;
}
    
// LUT
__host__ __device__
void addToLUT(LUTRow* Row, short Value) {
    if (Row->FailCount < FAILS_PER_CLOCK_CYCLE) {
        if ((Row->First < 0) || (Value < Row->First)) Row->First = Value;
        if ((Row->Last < 0) || (Value > Row->Last)) Row->Last = Value;
        Row->LUT[Row->FailCount] = Value;
        Row->FailCount++;
    }
}
void getLUT(LUTRow* Lut, int& LutSize) {
    int LutMax = LutSize;
    LUTRow* Row = new LUTRow;
    Row->First = -1;
    Row->FailCount = 0;
    Lut[LutSize] = *Row;
    LutSize = 1;    
    int kmax = FAILS_PER_CLOCK_CYCLE;
    if (kmax > SCAN_COUNT) kmax = SCAN_COUNT;
    for (int k = 1; k <= kmax; k++) {
        vector<bool> v(SCAN_COUNT);
        fill(v.end() - k, v.end(), true);
        do {
            short First = -1;
            short Last = -1;
            Row = new LUTRow;
            for (short i = 0; i < SCAN_COUNT; ++i) {
                if (v[i]) {
                    Last = (i);
                    if (First == -1) First = Last;
                    addToLUT(Row, Last);
                }
            }
            if ((Last - First) <= FAILS_VERTICAL_DISTANCE) {
                Lut[LutSize] = *Row;
                LutSize++;
                if (LutSize >= LutMax) {
                    cout << "LUT size exceeded" << endl;
                    return;
                }
            } else {
                delete Row;
            }
        } while (next_permutation(v.begin(), v.end()));
    }
}
void printLutRow(LUTRow& LR) {
    cout << "LUTRow >> ";
    cout << "First: " << LR.First << " ";
    cout << "Last: " << LR.Last << " ";
    cout << "Fails: ";
    for (int i = 0; i < LR.FailCount; i++) {
        cout << LR.LUT[i] << " ";
    }
    cout << endl;
}
    
`if not cpu_debug:
__global__ 
`endif
void kernel(TreeItem* MyTree, int TreeSize, int* NewTreeSize, LUTRow* Lut, int LutSize,
        CompactorRegisters* GivenCompactorOutput, CompactorRegisters* SimulatorCompactor, int Cycles) {
`if cpu_debug:
    int EnvIndex = 0;
`else:
    int EnvIndex = threadIdx.x + blockIdx.x * blockDim.x;
`endif
    int BranchIndex = EnvIndex;
`for rdi in range(len(compactor_registers)):
`   reg_definition = compactor_registers[rdi]
`   if reg_definition[0] != 0:
    short aux;
`       break
`   endif
`endfor
    short OutputValues[COMPACTOR_REGISTERS_COUNT];
`for rdi in range(len(compactor_registers)):
`   reg_definition = compactor_registers[rdi]
`   if reg_definition[0] != 0:
    ShiftRegister ShiftReg`(rdi`);
`   endif
`endfor
    while (BranchIndex < TreeSize) {
        bool BranchOverwritten = false;
        TreeItem BaseBranch = getCopiedTreeItem(MyTree, BranchIndex);
        CompactorRegisters MyCompactor = SimulatorCompactor[EnvIndex];
        for (int NewLutPosition = 0; NewLutPosition < LutSize; NewLutPosition++) {
            TreeItem MyBranch = getCopiedTreeItem(&BaseBranch);
            if (Cycles <= SCAN_LENGTH)
                addFailToTreeBranch(&MyBranch, Cycles-1, NewLutPosition, Lut);
            short TotalFails = 0;
            short FirstNonZeroCycle = -1;
            short LastNonZeroCycle = -1;
            for (short CycleIndex = 0; CycleIndex < (Cycles>SCAN_LENGTH ? SCAN_LENGTH : Cycles); CycleIndex++) {
                short fc = Lut[MyBranch.FailMap[CycleIndex]].FailCount;
                if (fc > 0) {
                    LastNonZeroCycle = CycleIndex;
                    if (FirstNonZeroCycle < 0) {
                        FirstNonZeroCycle = CycleIndex;
                    }
                }
                TotalFails += fc;
            }
            if (TotalFails > MAX_TOTAL_FAIL_COUNT) {
                continue;
            } 
            if (MyBranch.ScanMaxIndex - MyBranch.ScanMinIndex > FAILS_VERTICAL_DISTANCE) {
                continue;
            }
            if (LastNonZeroCycle - FirstNonZeroCycle > FAILS_HORIZONTAL_DISTANCE) {
                continue;
            }
            for (short i = 0; i < COMPACTOR_REGISTERS_COUNT; i++) {
                OutputValues[i] = 0;
            }
            clearCompactorRegisters(&MyCompactor);
`for rdi in range(len(compactor_registers)):
`   reg_definition = compactor_registers[rdi]
`   if reg_definition[0] != 0:
            clearShiftRegister(&ShiftReg`(rdi`));
`   endif
`endfor
`if cpu_debug:
            if (Cycles > 32) {
                cout << "BRANCH:";
                printTreeItem(MyBranch);
            }
`endif
            for (short CycleIndex = 0; CycleIndex < Cycles; CycleIndex++) {
                short CycleScanValues[SCAN_COUNT];
                for (short i = 0; i < SCAN_COUNT; i++) {
                    CycleScanValues[i] = 0;
                }            
                if (CycleIndex <= SCAN_LENGTH) {
                    LUTRow Fails = Lut[MyBranch.FailMap[CycleIndex]];
                    for (short fi = 0; fi < Fails.FailCount; fi++) {
                        CycleScanValues[Fails.LUT[fi]] = 1;
                    }
                }
`for rdi in range(len(compactor_registers)):
`   reg_definition = compactor_registers[rdi]
`   if reg_definition[0] == 0:
                OutputValues[`(rdi`)] = 0;
                for (short i = 0; i < SCAN_COUNT; i++) {
                    OutputValues[`(rdi`)] ^= CycleScanValues[i];
                }
`   else:
                OutputValues[`(rdi`)] = getShiftRegisterBit(&ShiftReg`(rdi`), `(shift_register_size-1`));
                shiftShiftRegister(&ShiftReg`(rdi`));
`       dir_up = 1 if reg_definition[0] > 0 else false
`       xoring = abs(reg_definition[0])
`       offset = reg_definition[1]
                for (short SCIndex = 0; SCIndex < SCAN_COUNT; SCIndex++) {
`       if xoring == 1:
`           if dir_up:
                    aux = CycleScanValues[(SCIndex + `(offset`)) % SCAN_COUNT];
`           else:
                    aux = CycleScanValues[((SCAN_COUNT-1) - (SCIndex + `(offset`))) % SCAN_COUNT];
`           endif
`       else:
                    aux = 0;
                    for (short k = 0; k < `(xoring`); k++) {
`           if dir_up:
                        aux ^= CycleScanValues[(SCIndex + `(offset`) + k) % SCAN_COUNT];
`           else:
                        aux ^= CycleScanValues[((SCAN_COUNT-1) - (SCIndex + `(offset`) + k)) % SCAN_COUNT];
`           endif
                    }
`       endif
                    if (aux) flipShiftRegisterBit(&ShiftReg`(rdi`), SCIndex);
                }
`   endif
`endfor
`if cpu_debug:
                if (Cycles > 32) {
                    cout << "Cycle " << CycleIndex << " : OutpuCycleScanValuestValues = ";
                    for (short i = 0; i < SCAN_COUNT; i++) {
                        cout << CycleScanValues[i];
                    }            
                    cout << "   OutputVal = ";
                    for (short i = 0; i < COMPACTOR_REGISTERS_COUNT; i++) {
                        cout << OutputValues[i] ;
                    }
                    cout << endl;
                }
`endif
                pushCompactorValue(&MyCompactor, OutputValues);
            }
            if (areCompactorsEqual(&MyCompactor, GivenCompactorOutput)) {
                int AuxIndex;
                if (BranchOverwritten) {
`if cpu_debug:
                    AuxIndex = (*NewTreeSize);
                    (*NewTreeSize)++;
                //cout << "CORRECT BRANCH:" << AuxIndex << " " << *NewTreeSize << endl;
`else:
                    AuxIndex = atomicAdd(NewTreeSize, 1);
`endif
                } else {
                    BranchOverwritten = true;
                    AuxIndex = BranchIndex;
                }
                copyTreeItem(MyTree, &MyBranch, AuxIndex);
            }
`if cpu_debug:
            if (Cycles > 32) {
                printCompactorRegisters(&MyCompactor);
            }
`endif
            if (Cycles > SCAN_LENGTH) {
                break;
            }
        }
        if (!BranchOverwritten) {
            disableTreeBranch(MyTree, BranchIndex);
        }
`if cpu_debug:
        BranchIndex += 1;
`else:
        BranchIndex += blockDim.x * gridDim.x;
`endif
    }
}
    
__global__ 
void kernel_cleanup(TreeItem* MyTree, int* TreeSize) {
    int tid = threadIdx.x + blockIdx.x * blockDim.x;
    if (tid == 0) {
        cleanTree(MyTree, TreeSize);
    }
}
    
int main() {
    clock_t global_c_start = clock();
    clock_t c_start = 0;
    clock_t c_end = 0;
    double time_elapsed_ms = 0;
    
    cout << "['''" << endl;
    cout << "CUDA --------------------------------" << endl;
    cout << "Blocks                      : " << `(cuda_blocks`) << endl;
    cout << "Threads per block           : " << `(cuda_threads`) << endl;

    cout << "COMPACTOR ----------------------------" << endl;
    cout << "# Compactor Registers      : " << COMPACTOR_REGISTERS_COUNT << endl;
    cout << "Compactor Register length  : " << COMPACTOR_REGISTER_SIZE << endl;
    cout << "CompactorRegister size     : " << sizeof(CompactorRegister) << " B" << endl;
    cout << "CompactorRegisters size    : " << sizeof(CompactorRegisters) << " B" << endl;
    CompactorRegisters* SimulatorCompactor = new CompactorRegisters[`(cuda_grid_size`)];
    cout << "SimulatorCompactor size    : " << `(cuda_grid_size`) * sizeof(CompactorRegisters) / (1024) << " kB" << endl;
    CompactorRegisters* SimulatorCompactor_dev = nullptr;
    c_start = clock();
    cudaMalloc(&SimulatorCompactor_dev, `(cuda_grid_size`) * sizeof(CompactorRegisters));
    c_end = clock();
    time_elapsed_ms = 1000.0 * (c_end-c_start) / CLOCKS_PER_SEC;
    cout << "GPU memory allocated in    : " << time_elapsed_ms << " ms" << endl;
    c_start = clock();
    cudaMemcpy(SimulatorCompactor_dev, SimulatorCompactor, `(cuda_grid_size`) * sizeof(CompactorRegisters), cudaMemcpyHostToDevice);
    c_end = clock();
    time_elapsed_ms = 1000.0 * (c_end-c_start) / CLOCKS_PER_SEC;
    cout << "Compactors copied to GPU in :" << time_elapsed_ms << " ms" << endl;
`if not cpu_debug:
    delete[] SimulatorCompactor;
`endif
    
    // FailMap at compactor output
    CompactorRegisters* GivenCompactorOutput = new CompactorRegisters;
`for c_reg in range(compactor_registers_count):
`    r_val = compactor_given_result[c_reg].copy()
`    for c_word in range(compactor_register_words):
`        result = ''
`        for c_bit in range(16):
`            result = str(r_val[0]) + result
`            r_val <<= 1
`        end
    GivenCompactorOutput->Regs[`(c_reg`)].Reg[`(c_word`)] = 0b`(result`);
`    end
`end
    cout << "Given compactor reg values :" << endl;
    printCompactorRegisters(GivenCompactorOutput);
    CompactorRegisters* GivenCompactorOutput_dev = nullptr;
    cudaMalloc(&GivenCompactorOutput_dev, sizeof(CompactorRegisters));
    cudaMemcpy(GivenCompactorOutput_dev, GivenCompactorOutput, sizeof(CompactorRegisters), cudaMemcpyHostToDevice);

    cout << "LUT ----------------------------------" << endl;
    int LutSize = MAX_LUT_SIZE;
    LUTRow* LutAux = new LUTRow[LutSize];
    getLUT(LutAux, LutSize);
    LUTRow* Lut = (LUTRow*)malloc(LutSize * sizeof(LUTRow));
    memcpy(Lut, LutAux, LutSize * sizeof(LUTRow));
    delete[] LutAux;
    // LUT is ready in Lut[LutSize]
    cout << "# Fails per clock cycle    : " << FAILS_PER_CLOCK_CYCLE << endl;
    cout << "LUT row size               : " << sizeof(LUTRow) << " B" << endl;
    cout << "LUT items                  : " << LutSize << endl;
    cout << "LUT size                   : " << LutSize * sizeof(LUTRow) << " B" << endl;
`if cpu_debug:
    for (int i = 0; i < LutSize; i++) {
        cout << i << "\t: ";
        printLutRow(Lut[i]);
    }
`endif
    LUTRow* Lut_dev = nullptr;
    c_start = clock();
    cudaMalloc(&Lut_dev, LutSize * sizeof(LUTRow));
    c_end = clock();
    time_elapsed_ms = 1000.0 * (c_end-c_start) / CLOCKS_PER_SEC;
    cout << "GPU memory allocated in    : " << time_elapsed_ms << " ms" << endl;
    c_start = clock();
    cudaMemcpy(Lut_dev, Lut, LutSize * sizeof(LUTRow), cudaMemcpyHostToDevice);
    c_end = clock();
    time_elapsed_ms = 1000.0 * (c_end-c_start) / CLOCKS_PER_SEC;
    cout << "LUT copied to GPU in       : " << time_elapsed_ms << " ms" << endl;
    
    cout << "SEARCHING TREE -----------------------" << endl;
    TreeItem* SearchingTree = new TreeItem[TREE_BRANCHES];
    cout << "TreeItem size              : " << sizeof(TreeItem) << " B" << endl;
    cout << "# Max branches             : " << TREE_BRANCHES / 1000000 << "M" << endl;
    cout << "Max tree size              : " << TREE_BRANCHES * sizeof(TreeItem) / (1024*1024) << " MB" << endl;
    // CUDA memory allocation
    c_start = clock();
    TreeItem* SearchingTree_dev = nullptr;
    cudaMalloc(&SearchingTree_dev, TREE_BRANCHES * sizeof(TreeItem));
    int* NewTreeSize_dev = nullptr;
    cudaMalloc(&NewTreeSize_dev, sizeof(int));
    c_end = clock();
    time_elapsed_ms = 1000.0 * (c_end-c_start) / CLOCKS_PER_SEC;
    cout << "GPU memory allocated in    : " << time_elapsed_ms << " ms" << endl;
    int TreeSize = 0;
    for (int i = 0; i < LutSize; i++) {
        SearchingTree[TreeSize].ScanMinIndex = Lut[i].First;
        SearchingTree[TreeSize].ScanMaxIndex = Lut[i].Last;
        SearchingTree[TreeSize].FailMap[0] = i;
        TreeSize++;
    }
    cout << "Branches before 1st iter.  : " << TreeSize << endl;
    c_start = clock();
    cudaMemcpy(SearchingTree_dev, SearchingTree, TreeSize * sizeof(TreeItem), cudaMemcpyHostToDevice);
    cudaMemcpy(NewTreeSize_dev, &TreeSize, sizeof(int), cudaMemcpyHostToDevice);
    c_end = clock();
    time_elapsed_ms = 1000.0 * (c_end-c_start) / CLOCKS_PER_SEC;
    cout << "Tree size before 1st iter. : " << TreeSize * sizeof(TreeItem) / (1024) << " kB" << endl;
    cout << "Tree copied to GPU in      : " << time_elapsed_ms << " ms" << endl;
    cout << "--------------------------------------" << endl;
    cout << endl;

    cout << "SIMULATION START =====================" << endl;

    int* NewTreeSize = new int;
    short Cycle = 2;
    while (Cycle <= COMPACTOR_REGISTER_SIZE) {
        cout << "--- Cycle " << Cycle << "\t---" << endl;
        cudaMemcpy(SearchingTree_dev, SearchingTree, TreeSize * sizeof(TreeItem), cudaMemcpyHostToDevice);
        cudaMemcpy(NewTreeSize_dev, &TreeSize, sizeof(int), cudaMemcpyHostToDevice);
        c_start = clock();
`if cpu_debug:
        *NewTreeSize = TreeSize;
        kernel(SearchingTree, TreeSize, NewTreeSize, Lut, LutSize,
            GivenCompactorOutput, SimulatorCompactor, Cycle);
        TreeSize = *NewTreeSize;
`else:
        kernel<<<`(cuda_blocks`), `(cuda_threads`)>>>(SearchingTree_dev, TreeSize, NewTreeSize_dev, Lut_dev, LutSize,
            GivenCompactorOutput_dev, SimulatorCompactor_dev, Cycle);
`endif
        c_end = clock();
        time_elapsed_ms = 1000.0 * (c_end-c_start) / CLOCKS_PER_SEC;
        cout << "Kernel execution time      : " << time_elapsed_ms << " ms" << endl;
`if not cpu_debug:
        cudaMemcpy(&TreeSize, NewTreeSize_dev, sizeof(int), cudaMemcpyDeviceToHost);
`endif
        cout << "Tree branches before clean : " << TreeSize << endl;
        cout << "Tree size before clean     : " << TreeSize * sizeof(TreeItem) / (1024*1024) << " MB" << endl;
`if not cpu_debug:
        cudaMemcpy(SearchingTree, SearchingTree_dev, TreeSize * sizeof(TreeItem), cudaMemcpyDeviceToHost);
`endif
        //kernel_cleanup<<<1, 1>>>(SearchingTree_dev, NewTreeSize_dev);
        //cudaMemcpy(&TreeSize, NewTreeSize_dev, sizeof(int), cudaMemcpyDeviceToHost);
        cleanTree(SearchingTree, &TreeSize);
        cout << "Tree branches - final      : " << TreeSize << endl;
        cout << "Tree size - final          : " << TreeSize * sizeof(TreeItem) / (1024*1024) << " MB" << endl;
        if (Cycle ==  SCAN_LENGTH)
            Cycle = COMPACTOR_REGISTER_SIZE;
        else
            Cycle += 1;
    }
    cudaMemcpy(SearchingTree, SearchingTree_dev, TreeSize * sizeof(TreeItem), cudaMemcpyDeviceToHost);
    
    clock_t global_c_end = clock();
    time_elapsed_ms = 1000.0 * (global_c_end-global_c_start) / CLOCKS_PER_SEC;
    cout << "SIMULATION END =======================" << endl;
    cout << "Total time elapsed          : " << time_elapsed_ms << " ms" << endl;

    cout << "'''," << endl;

    cout << "[ " << endl;
    for (int LutIndex = 0; LutIndex < LutSize; LutIndex++) {
        cout << "[";
        for (short i = 0; i < Lut[LutIndex].FailCount; i++) {
            cout << Lut[LutIndex].LUT[i] << ",";
        }
        cout << "],";
    }
    cout << "]," << endl;

    cout << "[ " << endl;
    for (int TreeIndex = 0; TreeIndex < TreeSize; TreeIndex++) {
        cout << "[";
        for (short i = 0; i < SCAN_LENGTH; i++) {
            cout << SearchingTree[TreeIndex].FailMap[i] << ",";
        }
        cout << "],";
    }
    cout << "]," << endl;

    cout << TreeSize << "," << time_elapsed_ms << "," << endl;

    cout << "]" << endl;
    return 0;
}