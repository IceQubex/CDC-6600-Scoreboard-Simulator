import sys
import time

class scoreboard:

    def __init__(self, instructions_file, data_file, config_file):
        with open(instructions_file, 'r') as f:
            self.instructions = f.read()
            self.instructions = self.instructions.split("\n")
        with open(data_file, 'r') as f:
            self.data = f.read()
            self.data = self.data.split()
        with open(config_file, 'r') as f:
            temp = f.readline().split(":")[-1]
            self.FP_add_units, self.FP_add_cycle = int(temp.split(",")[0]), int(temp.split(",")[1])
            temp = f.readline().split(":")[-1]
            self.FP_mult_units, self.FP_mult_cycle = int(temp.split(",")[0]), int(temp.split(",")[1])
            temp = f.readline().split(":")[-1]
            self.FP_div_units, self.FP_div_cycle = int(temp.split(",")[0]), int(temp.split(",")[1])
            temp = f.readline().split(":")[-1]
            self.I_cache_blocks, self.I_block_size = int(temp.split(",")[0]), int(temp.split(",")[1])

        self.FP_add_status = [0]*self.FP_add_units
        self.FP_mult_status = [0]*self.FP_mult_units
        self.FP_div_status = [0]*self.FP_div_units

        print(self.FP_add_status)
        print(self.FP_mult_status)
        print(self.FP_div_status)

    def run(self):
        for i in



s = scoreboard(sys.argv[1], sys.argv[2], sys.argv[3])
s.run()

# map labels to their corresponding instruction for easy branch jumping
branch = {}
for i, instruction in enumerate(instructions):
    if ":" in instruction:
        branch[instruction.split(":")[0].strip()] = i

# initialize the registers
R = {}
for i in range(32):
    R["R"+str(i)] = 0

# initialize the variables (program counter and clock cycle) for the simulation
cycle = pc = 0

# define the main simulation loop
while pc < len(instructions):

    # parse the instruction into the "current" variable
    if ":" in instructions[pc]:
        current = instructions[pc][instructions[pc].index(":")+1:].split()
    else:
        current = instructions[pc].split()

    # if-ladder to decide action based on instruction
    if current[0].lower() == "li":
        R[current[1].strip(",")] = int(current[2])
        print(R)
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
        print(R)
    elif current[0].lower() == "dsub":
        print(f"Subtracting {current[3]} from {current[2]} into {current[1]}")
        R[current[1].strip(",")] = R[current[2].strip(",")] - R[current[3].strip(",")]
        print(R)
    elif current[0].lower() == "bne":
        print(f"Comparing {current[2]} and {current[1]} and jumping to {current[3]}")
        if R[current[1].strip(",")] != R[current[2].strip(",")]:
            pc = branch[current[3]]
            continue
    elif current[0].lower() == "hlt":
        print(f"STOP!")

    # time.sleep(1)

    # increment the program counter and clock cycle by 1
    pc += 1
    cycle += 1

results = [("LI R1, 260", '1', '2', '3', '4', '5', "N", "N", "N"), ("GG: L.D F1, 4(R4)", '1', '2', '3', '4', '5', "N", "N", "N"), ("DADDI R4, R4, 20", '1', '2', '3', '4', '5', "N", "N", "N"), ("DADDI R20, R20, 3000", '1', '2', '3', '4', '5', "N", "N", "N"), ("HLT", "-", "-")]

with open(result_file, 'w') as f:
    f.write("\tInstruction\t\tFetch\t\tIssue\t\tRead\t\tExec\t\tWrite\t\tRAW\t\tWAW\t\tStruct\n")
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
            f.write(result[i]+"\t\t")
        f.write("\n")

    for i in range(len(results)):
        write_result(results[i])


print("Done!")


