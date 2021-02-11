import sys
import time

# define the instruction class
class inst:
    def __init__(self, inst, pc):

        # store the original instruction
        self.inst = inst
        self.pc = pc

        # parse the instruction to know the read and store registers
        if ":" in inst:
            temp = inst[inst.index(":") + 1:].split()
        else:
            temp = inst.split()
        self.keyword = temp[0].lower()
        self.args = []
        for i in range(1,4):
            try:
                self.args.append(temp[i].strip(","))
            except IndexError:
                self.args.append(-1)

        # define the instruction's attributes
        self.fetch = 0
        self.issue = 0
        self.read = 0
        self.exec = 0
        self.write = 0
        self.status = 0
        self.raw = "N"
        self.waw = "N"
        self.struct = "N"

    # function to check the contents of the instruction
    def print(self):
        print(self.inst, self.fetch, self.issue, self.read, self.exec, self.write, self.raw, self.waw, self.struct)

    # function to check if the instruction uses the ALU
    def is_ALU_inst(self):
        if self.keyword == "dadd" or self.keyword == "daddi" or self.keyword == "dsub" or self.keyword == "dsubi" or self.keyword == "and" or self.keyword == "andi" or self.keyword == "or" or self.keyword == "ori" or self.keyword == "li" or self.keyword == "lui":
            return True
        return False

    # function to check if the instruction is lw or sw
    def is_dataword_inst(self):
        if self.keyword == "lw" or self.keyword == "sw":
            return True
        return False

    # function to check if the instruction is ld or sd
    def is_datadouble_inst(self):
        if self.keyword == "l.d" or self.keyword == "s.d":
            return True
        return False

    # function to check if the instruction uses the FP adder
    def is_FPadd_inst(self):
        if self.keyword == "add.d" or self.keyword == "sub.d":
            return True
        return False

    # function to check if the instruction uses the FP multiplier
    def is_FPmult_inst(self):
        if self.keyword == "mul.d":
            return True
        return False

    # function to check if the instruction uses the FP divider
    def is_FPdiv_inst(self):
        if self.keyword == "div.d":
            return True
        return False

    # function to check if the instruction is a branch instruction
    def is_branch_inst(self):
        if self.keyword == "bne" or self.keyword == "beq":
            return True
        return False

