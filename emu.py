class Register_Single:
    # 8-bit register

    byte = bytearray([0])

    def __init__(self, x=0):
        self.byte = bytearray([x])

    def __str__(self):
        return hex(self.byte[0])

    def __len__(self):
        return 8

    # Set the value of the register
    def push(self, new):
        self.byte[0] = new

    # Return the value of register as a bytearray
    def get(self):
        return self.byte

    # Return the value of register as an int
    def num(self):
        return self.byte[0]

    # [] used to access individual bits
    def __getitem__(self, index):
        assert(index >= 0 and index <= 7), "Bit index out of bounds."
        mask = 1 << int(index)
        return mask == self.byte[0] & mask

    # Copy the value from another register into self
    def __lshift__(self, other):
        self.push(other.num())


class Arithmetic_Logic_Unit:
    # ALU model
    def __init__(self):
        # inputs
        self.A = Register_Single(0)
        self.B = Register_Single(0)
        self.carry_in = False
        self.opcode = 0

        # outputs
        self.C = Register_Single(0)
        self.carry_out = False
        self.equal = True
        self.A_larger = False

    def update(self):
        # Only compare (COMP / opcode 7)
        self.A_larger = self.A.num() > self.B.num()
        self.equal = self.A.num() == self.B.num()
        self.C.push(0)

        if self.opcode == 6:  # XOR
            self.C.push(self.A.num() ^ self.B.num())

        elif self.opcode == 5:  # OR
            self.C.push(self.A.num() | self.B.num())

        elif self.opcode == 4:  # AND
            self.C.push(self.A.num() & self.B.num())

        elif self.opcode == 3:  # NOT
            neg = 0
            for i in range(0, len(self.A)):
                neg += (not self.A[i])*2**i
            self.C.push(neg)

        elif self.opcode == 2:  # SHL
            new = self.A.num() << 1
            self.carry_out = new > 255
            self.C.push(new % 256 + self.carry_in)

        elif self.opcode == 1:  # SHR
            new = self.A.num() >> 1
            self.carry_out = self.A[0]
            self.C.push(new + 128*self.carry_in)

        elif self.opcode == 0:  # ADD
            new = self.A.num() + self.B.num() + self.carry_in
            self.carry_out = new > 256
            self.C.push(new % 256)

        elif self.opcode != 7:
            raise Exception(f"Invalid opcode:{self.opcode}")

    # Updates all inputs at once

    def new_inputs(self, a, b, c, op):
        self.A.push(a)
        self.B.push(b)
        self.carry_in = c
        self.opcode = op
        self.update()

    def setA(self, a):
        self.A.push(a)
        self.update()

    def setB(self, b):
        self.B.push(b)
        self.update()

    def set_carry(self, c):
        self.carry_in = c
        self.update()

    def set_op(self, op):
        self.opcode = op
        self.update()

    def read(self):
        return self.C

    def get_carry(self):
        return self.carry_out

    def get_A_larger(self):
        return self.A_larger

    def get_equal(self):
        return self.equal

    def get_zero(self):
        return self.C.num() == 0


def hex_dump(data, cols=8):
    # print hex values in a grid
    size = len(data)

    for address in range(0, size):
        if address % cols == 0:
            print(f'\n{address}\t{hex(address)}:\t', end='')
        print(f'{hex(data[address])[2:]}'.zfill(2), end=' ')
    print('\n')


# Special registers
MAR = Register_Single(0)
ACC = Register_Single(0)
BUS = Register_Single(0)
IAR = Register_Single(0)
IR = Register_Single(0)
FLAG = Register_Single(0)

# General-purpose registers
GEN_REG = [Register_Single(0) for i in range(0, 4)]

# Set up RAM and ALU
RAM = bytearray(256)
ALU = Arithmetic_Logic_Unit()


# Updates the flags register
def set_flags():
    new_flags = 0

    if ALU.get_zero():
        new_flags += 0b0001

    if ALU.get_equal():
        new_flags += 0b0010

    if ALU.get_A_larger():
        new_flags += 0b0100

    if ALU.get_carry():
        new_flags += 0b1000

    FLAG.push(new_flags)


