import sys
import time

'''
LIST OF FUNCTIONS
'''

# function to write the results
def write_result(result):
    if len(result[0]) < 8:
        f.write(result[0] + "\t\t\t\t")
    elif len(result[0]) < 16:
        f.write(result[0] + "\t\t\t")
    elif len(result[0]) < 24:
        f.write(result[0] + "\t\t")
    else:
        f.write(result[0] + "\t")
    for i in range(1, len(result)):
        f.write(result[i] + "\t\t")
    f.write("\n")

class result:
    def __init__(self, inst):
        self.inst = inst
        self.fetch = 0
        self.issue = 0
        self.read = 0
        self.exec = 0
        self.write = 0
        self.raw = "N"
        self.waw = "N"
        self.struc = "N"

    def print(self):
        # print(self.inst, self.fetch, self.issue, self.read, self.exec, self.write, self.raw, self.waw, self.struc)
        print(self.fetch)

# accepting the commandline arguments
instructions_file = sys.argv[1]
data_file = sys.argv[2]
config_file = sys.argv[3]
result_file = sys.argv[4]

# read the respective files and parsing input
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

# initialize the variables (program counter and clock cycle) for the simulation
cycle = 1
pc = 0

fetch = 0

status = []
results = []
# define the main simulation loop
while len(status) != 0 or cycle == 1:

    # parse the instruction into the "current" variable
    if pc < len(instructions):
        if ":" in instructions[pc]:
            current = instructions[pc][instructions[pc].index(":")+1:].split()
        else:
            current = instructions[pc].split()

        status.append(result(instructions[pc]))

    i = 0
    while i < len(status):
        if status[i].fetch == 0:
            status[i].fetch = cycle
        elif status[i].issue == 0:
            status[i].issue = cycle
        elif status[i].read == 0:
            status[i].read = cycle
        elif status[i].exec == 0:
            status[i].exec = cycle
        elif status[i].write == 0:
            status[i].write = cycle
            results.append(status.pop(i))
            # print(results)
            continue
        i += 1

    if pc < len(instructions):
        # if-ladder to decide action based on instruction
        if current[0].lower() == "li":
            R[current[1].strip(",")] = int(current[2])
            # print(R)
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
            # print(R)
        elif current[0].lower() == "dsub":
            print(f"Subtracting {current[3]} from {current[2]} into {current[1]}")
            R[current[1].strip(",")] = R[current[2].strip(",")] - R[current[3].strip(",")]
            # print(R)
        elif current[0].lower() == "bne":
            print(f"Comparing {current[2]} and {current[1]} and jumping to {current[3]}")
            if R[current[1].strip(",")] != R[current[2].strip(",")]:
                pc = branch[current[3]]-1
        elif current[0].lower() == "hlt":
            print(f"STOP!")

        # time.sleep(1)

    # increment the program counter and clock cycle by 1
    pc += 1
    cycle += 1

print(results)

for stat in results:
    stat.print()

# write the obtained results to the specified output file
# with open(result_file, 'w') as f:
#     f.write("\tInstruction\t\tFetch\t\tIssue\t\tRead\t\tExec\t\tWrite\t\tRAW\t\tWAW\t\tStruct\n")
#     for i in range(len(results)):
#         write_result(results[i])

# indicate termination of simulation
print("Done!")