# define the scoreboard class
class scoreboard:

    def __init__(self, config_file):

        # read the respective files and parsing input into variables
        with open(config_file, 'r') as f:
            temp = f.readline().split(":")[-1]
            self.FP_add_units, self.FP_add_cycle = int(temp.split(",")[0]), int(temp.split(",")[1])
            temp = f.readline().split(":")[-1]
            self.FP_mult_units, self.FP_mult_cycle = int(temp.split(",")[0]), int(temp.split(",")[1])
            temp = f.readline().split(":")[-1]
            self.FP_div_units, self.FP_div_cycle = int(temp.split(",")[0]), int(temp.split(",")[1])
            temp = f.readline().split(":")[-1]
            self.I_cache_size, self.I_block_size = int(temp.split(",")[0]), int(temp.split(",")[1])

        # initialize the registers
        self.R = {}
        for i in range(32):
            self.R["R" + str(i)] = 0

        # initialize the processing units:
        self.ALU_status = 0
        self.FP_add_status = [0] * self.FP_add_units
        self.FP_mult_status = [0] * self.FP_mult_units
        self.FP_div_status = [0] * self.FP_div_units
        self.load_status = 0
        self.stall = 0

        # define the D-cache and I-cache and the bus
        self.D_cache = [[(-1, -1), (-1, -1)], [(-1, -1), (-1, -1)]]
        self.I_cache = [-1] * self.I_cache_size
        self.bus = 0

        # provide overview of input
        print("-----FUNCTIONAL UNITS-----")
        print(f"There is only one ALU unit.")
        print(f"There are {len(self.FP_add_status)} FP Adder Unit(s), each with a latency of {self.FP_add_cycle} cycles.")
        print(f"There are {len(self.FP_mult_status)} FP Multiplier Unit(s), each with a latency of {self.FP_mult_cycle} cycles.")
        print(f"There are {len(self.FP_div_status)} FP Divider Unit(s), each with a latency of {self.FP_div_cycle} cycles.\n")

        print("-----CACHE ORGANIZATION-----")
        print(f"There are 2 types of cache used, I-Cache and D-cache.")
        print(f"The I-Cache is a direct-mapped cache with each block having a size of {self.I_block_size} words and a total I-Cache size of {len(self.I_cache)} blocks.")
        print(f"The D-cache is a 2-way set associative cache, with each block having a size of 4 words and a total D-Cache size of 4 blocks.")

        # define the pc and the clock cycle
        self.clock_cycle = 0
        self.pc = 0
        self.oldpc = -1

        # define the list of active and completed instructions
        self.active = []
        self.complete = []
        self.tobewritten = []

    # method to fetch instructions
    def fetch_inst(self, inst):
        for i in range(len(self.active)):
            if self.active[i].fetch != 0 and self.active[i].issue == 0:
                break
        else:
            inst.fetch = self.clock_cycle
            self.pc += 1

    # method to issue instructions
    def issue_inst(self, inst):

        # check if the pipeline has been stalled
        if self.stall != 1:

            # if the instruction uses the ALU unit
            if inst.is_ALU_inst():

                # check for structural hazards and WAW hazards
                if self.ALU_status == 0 and inst.args[0] not in self.tobewritten:
                    inst.issue = self.clock_cycle

                    # set ALU unit to busy
                    self.ALU_status = 1
                else:
                    if self.ALU_status == 1:
                        inst.struct = "Y"
                    if inst.args[0] in self.tobewritten:
                        inst.waw = "Y"

            # if the instruction is a data transfer instruction
            elif inst.is_datadouble_inst() or inst.is_dataword_inst():

                # check for structural hazards and WAW hazards
                if self.load_status == 0 and inst.args[0] not in self.tobewritten:
                    inst.issue = self.clock_cycle

                    # set loading unit to busy
                    self.load_status = 1
                else:
                    if self.load_status == 1:
                        inst.struct = "Y"
                    if inst.args[0] in self.tobewritten:
                        inst.waw = "Y"

            # if the instruction is a FP add instruction
            elif inst.is_FPadd_inst():

                # check for structural and WAW hazards
                if 0 in self.FP_add_status and inst.args[0] not in self.tobewritten:
                    inst.issue = self.clock_cycle

                    # set one of the FP add units to busy
                    for k in range(len(self.FP_add_status)):
                        if self.FP_add_status[k] == 0:
                            self.FP_add_status[k] = 1
                            break
                else:
                    if 0 not in self.FP_add_status:
                        inst.struct = "Y"
                    if inst.args[0] in self.tobewritten:
                        inst.waw = "Y"

            # if the instruction is a FP mult instruction
            elif inst.is_FPmult_inst():

                # check for structural and WAW hazards
                if 0 in self.FP_mult_status and inst.args[0] not in self.tobewritten:
                    inst.issue = self.clock_cycle

                    # set one of the FP mult units to busy
                    for k in range(len(self.FP_mult_status)):
                        if self.FP_mult_status[k] == 0:
                            self.FP_mult_status[k] = 1
                            break
                else:
                    if 0 not in self.FP_mult_status:
                        inst.struct = "Y"
                    if inst.args[0] in self.tobewritten:
                        inst.waw = "Y"

            # if the instruction is a FP div instruction
            elif inst.is_FPdiv_inst():

                # check for structural and WAW hazards
                if 0 in self.FP_div_status and inst.args[0] not in self.tobewritten:
                    inst.issue = self.clock_cycle
                    for k in range(len(self.FP_div_status)):
                        if self.FP_div_status[k] == 0:
                            self.FP_div_status[k] = 1
                            break
                else:
                    if 0 not in self.FP_div_status:
                        inst.struct = "Y"
                    if inst.args[0] in self.tobewritten:
                        inst.waw = "Y"

            # if the instruction is a branching instruction
            elif inst.is_branch_inst():
                inst.issue = self.clock_cycle

                # stall the pipeline
                self.stall = 1

            # if it is any other instruction (J or HLT)
            else:
                inst.issue = self.clock_cycle

    # method to read instructions
    def read_inst(self, inst):

        # if instruction is not a branch instruction
        if not inst.is_branch_inst():

            # check for RAW hazard
            block = 0
            for i in range(1,len(inst.args)):
                if inst.args[i] != -1 and inst.args[i] in self.tobewritten:
                    block = 1
            if block == 0:
                inst.read = self.clock_cycle
                # self.tobewritten.append(inst.args[0])
            else:
                inst.raw = "Y"

        # if the instruction is a branch instruction
        else:

            # check for RAW hazard
            block = 0
            for i in range(0, 2):
                if inst.args[i] in self.tobewritten:
                    block = 1
            if block == 0:
                inst.read = self.clock_cycle

                # check if the branch condition is satisfied, and change PC if necessary
                if (inst.keyword == "bne" and self.R[inst.args[0]] != self.R[inst.args[1]]) or (inst.keyword == "beq" and self.R[inst.args[0]] == self.R[inst.args[1]]):
                    self.pc = branch[inst.args[2]]
                    self.stall = 0

                    # flush the pipeline if branch is taken
                    k = 0
                    while len(self.active) != 0 and k < len(self.active):
                        self.complete.append(self.active.pop(k))
            else:
                inst.raw = "Y"

    # method to execute instructions
    def exec_inst(self, inst):

        # if the instruction is an ALU instruction or a SW or LW instruction --> 1 clock cycle:
        if inst.is_ALU_inst() or inst.is_dataword_inst():
            inst.exec = self.clock_cycle

        # if the instruction is a S.D or L.D instruction --> 2 clock cycles:
        elif inst.is_datadouble_inst():
            if inst.status == 0:
                inst.status = 1
            else:
                inst.status -= 1
                if inst.status == 0:
                    inst.exec = self.clock_cycle

        # if the instruction is a FP Add instruction --> x clock cycles:
        elif inst.is_FPadd_inst():
            if inst.status == 0:
                inst.status = self.FP_add_cycle - 1
            else:
                inst.status -= 1
                if inst.status == 0:
                    inst.exec = self.clock_cycle

        # if the instruction is a FP Mult instruction --> y clock cycles:
        elif inst.is_FPmult_inst():
            if inst.status == 0:
                inst.status = self.FP_mult_cycle - 1
            else:
                inst.status -= 1
                if inst.status == 0:
                    inst.exec = self.clock_cycle

        # if the instruction is a FP Div instruction --> z clock cycles:
        elif inst.is_FPdiv_inst():
            if inst.status == 0:
                inst.status = self.FP_div_cycle - 1
            else:
                inst.status -= 1
                if inst.status == 0:
                    inst.exec = self.clock_cycle

    # method to write instructions
    def write_inst(self, inst):
        inst.write = self.clock_cycle

        # check if the instructions change the registers' values, and apply necessary changes
        if inst.keyword == "li":
            self.R[inst.args[0]] = int(inst.args[1])
        if inst.keyword == "daddi":
            self.R[inst.args[0]] = self.R[inst.args[1]] + int(inst.args[2])
        if inst.keyword == "dsub":
            self.R[inst.args[0]] = self.R[inst.args[1]] - self.R[inst.args[2]]

    # method to free the corresponding resources used by the instruction
    def free(self, inst):

        # if the instruction uses the ALU unit
        if inst.is_ALU_inst():
            self.ALU_status = 0

        # if the instruction is a load
        if inst.is_dataword_inst() or inst.is_datadouble_inst():
            self.load_status = 0

        # if the instruction is a FP add instruction
        if inst.is_FPadd_inst():
            for k in range(len(self.FP_add_status)):

                # set status of any busy FP adder to 0
                if self.FP_add_status[k] == 1:
                    self.FP_add_status[k] = 0
                    break

        # if the instruction is a FP mult instruction
        if inst.is_FPmult_inst():
            for k in range(len(self.FP_mult_status)):

                # set status of any busy FP multiplier to 0
                if self.FP_mult_status[k] == 1:
                    self.FP_mult_status[k] = 0
                    break

        # if the instruction is a FP div instruction
        if inst.is_FPdiv_inst():
            for k in range(len(self.FP_div_status)):

                # set status of any busy FP divider to 0
                if self.FP_div_status[k] == 1:
                    self.FP_div_status[k] = 0
                    break

        # if the instruction is a branching instruction, remove the pipeline stall
        if inst.is_branch_inst():
            self.stall = 0

        # if it is not a branching instruction, remove the target register from the to-be-written list
        if not inst.is_branch_inst():
            self.tobewritten.remove(inst.args[0])

    # method to simulate the pipeline
    def simulate(self, instructions_list):

        # while the pc is still valid
        while(self.pc < len(instructions_list)):

            # increase the clock_cycle each time
            self.clock_cycle += 1
            # print(f"At clock cycle {self.clock_cycle}: ", self.pc, self.oldpc)

            # if the PC has been updated, and the pipeline is not stalled, add new instructions
            if self.oldpc != self.pc and self.stall != 1:
                self.active.append(inst(instructions_list[self.pc], self.pc))
                self.oldpc = self.pc

            # check the status of all the active instructions and choose action correspondingly
            i = 0
            while i < len(self.active):
                if self.active[i].fetch == 0:
                    self.fetch_inst(self.active[i])
                elif self.active[i].issue == 0:
                    self.issue_inst(self.active[i])
                elif self.active[i].read == 0:
                    self.read_inst(self.active[i])
                elif self.active[i].exec == 0:
                    self.exec_inst(self.active[i])
                elif self.active[i].write == 0:
                    self.write_inst(self.active[i])
                i += 1

            # loop to check for completed instructions and free up the necessary resources
            i = 0
            while i < len(self.active):

                # condition to free non-branch instructions
                if not self.active[i].is_branch_inst() and self.active[i].write != 0:
                    self.free(self.active[i])
                    self.complete.append(self.active.pop(i))
                    continue

                # condition to free branch instructions
                elif self.active[i].is_branch_inst() and self.active[i].read != 0:
                    self.free(self.active[i])
                    self.complete.append(self.active.pop(i))
                    continue
                i += 1

            # for i in range(len(self.complete)):
            #     self.complete[i].print()
            # for i in range(len(self.active)):
            #     self.active[i].print()

            # time.sleep(0.1)
            # print("\n")

        # final flush the pipeline
        k = 0
        while len(self.active) != 0 and k < len(self.active):
            self.complete.append(self.active.pop(k))

        # return the list of completed instructions
        return self.complete

    @staticmethod
    def I_cache_hit(inst):
        pass

    @staticmethod
    def I_cache_miss(inst):
        pass


# parse the command-line arguments
instructions_file = sys.argv[1]
data_file = sys.argv[2]
config_file = sys.argv[3]
result_file = sys.argv[4]

s = scoreboard(config_file)

# parse the instructions and the data files
with open(instructions_file, 'r') as f:
    instructions = f.read()
    instructions = instructions.split("\n")
with open(data_file, 'r') as f:
    data = f.read()
    data = data.split()

# map labels to their corresponding instruction for easy branch jumping
branch = {}
for i, j in enumerate(instructions):
    if ":" in j:
        branch[j.split(":")[0].strip()] = i

final = s.simulate(instructions)
final.sort(key = lambda x: x.fetch)
over = []
for i in range(len(final)):
    over.append([final[i].inst, str(final[i].fetch), str(final[i].issue), str(final[i].read), str(final[i].exec), str(final[i].write), final[i].raw, final[i].waw, final[i].struct])

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
            if result[i] == "0":
                result[i] = "-"
            f.write(result[i]+"\t\t")
        f.write("\n")

    for i in range(len(over)):
        write_result(over[i])

print("\nDone!")