def ALU_instruction(inst):
    # Slice up instruction to extract information
    op = (inst & 0b01110000) >> 4
    reg_from = (inst & 0b00001100) >> 2
    reg_to = inst & 0b00000011

    # Select the registers
    REG_A = GEN_REG[reg_from]  # take from
    REG_B = GEN_REG[reg_to]    # store to

    # STEP 4
    ALU.setB(REG_B.num())

    # STEP 5
    # Select operation and compute the result
    ALU.set_op(op)
    ALU.setA(REG_A.num())
    ACC.push(ALU.read().num())
    set_flags()
    ALU.set_op(0)  # Reset ALU operation

    # STEP 6
    if op != 7:
        REG_B << ACC


def LOAD_instruction(inst):
    # Select the registers
    REG_A = GEN_REG[(inst & 0b00001100) >> 2]  # address in RAM
    REG_B = GEN_REG[inst & 0b00000011]  # store to this register

    # STEP 4
    # Select the desired address in RAM from REG_A
    MAR << REG_A

    # STEP 5
    # Store the value from RAM to REG_B
    REG_B.push(RAM[MAR.num()])


def STORE_instruction(inst):
    # Select the registers
    REG_A = GEN_REG[(inst & 0b00001100) >> 2]  # address in RAM
    REG_B = GEN_REG[inst & 0b00000011]  # store to this register

    # STEP 4
    # Select the desired address in RAM from REG_A
    MAR << REG_A

    # STEP 5
    # Store the value from REG_B to RAM
    RAM[MAR.num()] = REG_B.num()


def DATA_instruction(inst):
    REG = GEN_REG[(inst & 0b00001100) >> 2]  # store to this register

    # STEP 4
    # Use the location of next instruction as address in RAM
    MAR << IAR
    # Increment IAR to skip the next line
    ALU.new_inputs(IAR.num(), 1, False, 0)
    ACC << ALU.read()

    # STEP 5
    # Store the value from RAM to the register
    REG.push(RAM[MAR.num()])

    # STEP 6
    # Store incremented instruction address to IAR
    IAR << ACC


def JMPR_instruction(inst):
    REG = GEN_REG[inst & 0b00001100]  # get address from this register

    # STEP 4
    IAR << REG


def JUMP_instruction():
    # STEP 4
    # Use the location of next instruction as address in RAM
    MAR << IAR

    # STEP 5
    # Load the new address from RAM
    IAR.push(RAM[MAR.num()])


def JCAEZ_instruction(inst):
    # If any of the tested flags in on, jump to the given RAM address

    # Select which flags to test for
    mask = inst & 0b00001111

    # STEP 4
    # Use the location of next instruction as address in RAM
    MAR << IAR
    # Increment IAR to skip the next line
    ALU.new_inputs(IAR.num(), 1, False, 0)
    ACC << ALU.read()

    # STEP 5
    # Store incremented instruction address to IAR
    IAR << ACC

    # STEP 6
    # Test if any selected flags are on
    if (FLAG.num() & mask):
        # Jump to
        IAR.push(RAM[MAR.num()])


def CLF_instruction():
    # STEP 4
    FLAG.push(0)


def cycle():
    # STEP 1
    # Load instruction address into memory address and increment by 1
    ALU.new_inputs(IAR.num(), 1, False, 0)
    MAR << IAR
    ACC << ALU.read()

    # STEP 2
    # Load instruction from RAM
    IR.push(RAM[MAR.num()])

    # STEP 3
    # Load incremented instruction number back into IAR
    IAR << ACC

    # Decide which steps 4-6 to carry out next:

    # Test if this is an ALU operation
    if IR[7]:
        ALU_instruction(IR.num())

    else:
        # Decode the instruction
        instruction_code = (IR.num() & 0b01110000) >> 4

        # LOAD RA,RB
        if instruction_code == 0:
            LOAD_instruction(IR.num())

        # STORE RA,RB
        elif instruction_code == 1:
            STORE_instruction(IR.num())

        # DATA RA, XXXXXXXX
        elif instruction_code == 2:
            DATA_instruction(IR.num())

        # JMPR RA
        elif instruction_code == 3:
            JMPR_instruction(IR.num())

        # JUMP XXXXXXXX
        elif instruction_code == 4:
            JUMP_instruction()

        # J[CAEZ] XXXXXXXX
        elif instruction_code == 5:
            JCAEZ_instruction(IR.num())

        # CLF
        elif instruction_code == 6:
            CLF_instruction()


