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
        for i in range(1, 4):
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
        self.status2 = 0
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

    # function to check if the instruction is a store instruction
    def is_store_inst(self):
        if self.keyword == "s.d" or self.keyword == "sw":
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

    def is_jump_inst(self):
        if self.keyword == "j":
            return True
        return False

    def is_hlt_inst(self):
        if self.keyword == "hlt":
            return True
        return False

# define the scoreboard class
class scoreboard:

    def __init__(self, config_file):

        # set this value to 1 for more detailed output in the terminal, set this value to 2 to view the pipeline at each stage
        self.verbose = 2

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

        # initialize the processing units
        self.ALU_status = 0
        self.FP_add_status = [0] * self.FP_add_units
        self.FP_mult_status = [0] * self.FP_mult_units
        self.FP_div_status = [0] * self.FP_div_units
        self.load_status = 0

        # initialize other scoreboard status monitors
        self.stall = 0
        self.end = 0
        self.branch = 0

        # define the D-cache and I-cache and the bus, and counters to keep track of cache access requests
        self.D_cache = [[[-1, -1, 0], [-1, -1, 0]], [[-1, -1, 0], [-1, -1, 0]]]
        self.I_cache = [-1] * self.I_cache_size
        self.bus = 0
        self.totalImiss = 0
        self.totalDmiss = 0

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
        if self.I_cache_access(inst):
            for i in range(len(self.active)):
                if self.active[i].fetch != 0 and self.active[i].issue == 0:
                    if self.verbose >= 1:
                        print(f"Instruction \"{inst.inst}\" cannot complete fetch stage!")
                    break
            else:
                if self.verbose >= 1:
                    print(f"Instruction \"{inst.inst}\" completes fetch stage!")
                inst.fetch = self.clock_cycle
                self.pc += 1

    # method to issue instructions
    def issue_inst(self, inst):

        # check if the pipeline has been stalled
        if self.stall != 1:

            block = 0
            # if the instruction uses the ALU unit
            if inst.is_ALU_inst():

                # check for structural hazards and WAW hazards
                if self.ALU_status == 1:
                    if self.verbose >= 1:
                        print(f"Instruction \"{inst.inst}\" is not issued due to structural hazard.")
                    inst.struct = "Y"
                    block = 1
                for m in range(len(self.tobewritten)):
                    if inst.args[0] == self.tobewritten[m][0] and inst.pc > self.tobewritten[m][1]:
                        if self.verbose >= 1:
                            print(f"Instruction \"{inst.inst}\" is not issued due to WAW hazard.")
                        inst.waw = "Y"
                        block = 1

                if block == 0:
                    self.tobewritten.append((inst.args[0], inst.pc))
                    if self.verbose >= 1:
                        print(f"Instruction \"{inst.inst}\" completes issue stage!")
                    inst.issue = self.clock_cycle
                    # set ALU unit to busy
                    self.ALU_status = 1


            # if the instruction is a data transfer instruction
            elif inst.is_datadouble_inst() or inst.is_dataword_inst():

                # check for structural hazards and WAW hazards
                if self.load_status == 1:
                    if self.verbose >= 1:
                        print(f"Instruction \"{inst.inst}\" is not issued due to structural hazard.")
                    inst.struct = "Y"
                    block = 1
                for m in range(len(self.tobewritten)):
                    if inst.args[0] == self.tobewritten[m][0] and inst.pc > self.tobewritten[m][1] and not inst.is_store_inst():
                        if self.verbose >= 1:
                            print(f"Instruction \"{inst.inst}\" is not issued due to WAW hazard.")
                        inst.waw = "Y"
                        block = 1

                if block == 0:
                    self.tobewritten.append((inst.args[0], inst.pc))
                    if self.verbose >= 1:
                        print(f"Instruction \"{inst.inst}\" completes issue stage!")
                    inst.issue = self.clock_cycle
                    # set loading unit to busy
                    self.load_status = 1

            # if the instruction is a FP add instruction
            elif inst.is_FPadd_inst():

                # check for structural hazards and WAW hazards
                if 0 not in self.FP_add_status:
                    if self.verbose >= 1:
                        print(f"Instruction \"{inst.inst}\" is not issued due to structural hazard.")
                    inst.struct = "Y"
                    block = 1
                for m in range(len(self.tobewritten)):
                    if inst.args[0] == self.tobewritten[m][0] and inst.pc > self.tobewritten[m][1]:
                        if self.verbose >= 1:
                            print(f"Instruction \"{inst.inst}\" is not issued due to WAW hazard.")
                        inst.waw = "Y"
                        block = 1

                if block == 0:
                    self.tobewritten.append((inst.args[0], inst.pc))
                    if self.verbose >= 1:
                        print(f"Instruction \"{inst.inst}\" completes issue stage!")
                    inst.issue = self.clock_cycle
                    # set one of the FP add units to busy
                    for k in range(len(self.FP_add_status)):
                        if self.FP_add_status[k] == 0:
                            self.FP_add_status[k] = 1
                            break


            # if the instruction is a FP mult instruction
            elif inst.is_FPmult_inst():

                # check for structural hazards and WAW hazards
                if 0 not in self.FP_mult_status:
                    if self.verbose >= 1:
                        print(f"Instruction \"{inst.inst}\" is not issued due to structural hazard.")
                    inst.struct = "Y"
                    block = 1
                for m in range(len(self.tobewritten)):
                    if inst.args[0] == self.tobewritten[m][0] and inst.pc > self.tobewritten[m][1]:
                        if self.verbose >= 1:
                            print(f"Instruction \"{inst.inst}\" is not issued due to WAW hazard.")
                        inst.waw = "Y"
                        block = 1

                if block == 0:
                    self.tobewritten.append((inst.args[0], inst.pc))
                    if self.verbose >= 1:
                        print(f"Instruction \"{inst.inst}\" completes issue stage!")
                    inst.issue = self.clock_cycle
                    # set one of the FP mult units to busy
                    for k in range(len(self.FP_mult_status)):
                        if self.FP_mult_status[k] == 0:
                            self.FP_mult_status[k] = 1
                            break

            # if the instruction is a FP div instruction
            elif inst.is_FPdiv_inst():

                # check for structural hazards and WAW hazards
                if 0 not in self.FP_div_status:
                    if self.verbose >= 1:
                        print(f"Instruction \"{inst.inst}\" is not issued due to structural hazard.")
                    inst.struct = "Y"
                    block = 1
                for m in range(len(self.tobewritten)):
                    if inst.args[0] == self.tobewritten[m][0] and inst.pc > self.tobewritten[m][1]:
                        if self.verbose >= 1:
                            print(f"Instruction \"{inst.inst}\" is not issued due to WAW hazard.")
                        inst.waw = "Y"
                        block = 1

                if block == 0:
                    self.tobewritten.append((inst.args[0], inst.pc))
                    if self.verbose >= 1:
                        print(f"Instruction \"{inst.inst}\" completes issue stage!")
                    inst.issue = self.clock_cycle
                    # set one of the FP div units to busy
                    for k in range(len(self.FP_div_status)):
                        if self.FP_div_status[k] == 0:
                            self.FP_div_status[k] = 1
                            break

            # if the instruction is a branching instruction
            elif inst.is_branch_inst():
                if self.verbose >= 1:
                    print(f"Instruction \"{inst.inst}\" completes issue stage!")
                inst.issue = self.clock_cycle

                # stall the pipeline
                self.stall = 1

            # if it is any other instruction (J or HLT)
            else:
                if self.verbose >= 1:
                    print(f"Instruction \"{inst.inst}\" completes issue stage!")
                inst.issue = self.clock_cycle

    # method to read instructions
    def read_inst(self, inst):

        # if instruction is not a branch instruction or a store instruction
        if not inst.is_branch_inst() and not inst.is_store_inst():

            # check for RAW hazard
            block = 0
            for i in range(1, len(inst.args)):
                if inst.args[i] != -1:
                    for k in range(len(self.tobewritten)):
                        if inst.args[i] == self.tobewritten[k][0] and inst.pc > self.tobewritten[k][1]:
                            block = 1
            if block == 0:
                inst.read = self.clock_cycle
                if self.verbose >= 1:
                    print(f"Instruction \"{inst.inst}\" completes read stage!")
            else:
                if self.verbose >= 1:
                    print(f"Instruction \"{inst.inst}\" is not read due to RAW hazard.")
                inst.raw = "Y"

        # if the instruction is a store instruction
        elif inst.is_store_inst():
            block = 0
            for k in range(len(self.tobewritten)):
                if inst.args[0] == self.tobewritten[k][0] and inst.pc > self.tobewritten[k][1]:
                    block = 1
            if block == 0:
                inst.read = self.clock_cycle
                if self.verbose >= 1:
                    print(f"Instruction \"{inst.inst}\" completes read stage!")
            else:
                if self.verbose >= 1:
                    print(f"Instruction \"{inst.inst}\" is not read due to RAW hazard.")
                inst.raw = "Y"


        # if the instruction is a branch instruction
        else:

            # check for RAW hazard
            block = 0
            for i in range(0, 2):
                for m in range(len(self.tobewritten)):
                    if inst.args[i] == self.tobewritten[m][0] and inst.pc > self.tobewritten[m][1]:
                        block = 1

            if block == 0:
                inst.read = self.clock_cycle
                if self.verbose >= 1:
                    print(f"Instruction \"{inst.inst}\" completes read stage!")

                # check if the branch condition is satisfied, and change PC if necessary
                if (inst.keyword == "bne" and self.R[inst.args[0]] != self.R[inst.args[1]]) or (
                        inst.keyword == "beq" and self.R[inst.args[0]] == self.R[inst.args[1]]):
                    # self.pc = branch[inst.args[2]]
                    self.branch = branch[inst.args[2]]

                    # flush the pipeline if branch is taken
                    print("Branch condition satisfied, branch is taken and pipeline is flushed!")
                    for k in range(len(self.active)):
                        if self.active[k] != inst:
                            self.active[k].status2 = 1

                else:
                    self.stall = 0
                    inst.status2 = 1
            else:
                if self.verbose >= 1:
                    print(f"Instruction \"{inst.inst}\" is not read due to RAW hazard.")
                inst.raw = "Y"

    # method to execute instructions
    def exec_inst(self, inst):

        # if the instruction is an ALU instruction --> 1 clock cycle:
        if inst.is_ALU_inst():
            if self.verbose >= 1:
                print(f"Instruction \"{inst.inst}\" completes execute stage!")
            inst.exec = self.clock_cycle

        # if the instruction is an L.W or S.W instruction --> 1 clock cycle (load a single word):
        if inst.is_dataword_inst():
            memory = int(inst.args[1].split("(")[0]) + self.R[inst.args[1].split("(")[1].strip(')')]
            if self.D_cache_access(inst, memory):
                if self.verbose >= 1:
                    print(f"Instruction \"{inst.inst}\" completes execute stage!")
                inst.exec = self.clock_cycle

        # if the instruction is a S.D or L.D instruction --> 2 clock cycles (load both words):
        elif inst.is_datadouble_inst():
            memory = int(inst.args[1].split("(")[0]) + self.R[inst.args[1].split("(")[1].strip(')')]

            if inst.status2 == 1:
                if self.D_cache_access(inst, memory + 4):
                    if self.verbose >= 1:
                        print(f"Instruction \"{inst.inst}\" completes execute stage!")
                    inst.exec = self.clock_cycle

            if inst.status2 != 1 and self.D_cache_access(inst, memory):
                inst.status2 = 1

        # if the instruction is a FP Add instruction --> x clock cycles:
        elif inst.is_FPadd_inst():
            if inst.status == 0:
                inst.status = self.FP_add_cycle - 1
            else:
                inst.status -= 1
                if inst.status == 0:
                    if self.verbose >= 1:
                        print(f"Instruction \"{inst.inst}\" completes execute stage!")
                    inst.exec = self.clock_cycle

        # if the instruction is a FP Mult instruction --> y clock cycles:
        elif inst.is_FPmult_inst():
            if inst.status == 0:
                inst.status = self.FP_mult_cycle - 1
            else:
                inst.status -= 1
                if inst.status == 0:
                    if self.verbose >= 1:
                        print(f"Instruction \"{inst.inst}\" completes execute stage!")
                    inst.exec = self.clock_cycle

        # if the instruction is a FP Div instruction --> z clock cycles:
        elif inst.is_FPdiv_inst():
            if inst.status == 0:
                inst.status = self.FP_div_cycle - 1
            else:
                inst.status -= 1
                if inst.status == 0:
                    if self.verbose >= 1:
                        print(f"Instruction \"{inst.inst}\" completes execute stage!")
                    inst.exec = self.clock_cycle

    # method to write instructions
    def write_inst(self, inst):
        if self.verbose >= 1:
            print(f"Instruction \"{inst.inst}\" completes write stage!")
        inst.write = self.clock_cycle

        # check if the instructions change the registers' values, and apply necessary changes
        if inst.keyword == "li":
            if self.verbose >= 1:
                print(f"Register {inst.args[0]} = {int(inst.args[1])}")
            self.R[inst.args[0]] = int(inst.args[1])
        if inst.keyword == "daddi":
            if self.verbose >= 1:
                print(f"Register {inst.args[0]} = Register {inst.args[1]} + {int(inst.args[2])} = {self.R[inst.args[1]] + int(inst.args[2])}")
            self.R[inst.args[0]] = self.R[inst.args[1]] + int(inst.args[2])
        if inst.keyword == "dsub":
            if self.verbose >= 1:
                print(f"Register {inst.args[0]} = Register {inst.args[1]} - Register {inst.args[2]} = {self.R[inst.args[1]] - self.R[inst.args[2]]}")
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

        # if it is not a branching instruction, remove the target register from the to-be-written list
        if not inst.is_branch_inst():
            self.tobewritten.remove((inst.args[0], inst.pc))

    # method to access the instruction cache
    def I_cache_access(self, inst):

        if inst.pc // self.I_block_size in self.I_cache:
            if self.verbose >= 1:
                print(f"Instruction \"{inst.inst}\" found in the I-cache!")
            return True
        else:
            # check if the transfer bus is free
            if inst.status == 0:
                if self.bus == 0:
            # if self.bus == 0:
            #     if inst.status == 0:
                    if self.verbose >= 1:
                        print(f"Instruction \"{inst.inst}\" is a miss in the I-cache!")
                    inst.status = self.I_block_size * 3
                    self.totalImiss += 1
                    # set the transfer bus to busy
                    self.bus = 1
            else:
                # if inst.status != 0:
                inst.status -= 1
                if inst.status == 1:
                    self.bus = 0
                if inst.status == 0:
                    # insert the block in the I-cache, and set the transfer bus to available
                    self.I_cache[(inst.pc // self.I_block_size) % self.I_cache_size] = inst.pc // self.I_block_size
                    # self.bus = 0
                    return True
            if self.verbose >= 1:
                print(f"Instruction \"{inst.inst}\" is being loaded onto the I-cache. Remaining cycles: {inst.status}")
            return False

    # method to access the data cache
    def D_cache_access(self, inst, data):

        set = (data // 16) % 2

        # check if the data is in the D-cache
        for j in range(0, len(self.D_cache[set])):
            if self.D_cache[set][j][0] == data // 16:
                self.D_cache[set][j][1] = self.clock_cycle

                if self.verbose >= 1:
                    print(f"Memory {data} found in the D-cache!")

                # check if the instruction is a store instruction to set dirty bit
                if inst.is_store_inst():
                    self.D_cache[set][j][2] = 1
                return True
        else:
            # check if the transfer bus is free
            # if self.bus == 0:
            #     if inst.status == 0:
            if inst.status == 0:
                if self.bus == 0:
                    if self.D_cache[set][0][1] <= self.D_cache[set][1][1]:
                        if self.D_cache[set][0][2] == 1:
                            inst.status = 8*3
                            print(f"Instruction \"{inst.inst}\" is a miss in the D-cache, and needs to be put in a dirty block!")
                        else:
                            inst.status = 4*3
                            print(f"Instruction \"{inst.inst}\" is a miss in the D-cache!")
                    else:
                        if self.D_cache[set][1][2] == 1:
                            inst.status = 8 * 3
                            print(f"Instruction \"{inst.inst}\" is a miss in the D-cache, and needs to be put in a dirty block!")
                        else:
                            inst.status = 4 * 3
                            print(f"Instruction \"{inst.inst}\" is a miss in the D-cache!")

                    self.totalDmiss += 1

                    # set the transfer bus to busy
                    self.bus = 1
            else:
                # if inst.status != 0:
                inst.status -= 1
                if inst.status == 1:
                    self.bus = 0
                if inst.status == 0:

                    # check the LRU status of the D-cache, and put the data in the LRU slot
                    if self.D_cache[set][0][1] <= self.D_cache[set][1][1]:
                        self.D_cache[set][0][0] = data // 16
                        self.D_cache[set][0][1] = self.clock_cycle
                        if inst.is_store_inst():
                            self.D_cache[set][0][2] = 1
                        else:
                            self.D_cache[set][0][2] = 0
                    else:
                        self.D_cache[set][1][0] = data // 16
                        self.D_cache[set][1][1] = self.clock_cycle
                        if inst.is_store_inst():
                            self.D_cache[set][1][2] = 1
                        else:
                            self.D_cache[set][1][2] = 0

                    # set the transfer bus to free
                    # self.bus = 0

                    if self.verbose >= 1:
                        print(f"Memory {data} loaded onto the D-cache!")
                    return True
                if self.verbose >= 1:
                    print(f"Memory {data} is being loaded onto the D-cache. Remaining cycles: {inst.status}")
            return False

    # method to simulate the pipeline
    def simulate(self, instructions_list):

        # while the simuation is still valid
        while (self.end != 1):

            # increase the clock_cycle each time
            self.clock_cycle += 1
            if self.verbose >= 1:
                print(f"At clock cycle {self.clock_cycle}:")

            # remove the stall on the pipeline
            if len(self.active) == 0:
                self.stall = 0
                self.pc = self.branch

            # if the PC has been updated, and the pipeline is not stalled, add new instructions
            if self.oldpc != self.pc and self.stall != 1 and self.pc < len(instructions_list):
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
                    if self.active[i].is_branch_inst() and self.active[i].status2 == 1:
                        break
                elif self.active[i].exec == 0:
                    self.exec_inst(self.active[i])
                elif self.active[i].write == 0:
                    self.write_inst(self.active[i])
                i += 1

            # loop to check for completed instructions and free up the necessary resources
            i = 0
            while i < len(self.active):

                # condition to remove non-branch instructions from pipeline
                if not self.active[i].is_branch_inst() and not self.active[i].is_jump_inst() and not self.active[i].is_hlt_inst():
                    if self.active[i].write != 0:
                        self.free(self.active[i])
                        self.complete.append(self.active.pop(i))
                        continue

                # condition to remove branch instructions from pipeline
                elif self.active[i].is_branch_inst():
                    if self.active[i].read != 0:
                        self.free(self.active[i])
                        self.complete.append(self.active.pop(i))
                        continue

                # condition to remove instructions that need to be flushed after branch is taken
                elif self.active[i].status2 != 0 and self.active[i].status == 0:
                    self.complete.append(self.active.pop(i))
                    continue
                i += 1

            # print("Completed:")
            # for i in range(len(self.complete)):
            #     self.complete[i].print()

            if self.verbose >= 2:
                print("Current Pipeline (Active Instructions):")
                for i in range(len(self.active)):
                    self.active[i].print()

            # time.sleep(0.1)
            print("\n")

            # condition to check whether the simulation has ended
            if not self.pc < len(instructions_list):
                for i in range(len(self.active)):
                    if not self.active[i].is_hlt_inst():
                        break
                else:
                    self.end = 1

        # final flush the pipeline
        k = 0
        while len(self.active) != 0 and k < len(self.active):
            self.complete.append(self.active.pop(k))

        # count the total number of accesses to the data cache
        self.totalD = 0
        for k in range(len(self.complete)):
            if self.complete[k].keyword == "lw" or self.complete[k].keyword == "sw":
                self.totalD += 1
            elif self.complete[k].keyword == "l.d" or self.complete[k].keyword == "s.d":
                self.totalD += 2

        # return the list of completed instructions
        return self.complete, len(self.complete), len(
            self.complete) - self.totalImiss, self.totalD, self.totalD - self.totalDmiss

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

final, itotal, ihits, dtotal, dhits = s.simulate(instructions)

final.sort(key=lambda x: x.fetch)
over = []
for i in range(len(final)):
    over.append([final[i].inst, str(final[i].fetch), str(final[i].issue), str(final[i].read), str(final[i].exec),
                 str(final[i].write), final[i].raw, final[i].waw, final[i].struct])

with open(result_file, 'w') as f:
    f.write("Instruction\t\t\tFetch\tIssue\tRead\tExec\tWrite\tRAW\tWAW\tStruct\n")


    def write_result(result):
        if result[1] == "0":
            return
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
            f.write(result[i] + "\t")
        f.write("\n")

    for i in range(len(over)):
        write_result(over[i])
    f.write("\n\n")
    f.write(f"Total number of access requests for instruction cache: {itotal}\n")
    f.write(f"Number of instruction cache hits: {ihits}\n")
    f.write(f"Total number of access requests for data cache: {dtotal}\n")
    f.write(f"Number of data cache hits: {dhits}")

print("\nDone!")