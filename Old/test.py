import sys
import time

# define the instruction class, with the necessary attributes to reflect in the results
class inst:
    def __init__(self, inst, program_counter):
        self.inst = inst
        self.pc = program_counter
        self.fetch = 0
        self.issue = 0
        self.read = 0
        self.exec = 0
        self.write = 0
        self.raw = "N"
        self.waw = "N"
        self.struc = "N"

    def print(self):
        print(self.inst, self.fetch, self.issue, self.read, self.exec, self.write, self.raw, self.waw, self.struc)
        # print(self.fetch)

def I_cache_hit(num):
    if num//I_block_size in I_cache:
        return True
    return False



# accepting the commandline arguments
instructions_file = sys.argv[1]
data_file = sys.argv[2]
config_file = sys.argv[3]
result_file = sys.argv[4]

# read the respective files and parsing input into variables
with open(instructions_file, 'r') as f:
    instructions = f.read()
    instructions = instructions.split("\n")
with open(data_file, 'r') as f:
    data = f.read()
    data = data.split()
with open(config_file, 'r') as f:
    temp = f.readline().split(":")[-1]
    FP_add_units, FP_add_cycle = int(temp.split(",")[0]), int(temp.split(",")[1])
    temp = f.readline().split(":")[-1]
    FP_mult_units, FP_mult_cycle = int(temp.split(",")[0]), int(temp.split(",")[1])
    temp = f.readline().split(":")[-1]
    FP_div_units, FP_div_cycle = int(temp.split(",")[0]), int(temp.split(",")[1])
    temp = f.readline().split(":")[-1]
    I_cache_blocks, I_block_size = int(temp.split(",")[0]), int(temp.split(",")[1])

# map labels to their corresponding instruction for easy branch jumping
branch = {}
for i, instruction in enumerate(instructions):
    if ":" in instruction:
        branch[instruction.split(":")[0].strip()] = i

# initialize the registers
R = {}
for i in range(32):
    R["R"+str(i)] = 0

# initialize the processing units:
ALU_status = [0]
FP_add_status = [0]*FP_add_units
FP_mult_status = [0]*FP_mult_units
FP_div_status = [0]*FP_div_units

# define the D-cache and I-cache
D_cache = [[(0,0),(0,0)],[(0,0),(0,0)]]
I_cache = [0]*I_cache_blocks

# provide overview of input
print("-----FUNCTIONAL UNITS-----")
print(f"There is only one ALU unit.")
print(f"There are {len(FP_add_status)} FP Adder Unit(s), each with a latency of {FP_add_cycle} cycles.")
print(f"There are {len(FP_mult_status)} FP Multiplier Unit(s), each with a latency of {FP_mult_cycle} cycles.")
print(f"There are {len(FP_div_status)} FP Divider Unit(s), each with a latency of {FP_div_cycle} cycles.\n")

print("-----CACHE ORGANIZATION-----")
print(f"There are 2 types of cache used, I-Cache and D-cache.")
print(f"The I-Cache is a direct-mapped cache with each block having a size of {I_block_size} words and a total I-Cache size of {I_cache_blocks} blocks.")
print(f"The D-cache is a 2-way set associative cache, with each block having a size of 4 words and a total D-Cache size of 4 blocks.")

# define the pc and the clock cycle
clock_cycle = 1
pc = 0

active = []
completed = []

while len(active) != 0 or clock_cycle == 1:

    # check if the instructions have finished executing
    if pc < len(instructions):

        # parse the instruction into the "current" variable
        if ":" in instructions[pc]:
            current = instructions[pc][instructions[pc].index(":") + 1:].split()
        else:
            current = instructions[pc].split()

        # add the instruction into the active list
        active.append(inst(instructions[pc], pc))

        # if-ladder to decide action based on instruction
        if current[0].lower() == "li":
            R[current[1].strip(",")] = int(current[2])
        elif current[0].lower() == "l.d":
            print(f"Loading from {current[2]} into {current[1]}")
        elif current[0].lower() == "add.d":
            print(f"Adding {current[3]} and {current[2]} into {current[1]}")
        elif current[0].lower() == "sub.d":
            print(f"Subtracting {current[3]} from {current[2]} into {current[1]}")
        elif current[0].lower() == "mul.d":
            print(f"Multiplying {current[3]} and {current[2]} into {current[1]}")
        elif current[0].lower() == "daddi":
            print(f"Adding immediate {current[3]} and {current[2]} into {current[1]}")
            R[current[1].strip(",")] = R[current[2].strip(",")] + int(current[3].strip(","))
        elif current[0].lower() == "dsub":
            print(f"Subtracting {current[3]} from {current[2]} into {current[1]}")
            R[current[1].strip(",")] = R[current[2].strip(",")] - R[current[3].strip(",")]
        elif current[0].lower() == "bne":
            print(f"Comparing {current[2]} and {current[1]} and jumping to {current[3]}")
            if R[current[1].strip(",")] != R[current[2].strip(",")]:
                pc = branch[current[3]] - 1
        elif current[0].lower() == "hlt":
            print(f"STOP!")


    i = 0
    while i < len(active):
        if active[i].fetch == 0 and I_cache_hit(active[i].pc):
            active[i].fetch = clock_cycle
        elif active[i].issue == 0:
            active[i].issue = clock_cycle
        elif active[i].read == 0:
            active[i].read = clock_cycle
        elif active[i].exec == 0:
            active[i].exec = clock_cycle
        elif active[i].write == 0:
            active[i].write = clock_cycle
            completed.append(active.pop(i))
            continue
        i += 1

    # time.sleep(1)
    clock_cycle += 1

for complete in completed:
    complete.print()

print("Done!")