def autoint(num):
    if num[0] == '0' and len(num) > 1:
        if num[1] == 'x':
            return int(num, 16)
        elif num[1] == 'b':
            return int(num, 2)
        else:
            return int(num)
    return int(num)


def check_reg(reg):
    if reg[0] != 'R':
        raise Exception(f"Invalid register name: {reg}")
    elif int(reg[1:]) > 3 or int(reg[1:]) < 0:
        raise Exception(f"Invalid register number: {reg}")
    else:
        return int(reg[1:])


def assemble(filename):
    # TODO: add better error handling
    code = []
    with open(filename, 'r') as source:
        line = source.readline()

        # Remove comments and spaces
        line = line.split(';', 1)[0].strip().replace(',', ' ')

        while line != 'END':

            # Skip parsing if the line is empty
            if not line:
                line = source.readline()
                line = line.split(';', 1)[0].strip().replace(',', ' ')
                continue

            op = line.split()[0]
            args = line.split()[1:]

            if op == 'LOAD':
                RA = check_reg(args[0])
                RB = check_reg(args[1])
                code.append(0x00 + (RA << 2) + RB)

            elif op == 'STORE':
                RA = check_reg(args[0])
                RB = check_reg(args[1])
                code.append(0x10 + (RA << 2) + RB)

            elif op == 'DATA':
                RA = check_reg(args[0])
                data = autoint(args[1])
                code.append(0x20 + (RA << 2))
                code.append(data)

            elif op == 'JMPR':
                RA = check_reg(args[0])
                code.append(0x30 + (RA << 2))

            elif op == 'JUMP':
                data = autoint(args[0])
                code.append(0x40)
                code.append(data)

            elif op[0] == 'J':
                data = autoint(args[0])
                flags = op[1:]
                flags_num = 0
                while flags:
                    if flags[0] in 'ZAEC':
                        flags_num += 1 << 'ZAEC'.find(flags[0])
                        flags.replace(flags[0], '')
                    flags = flags[1:]
                code.append(0x50 + flags_num)
                code.append(data)

            elif line == 'CLF':
                code.append(0x60)

            elif op == 'ADD':
                RA = check_reg(args[0])
                RB = check_reg(args[1])
                code.append(0x80 + (RA << 2) + RB)

            elif op == 'SHR':
                RB = check_reg(args[0])
                code.append(0x90 + (RB << 2) + RB)

            elif op == 'SHL':
                RB = check_reg(args[0])
                code.append(0xA0 + (RB << 2) + RB)

            elif op == 'NOT':
                RB = check_reg(args[0])
                code.append(0xB0 + (RB << 2) + RB)

            elif op == 'AND':
                RA = check_reg(args[0])
                RB = check_reg(args[1])
                code.append(0xC0 + (RA << 2) + RB)

            elif op == 'OR':
                RA = check_reg(args[0])
                RB = check_reg(args[1])
                code.append(0xD0 + (RA << 2) + RB)

            elif op == 'XOR':
                RA = check_reg(args[0])
                RB = check_reg(args[1])
                code.append(0xE0 + (RA << 2) + RB)

            elif op == 'COMP':
                RA = check_reg(args[0])
                RB = check_reg(args[1])
                code.append(0xF0 + (RA << 2) + RB)

            # Macros:
            elif op == 'COPY':
                RA = check_reg(args[0])
                RB = check_reg(args[1])
                code.append(0xE0 + (RB << 2) + RB)
                code.append(0x80 + (RA << 2) + RB)

            else:
                raise Exception(f"Invalid instruction/macro: {line}")

            line = source.readline()
            line = line.split(';', 1)[0].strip().replace(',', ' ')

    return code


def execute_until(end_line, max_cycles=1000, verbose=False):
    counter = 0
    while IAR.num() < end_line and counter < max_cycles:
        counter += 1
        if verbose:
            print(f"{counter}/{IAR.num()}: ", end='')

        cycle()

        if verbose:
            for i in range(0, 4):
                print(GEN_REG[i].num(), end=' ')
            print("\n")


asm = assemble('fibo.asm')
print([hex(x) for x in asm])
RAM[0:len(asm)] = asm
hex_dump(RAM, 16)

IAR.push(0)
execute_until(32, 200, False)
hex_dump(RAM, 16)
print([x for x in RAM[64:] if x != 0])
