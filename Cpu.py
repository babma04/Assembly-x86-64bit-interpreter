from storage import Storage
from register import Register64
import sys


class CPU:
    """
    A simple CPU simulator with registers, program counter, and memory, no stack system implemented.
    Does not yet support memory addressing besides direct addressing.
    Does not support memory addressing modes for the first operand (destiny).
    64-bit architecture with basic arithmetic and logic instructions.
    Created mainly for educational purposes.
    """


    def __init__(self, file):
        """
        Initialize the CPU with registers, program counter, and memory.
        :param file_name: The name of the file with extension.
        :requires: file_name includes the .json extension && the file exists
        """
        # Initialize registers
        self.rax = Register64()
        self.rbx = Register64()
        self.rcx = Register64()
        self.rdx = Register64()
        self.rsi = Register64()
        self.rdi = Register64()
        self.rsp = Register64()
        self.rbp = Register64()
        self.r8 = Register64()
        self.r9 = Register64()
        self.r10 = Register64()
        self.r11 = Register64()
        self.r12 = Register64()
        self.r13 = Register64()
        self.r14 = Register64()
        self.r15 = Register64()

        self.pc = 0  # Program counter
        
        self.flags = {
            'Z': 0,  # Zero flag
            'C': 0,  # Carry flag
            'S': 0,  # Sign flag
            'O': 0   # Overflow flag
        }
        
        self.memory = 0  # Creates an object memory to hold the program
        
        self.rodata_segment = {}  # Read-only data segment
        self.data_segment = {}  # Data segment for variables
        self.bss_segment = {}   # BSS segment for uninitialized data
        self.text_segment = {}  # Text segment for code/instructions
        self.labels = {}        # Labels for jump instructions
                
        #sets of supported instructions and their operand counts
        self.valid_instructions = {
            'mov': 2,
            'add': 2,
            'adc': 2,
            'sub': 2,
            'sbb': 2,
            'inc': 1,
            'dec': 1,
            'and': 2,
            'or': 2,
            'xor': 2,
            'not': 1,
            'neg': 1,
            'xchg': 2,
            'halt': 0,
            'cmp': 2,
            'jmp': 1,
            'jb': 1,
            'jl': 1,
            'ja': 1,
            'jg': 1,
            'je': 1,
            'jne': 1,
            'jz': 1,
            'js': 1,
            'jc': 1,
            'jo': 1
        }

        self.halted = False  # CPU halted state/finished execution
        self.instruction = None  # Current instruction being executed
        self.file_name = file
        

        # if (self.instruction != None  and self.instruction not in self.labels and self.validate_fetch(self)):
        #     if self.get_operand_number(self.pc) == 1:
        #         self.operand1 = self.get_operand1(self.pc)
        #     elif self.get_operand_number(self.pc) == 2:
        #         self.operand1 = self.get_operand1(self.pc)
        #         self.operand2 = self.get_operand2(self.pc)
    

    def section_separe(self):
        """
        Separates the different sections of the code int different dictionaries of the file for better management, and access to variables and instructions.
        """
        self.file_name = Storage.convert_to_json(self.file_name)
        self.load_program(self.file_name)
        pc = 0
        while pc < len(self.memory):
            print(f"ENTROU NO LOOP {pc}\n")
            if self.memory[pc][0] == "section" and self.memory[pc][1] == ".rodata":
                pc += 1
                while pc < len(self.memory) and self.memory[pc][1] not in (".data", ".bss", ".text"):
                    if("equ" not in self.memory[pc]):
                        tokens = self.memory[pc]
                        variable = tokens[0].rstrip(":")
                        size = tokens[1]
                        value = tokens[2]
                        if (size not in ["db","dw","dd","dq"]):
                            raise ValueError(f"Invalid size specifier: {size} for variable {variable} in rodata segment.")
                        
                    else:
                        tokens = self.memory[pc]
                        variable = tokens[0].rstrip(":")
                        value = tokens[2]
                        if value.startswith("$-"):   #if the value calculated string length or any other type of calculation
                            value = value.strip("$-").strip(" ")  #assuming the format is always $-variable,     the $- part
                            value = len(self.rodata_segment[value]) #get the length of the variable in rodata segment
                            size = None
                        else:
                            value = value.strip(" ")
                            size = None
                    self.rodata_segment[variable] = {'size': size, 'value': value}
                    pc += 1


            elif self.memory[pc][0] == "section" and self.memory[pc][1] == ".data":
                pc += 1
                while pc < len(self.memory) and self.memory[pc][1] not in (".rodata", ".bss", ".text"):
                    if("equ" not in self.memory[pc]):    
                        tokens = self.memory[pc]
                        variable = tokens[0].rstrip(":")
                        size = tokens[1]
                        
                        value = tokens[2]
                        if (size not in ["db","dw","dd","dq"]):
                            raise ValueError(f"Invalid size specifier: {size} for variable {variable} in rodata segment.")
                        
                    else:
                        tokens = self.memory[pc]
                        variable = tokens[0].rstrip(":")
                        value = tokens[2]
                        if value.startswith("$-"):   #if the value calculated string length or any other type of calculation
                            value = value.strip("$-").strip(" ")  #assuming the format is always $-variable, remove the $- part
                            value = len(self.data_segment[value]) #get the length of the variable in rodata segment
                            size = None
                        else:
                            value = value.strip(" ")
                            size = None
                    self.data_segment[variable] = {'size': size, 'value': value}
                    pc += 1

            elif self.memory[pc][0] == "section" and self.memory[pc][1] == ".bss":
                pc += 1
                while pc < len(self.memory) and self.memory[pc][1] not in (".data", ".rodata", ".text"):
                    tokens = self.memory[pc]
                    variable = tokens[0].rstrip(":")
                    size = tokens[1]
                    quantity = tokens[2]
                    try:
                        quantity = int(quantity.strip(" "))
                    except ValueError:
                        raise ValueError(f"Invalid quantity specifier: {quantity} for variable {variable} in bss segment.")
                    size = size.strip(" ")
                    if (size not in ["resb","resw","resd","resq"]):
                        raise ValueError(f"Invalid size specifier: {size} for variable {variable} in bss segment.")
                    self.bss_segment[variable] = {i: {'size': size, 'value': 0}  for i in range(quantity)}  #initializes the variable with quantity of 0s
                    pc += 1
                    
            elif self.memory[pc][0] == "section" and self.memory[pc][1] == ".text":
                if (self.memory[pc + 1][0] != "global" and self.memory[pc + 1][1] != "_start"):
                    raise ValueError("Missing 'global _start' declaration in text segment.") #verify that the program has a global _start declaration (necessary for execution start)
                pc += 1                            
                while pc < len(self.memory):
                    if (self.memory[pc][0].startswith("_") and len(self.memory[pc]) == 1):  #detect labels (which start with _ )
                        label = self.memory[pc][0].strip(":").strip(" ")
                        if label == "_start":
                            print("\nENCONTROU UM START")
                            self.pc = pc
                            print(f"self.pc setted for {pc + 1}\n")
                        if label in self.labels:
                            raise ValueError(f"Duplicate label found: {label}")
                        else:
                            self.labels[label] = pc #store the label with its corresponding memory address
                    pc += 1
        
        print(f"\nMEMORIA COMPLETA. pc:{pc + 1}\n")
            
            

                    
    def execute(self):
        """
        Executes the fetch-decode-execute cycle until the CPU is halted.
        """
        print("CPU STARTING\n")
        self.section_separe()
        #self.print_list(self.memory)

        self.pc += 1
        while not self.halted:          
            
            if self.memory[self.pc][0] == "syscall":
                self.is_syscall()
            
            elif self.memory[self.pc][0].replace(":", "") in self.labels:
                self.pc += 1
                continue
                
            else:
                if not self.validate_fetch():
                    print(f"Halting execution due to invalid instruction at line {self.pc + 1}.")
                    self.halted = True
                    continue
                else:
                    if self.instruction not in self.labels:
                        op_number = self.get_operand_number(self.pc)
                        if op_number == 1:
                            self.operand1 = self.get_operand1(self.pc)
                        elif op_number == 2:
                            self.operand1 = self.get_operand1(self.pc)
                            self.operand2 = self.get_operand2(self.pc)
                    self.execute_instruction()
                    print(f"INSTRUÇÃO {self.pc +1} EXECUTADA {' '.join(str(elemento) for elemento in self.memory[self.pc])}\n")
                    self.pc += 1
            
                    
    
    def execute_instruction(self):
        """
        Directs execution to the appropriate instruction method based on the current instruction.
        """
        if self.instruction == "halt":
            self.halted = True
            print("HALT instruction encountered. Stopping execution.")
        elif self.instruction == "mov":
            self.mov(self.operand1, self.operand2)
        elif self.instruction == "add":
            self.add(self.operand1, self.operand2)
        elif self.instruction == "adc":
            self.adc(self.operand1, self.operand2)
        elif self.instruction == "sub":
            self.sub(self.operand1, self.operand2)
        elif self.instruction == "sbb":
            self.sbb(self.operand1, self.operand2)
        elif self.instruction == "inc":
            self.inc(self.operand1)
        elif self.instruction == "dec":
            self.dec(self.operand1)
        elif self.instruction == "and":
            self.and_op(self.operand1, self.operand2)
        elif self.instruction == "or":
            self.or_op(self.operand1, self.operand2)
        elif self.instruction == "xor":
            self.xor_op(self.operand1, self.operand2)
        elif self.instruction == "not":
            self.not_op(self.operand1)
        elif self.instruction == "neg":
            self.neg(self.operand1)
        elif self.instruction == "xchg":
            self.xchg(self.operand1, self.operand2)
        elif self.instruction == "cmp":
            self.cmp(self.operand1, self.operand2)
        elif self.instruction == "jmp":
            self.jmp()
        elif self.instruction == "jb":
            raise ValueError(f"No cmp instruction in range of {self.memory[self.pc][0]}")
        elif self.instruction == "jl":
            raise ValueError(f"No cmp instruction in range of {self.memory[self.pc][0]}")
        elif self.instruction == "ja":
            raise ValueError(f"No cmp instruction in range of {self.memory[self.pc][0]}")
        elif self.instruction == "jg":
            raise ValueError(f"No cmp instruction in range of {self.memory[self.pc][0]}")
        elif self.instruction == "je":
            raise ValueError(f"No cmp instruction in range of {self.memory[self.pc][0]}")
        elif self.instruction == "jne":
            raise ValueError(f"No cmp instruction in range of {self.memory[self.pc][0]}")
        elif self.instruction == "jz":
            self.jz()
        elif self.instruction == "js":
            self.js()
        elif self.instruction == "jc":
            self.jc()
        elif self.instruction == "jo":
            self.jo()
        
        

    def mov(self, dest, src):
        """
        Move the value from src to dest.
        :param dest: The destination register or memory location.
        :param src: The source register, memory location, or immediate value.
        """
        dest_get, dest_set = self.select_operand(dest)
        try:
            src_get = int(src)
            value = src_get   # read the source value
            dest_set(value) 

        except ValueError:
            src_get, src_set = self.select_operand(src)

            value = src_get()   # read the source value
            dest_set(value)     # write to the destination
        

    def add(self, dest, src):
        """
        Add the value from src to dest and store the result in dest.
        :param dest: The destination register or memory location.
        :param src: The source register, memory location, or immediate value.
        """

        if not CPU.is_register(dest):
            print(f"Halting execution due to invalid instruction at line {self.pc}. Unsupported operand as a label/memory address as destiny operand")
            self.halted = True

        dest_get, dest_set = self.select_operand(dest)
        dest_size = self.get_size(dest)
        try:
            src_get = int(src)
            result = dest_get() + src_get

            #verify if the result exceeds the size of the destination operand and set the carry flag accordingly
            if int(dest_get()) > 0 and int(src_get) > 0 and result > 2**dest_size-1:
                self.flags['C'] = 1
                result = result % (2**dest_size) #wrap around the result to fit in the destination size
            else:
                self.flags['C'] = 0

        except ValueError:
            #veries if the two operands have the same size
            if self.get_size(dest) != self.get_size(src):
                raise ValueError(f"Operand size mismatch: dest size {self.get_size(dest)} bits, src size {self.get_size(src)} bits.")

            src_get, src_set = self.select_operand(src)
            result = int(dest_get()) + int(src_get())

            #verify if the result exceeds the size of the destination operand and set the carry flag accordingly
            if int(dest_get()) > 0 and int(src_get()) > 0 and result > 2**dest_size-1:
                self.flags['C'] = 1
                result = result % (2**dest_size) #wrap around the result to fit in the destination size
            else:
                self.flags['C'] = 0
        
        if result == 0:
            self.flags['Z'] = 1
        else:
            self.flags['Z'] = 0
        if result * dest_get() < 0:
            self.flags['S'] = 1
        else:
            self.flags['S'] = 0
        
        max_val = 2**(dest_size-1) - 1
        min_val = -2**(dest_size-1)

        # Overflow detection (signed)
        if result > max_val or result < min_val:
            self.flags['O'] = 1
        else:
            self.flags['O'] = 0
        
        # Wrap result to simulate 8-bit overflow
        mask = 2**dest_size - 1
        result =  result & mask

        dest_set(result)
    

    def adc(self, dest, src):
        """
        Add the value from src to dest with carry and store the result in dest.
        :param dest: The destination register or memory location.
        :param src: The source register, memory location, or immediate value.
        """

        if not CPU.is_register(dest):
            print(f"Halting execution due to invalid instruction at line {self.pc}. Unsupported operand as a label/memory address as destiny operand")
            self.halted = True

        dest_get, dest_set = self.select_operand(dest)
        carry = self.flags['C']
        dest_size = self.get_size(dest)
        try:
            src_get = int(src)
            result = dest_get() + src_get + carry

            #verify if the result exceeds the size of the destination operand and set the carry flag accordingly
            if int(dest_get()) > 0 and int(src_get) > 0 and result > 2**dest_size-1:
                self.flags['C'] = 1
                result = result % (2**dest_size) #wrap around the result to fit in the destination size
            else:
                self.flags['C'] = 0

        except ValueError:
            #veries if the two operands have the same size
            if self.get_size(dest) != self.get_size(src):
                raise ValueError(f"Operand size mismatch: dest size {self.get_size(dest)} bits, src size {self.get_size(src)} bits.")

            src_get, src_set = self.select_operand(src)
            result = int(dest_get()) + int(src_get()) + int(carry)

            #verify if the result exceeds the size of the destination operand and set the carry flag accordingly
            if int(dest_get()) > 0 and int(src_get()) > 0 and result > 2**dest_size-1:
                self.flags['C'] = 1
                result = result % (2**dest_size) #wrap around the result to fit in the destination size
            else:
                self.flags['C'] = 0
                
        if result == 0:
            self.flags['Z'] = 1
        else:
            self.flags['Z'] = 0
        if result * dest_get() < 0:
            self.flags['S'] = 1
        else:
            self.flags['S'] = 0
        
        max_val = 2**(dest_size-1) - 1
        min_val = -2**(dest_size-1)

        # Overflow detection (signed)
        if result > max_val or result < min_val:
            self.flags['O'] = 1
        else:
            self.flags['O'] = 0
        
        # Wrap result to simulate 8-bit overflow
        mask = 2**dest_size - 1
        result =  result & mask
        
        dest_set(result)
    

    def sub(self, dest, src):
        """
        Subtract the value from src from dest and store the result in dest.
        :param dest: The destination register or memory location.
        :param src: The source register, memory location, or immediate value.
        """

        if not CPU.is_register(dest):
            print(f"Halting execution due to invalid instruction at line {self.pc}. Unsupported operand as a label/memory address as destiny operand")
            self.halted = True

        dest_get, dest_set = self.select_operand(dest)
        dest_size = self.get_size(dest)
        try:
            src_get = int(src)
            result = dest_get() - src_get

            #verify if the result exceeds the size of the destination operand and set the carry flag accordingly
            if int(dest_get()) > 0 and int(src_get) > 0 and result > 2**dest_size-1:
                self.flags['C'] = 1
                result = result % (2**dest_size) #wrap around the result to fit in the destination size
            else:
                self.flags['C'] = 0

        except ValueError:
            #veries if the two operands have the same size
            if self.get_size(dest) != self.get_size(src):
                raise ValueError(f"Operand size mismatch: dest size {self.get_size(dest)} bits, src size {self.get_size(src)} bits.")
            
            src_get, src_set = self.select_operand(src)
            result = int(dest_get()) - int(src_get())

            #verify if the result exceeds the size of the destination operand and set the carry flag accordingly
            if int(dest_get()) > 0 and int(src_get()) > 0 and result > 2**dest_size-1:
                self.flags['C'] = 1
                result = result % (2**dest_size) #wrap around the result to fit in the destination size
            else:
                self.flags['C'] = 0


        
        if result == 0:
            self.flags['Z'] = 1
        else:
            self.flags['Z'] = 0
        if result * dest_get() < 0:
            self.flags['S'] = 1
        else:
            self.flags['S'] = 0
        
        max_val = 2**(dest_size-1) - 1
        min_val = -2**(dest_size-1)

        # Overflow detection (signed)
        if result > max_val or result < min_val:
            self.flags['O'] = 1
        else:
            self.flags['O'] = 0
        
        # Wrap result to simulate overflow
        mask = 2**dest_size - 1
        result =  result & mask

        dest_set(result)
    
    def sub_cmp(self, dest, src):
        """
        Subtract the value from src from dest without store the result in dest.
        Used in comparisons and to verify jump instructions.
        :param dest: The destination register or memory location.
        :param src: The source register, memory location, or immediate value.
        """

        if not CPU.is_register(dest):
            print(f"Halting execution due to invalid instruction at line {self.pc}. Unsupported operand as a label/memory address as destiny operand")
            self.halted = True

        dest_get, dest_set = self.select_operand(dest)
        dest_size = self.get_size(dest)
        try:
            src_get = int(src)
            result = dest_get() - src_get
            
            #verify if the result exceeds the size of the destination operand and set the carry flag accordingly
            if int(dest_get()) > 0 and int(src_get) > 0 and result > 2**dest_size-1:
                self.flags['C'] = 1
                result = result % (2**dest_size) #wrap around the result to fit in the destination size
            else:
                self.flags['C'] = 0
                
        except ValueError:
            #veries if the two operands have the same size
            if self.get_size(dest) != self.get_size(src):
                raise ValueError(f"Operand size mismatch: dest size {self.get_size(dest)} bits, src size {self.get_size(src)} bits.")

            src_get, src_set = self.select_operand(src)
            result = int(dest_get()) - int(src_get())
            
            #verify if the result exceeds the size of the destination operand and set the carry flag accordingly
            if int(dest_get()) > 0 and int(src_get()) > 0 and result > 2**dest_size-1:
                self.flags['C'] = 1
                result = result % (2**dest_size) #wrap around the result to fit in the destination size
            else:
                self.flags['C'] = 0

        max_val = 2**(dest_size-1) - 1
        min_val = -2**(dest_size-1)

        # Overflow detection (signed)
        if result > max_val or result < min_val:
            self.flags['O'] = 1
        else:
            self.flags['O'] = 0
        
        if result == 0:
            self.flags['Z'] = 1
        else:
            self.flags['Z'] = 0
        if result * dest_get() < 0:
            self.flags['S'] = 1
        else:
            self.flags['S'] = 0
        
        max_val = 2**(dest_size-1) - 1
        min_val = -2**(dest_size-1)

        # Overflow detection (signed)
        if result > max_val or result < min_val:
            self.flags['O'] = 1
        else:
            self.flags['O'] = 0
        
        # Wrap result to simulate 8-bit overflow
        mask = 2**dest_size - 1
        result =  result & mask

    

    def sbb(self, dest, src):
        """
        Subtract the value from src from dest with borrow and store the result in dest.
        :param dest: The destination register or memory location.
        :param src: The source register, memory location, or immediate value.
        """

        if not CPU.is_register(dest):
            print(f"Halting execution due to invalid instruction at line {self.pc}. Unsupported operand as a label/memory address as destiny operand")
            self.halted = True

        dest_get, dest_set = self.select_operand(dest)
        borrow = self.flags['C']
        dest_size = self.get_size(dest)
        try:
            src_get = int(src)
            result = dest_get() - src_get - borrow

            #verify if the result exceeds the size of the destination operand and set the carry flag accordingly
            if int(dest_get()) > 0 and int(src_get()) > 0 and result > 2**dest_size-1:
                self.flags['C'] = 1
                result = result % (2**dest_size) #wrap around the result to fit in the destination size
            else:
                self.flags['C'] = 0

        except ValueError:
            #veries if the two operands have the same size
            if self.get_size(dest) != self.get_size(src):
                raise ValueError(f"Operand size mismatch: dest size {self.get_size(dest)} bits, src size {self.get_size(src)} bits.")

            src_get, src_set = self.select_operand(src)
            result = int(dest_get()) - int(src_get()) - int(borrow)

            #verify if the result exceeds the size of the destination operand and set the carry flag accordingly
            if int(dest_get()) > 0 and int(src_get()) > 0 and result > 2**dest_size-1:
                self.flags['C'] = 1
                result = result % (2**dest_size) #wrap around the result to fit in the destination size
            else:
                self.flags['C'] = 0
        
        if result == 0:
            self.flags['Z'] = 1
        else:
            self.flags['Z'] = 0
        if result * dest_get() < 0:
            self.flags['S'] = 1
        else:
            self.flags['S'] = 0
        
        max_val = 2**(dest_size-1) - 1
        min_val = -2**(dest_size-1)

        # Overflow detection (signed)
        if result > max_val or result < min_val:
            self.flags['O'] = 1
        else:
            self.flags['O'] = 0
        
        # Wrap result to simulate 8-bit overflow
        mask = 2**dest_size - 1
        result =  result & mask

        dest_set(result)
    

    def inc(self, dest):
        """
        Increment the value of dest by 1.
        :param dest: The destination register or memory location.
        """
        dest_get, dest_set = self.select_operand(dest)
        result = int(dest_get()) + 1
        dest_size = self.get_size(dest)

        if result == 0:
            self.flags['Z'] = 1
        else:
            self.flags['Z'] = 0
        if result * dest_get() < 0:
            self.flags['S'] = 1
        else:
            self.flags['S'] = 0

        max_val = 2**(dest_size-1) - 1
        min_val = -2**(dest_size-1)

        # Overflow detection (signed)
        if result > max_val or result < min_val:
            self.flags['O'] = 1
        else:
            self.flags['O'] = 0
        
        # Wrap result to simulate 8-bit overflow
        mask = 2**dest_size - 1
        result =  result & mask
        
        dest_set(result)
        


    def dec(self, dest):
        """
        Decrement the value of dest by 1.
        :param dest: The destination register or memory location.
        """
        dest_get, dest_set = self.select_operand(dest)
        result = int(dest_get()) - 1
        dest_size = self.get_size(dest)

        if result == 0:
            self.flags['Z'] = 1
        else:
            self.flags['Z'] = 0
        if result * dest_get() < 0:
            self.flags['S'] = 1
        else:
            self.flags['S'] = 0
            
        max_val = 2**(dest_size-1) - 1
        min_val = -2**(dest_size-1)

        # Overflow detection (signed)
        if result > max_val or result < min_val:
            self.flags['O'] = 1
        else:
            self.flags['O'] = 0
        
        # Wrap result to simulate 8-bit overflow
        mask = 2**dest_size - 1
        result =  result & mask

        dest_set(result)
    
    def and_op(self, dest, src):
        """
        Perform bitwise AND between dest and src, store result in dest.
        :param dest: The destination register or memory location.
        :param src: The source register, memory location, or immediate value.
        """

        if not CPU.is_register(dest):
            print(f"Halting execution due to invalid instruction at line {self.pc}. Unsupported operand as a label/memory address as destiny operand")
            self.halted = True

        dest_get, dest_set = self.select_operand(dest)

        try:
            src_get = int(src)
            result = int(dest_get()) & int(src_get())
        except ValueError:
            if self.get_size(dest) != self.get_size(src):
                raise ValueError(f"Operand size mismatch: dest size {self.get_size(dest)} bits, src size {self.get_size(src)} bits.")
            
            src_get, src_set = self.select_operand(src)
            result = int(dest_get()) & int(src_get())

        #verify if the result exceeds the size of the destination operand and set the carry flag accordingly
        if result == 0:
            self.flags['Z'] = 1
        else:
            self.flags['Z'] = 0
        if result * dest_get() < 0:
            self.flags['S'] = 1
        else:
            self.flags['S'] = 0    

        dest_set(result)
    

    def or_op(self, dest, src):
        """
        Perform bitwise OR between dest and src, store result in dest.
        :param dest: The destination register or memory location.
        :param src: The source register, memory location, or immediate value.
        """

        if not CPU.is_register(dest):
            print(f"Halting execution due to invalid instruction at line {self.pc}. Unsupported operand as a label/memory address as destiny operand")
            self.halted = True

        dest_get, dest_set = self.select_operand(dest)

        try:
            src_get = int(src)
            result = int(dest_get()) | int(src_get())
        except ValueError:
            if self.get_size(dest) != self.get_size(src):
                raise ValueError(f"Operand size mismatch: dest size {self.get_size(dest)} bits, src size {self.get_size(src)} bits.")

            src_get, src_set = self.select_operand(src)
            result = int(dest_get()) | int(src_get())
        
        #verify if the result exceeds the size of the destination operand and set the carry flag accordingly
        if result == 0:
            self.flags['Z'] = 1
        else:
            self.flags['Z'] = 0
        if result * dest_get() < 0:
            self.flags['S'] = 1
        else:
            self.flags['S'] = 0

        dest_set(result)
    

    def xor_op(self, dest, src):
        """
        Perform bitwise XOR between dest and src, store result in dest.
        :param dest: The destination register or memory location.
        :param src: The source register, memory location, or immediate value.
        """

        if not CPU.is_register(dest):
            print(f"Halting execution due to invalid instruction at line {self.pc}. Unsupported operand as a label/memory address as destiny operand")
            self.halted = True
        
        dest_get, dest_set = self.select_operand(dest)

        try:
            src_get = int(src)
            result = int(dest_get()) ^ int(src_get())
        except ValueError:
            if self.get_size(dest) != self.get_size(src):
                raise ValueError(f"Operand size mismatch: dest size {self.get_size(dest)} bits, src size {self.get_size(src)} bits.")

            src_get, src_set = self.select_operand(src)
            result = int(dest_get()) ^ int(src_get())

        #verify if the result exceeds the size of the destination operand and set the carry flag accordingly
        if result == 0:
            self.flags['Z'] = 1
        else:
            self.flags['Z'] = 0
        if result * dest_get() < 0:
            self.flags['S'] = 1
        else:
            self.flags['S'] = 0

        dest_set(result)
    

    def not_op(self, dest):
        """
        Perform bitwise NOT on dest, store result in dest.
        :param dest: The destination register or memory location.
        """
        dest_get, dest_set = self.select_operand(dest)
        result = ~int(dest_get())
        dest_set(result)
    

    def neg(self, dest):
        """
        Negate the value of dest (two's complement), store result in dest.
        :param dest: The destination register or memory location.
        """
        dest_get, dest_set = self.select_operand(dest)
        result = -int(dest_get())
        dest_size = self.get_size(dest)

        if result == 0:
            self.flags['Z'] = 1
        else:
            self.flags['Z'] = 0
        if result * dest_get() < 0:
            self.flags['S'] = 1
        else:
            self.flags['S'] = 0

        max_val = 2**(dest_size-1) - 1
        min_val = -2**(dest_size-1)

        # Overflow detection (signed)
        if result > max_val or result < min_val:
            self.flags['O'] = 1
        else:
            self.flags['O'] = 0
        
        # Wrap result to simulate 8-bit overflow
        mask = 2**dest_size - 1
        result =  result & mask

        dest_set(result)
    

    def xchg(self, op1, op2):
        """
        Exchange the values of op1 and op2.
        !!!Does not yet support op1 to be a memory location!!!
        :param op1: The first register or memory location.
        :param op2: The second register or memory location.
        """

        if not CPU.is_register(op1):
            print(f"Halting execution due to invalid instruction at line {self.pc}. Unsupported operand as a label/memory address as destiny operand")
            self.halted = True

        op1_get, op1_set = self.select_operand(op1)

        try:
            if(int(op2)):
                raise ValueError(f"Invalid operand {op2} for 'xchg' operation")
        except ValueError:
            if self.get_size(op1) != self.get_size(op2):
                raise ValueError(f"Operand size mismatch: dest size {self.get_size(op1)} bits, src size {self.get_size(op2)} bits.")

            op2_get, op2_set = self.select_operand(op2)

        temp = op1_get()
        op1_set(op2_get())
        op2_set(temp)
    

    def cmp(self, dest, src):
        """
        Executes a subtraction to compare both operands and affects the flags.
        :param dest: The first register.
        :param src: The second register or imidiate value.
        """

        if self.memory[self.pc+1][0] not in ['jmp', 'jb', 'jl', 'ja', 'jg', 'je', 'jne', 'jz', 'js', 'jc', 'jo']:
            print(f"SYSTEM WARNING: cmp instruction is not followed by a jump operation in line {self.pc+1}")
            self.sub_cmp(dest, src)
        else:
            self.sub_cmp(dest, src)
            self.pc += 1
            if self.memory[self.pc][0] == "jmp":
                self.jmp()
            elif self.memory[self.pc][0] == "jb" or self.memory[self.pc][0] == "jl":
                self.jl(dest, src)
            elif self.memory[self.pc][0] == "ja" or self.memory[self.pc][0] == "jg":
                self.jg(dest, src)
            elif self.memory[self.pc][0] == "jne":
                self.jne()
            elif self.memory[self.pc][0] == "jz" or self.memory[self.pc][0] == "je":
                self.jz()
            elif self.memory[self.pc][0] == "js":
                self.js()
            elif self.memory[self.pc][0] == "jc":
                self.jc()
            elif self.memory[self.pc][0] == "jo":
                self.jo()
    

    def jmp(self):
        """
        Jumps inconditionaly to a label.
        :param label: Instruction index to jump.    
        """

        label = self.memory[self.pc][1]
        if label in self.labels:
            self.pc = self.labels[label]
        else:
            raise ValueError(f"Undefined label: {label}")


    def jl(self, op1, op2):
        """
        Jumps to a label if the first operand of the previous comparison was a integer number lower than the second operator.
        :param op1: The first register.
        :param op2: The second register or imidiate value.     
        """
        op1_get, op1_set = self.select_operand(op1)

        try:
            op2 = int(op2)

            if int(op1_get()) < int(op2_get):
                label = self.memory[self.pc][1]
                if label in self.labels:
                    self.pc = self.labels[label]
                else:
                    raise ValueError(f"Undefined label: {label}")
                
        except ValueError:
            if self.get_size(op1) != self.get_size(op2):
                raise ValueError(f"Operand size mismatch: dest size {self.get_size(op1)} bits, src size {self.get_size(op2)} bits.")

            op2_get, op2_set = self.select_operand(op2)

            if int(op1_get()) < int(op2_get):
                label = self.memory[self.pc][1]
                if label in self.labels:
                    self.pc = self.labels[label]
                else:
                    raise ValueError(f"Undefined label: {label}")
            
    def jg(self, op1, op2):
        """
        Jumps to a label if the first operand of the previous comparison was a integer number bigger than the second operator.
        :param op1: The first register.
        :param op2: The second register or imidiate value.   
        """
        op1_get, op1_set = self.select_operand(op1)

        try:
            op2 = int(op2)

            if int(op1_get()) > int(op2_get):
                label = self.memory[self.pc][1]
                if label in self.labels:
                    self.pc = self.labels[label]
                else:
                    raise ValueError(f"Undefined label: {label}")
                
        except ValueError:
            if self.get_size(op1) != self.get_size(op2):
                raise ValueError(f"Operand size mismatch: dest size {self.get_size(op1)} bits, src size {self.get_size(op2)} bits.")

            op2_get, op2_set = self.select_operand(op2)

            if int(op1_get()) > int(op2_get):
                label = self.memory[self.pc][1]
                if label in self.labels:
                    self.pc = self.labels[label]
                else:
                    raise ValueError(f"Undefined label: {label}")
            
    def jne(self):
        """
        Jumps to a label if the zero flag was not activated during the comparison operation.
        """

        if self.flags['Z'] == 0:
            label = self.memory[self.pc][1]
            if label in self.labels:
                self.pc = self.labels[label]
            else:
                raise ValueError(f"Undefined label: {label}")
    
    def jz(self):
        """
        Jumps to a label if the zero flag was activated during the comparison operation.
        """

        if self.flags['Z'] == 1:
            label = self.memory[self.pc][1]
            if label in self.labels:
                self.pc = self.labels[label]
            else:
                raise ValueError(f"Undefined label: {label}")
    
    def js(self):
        """
        Jumps to a label if the signal flag was activated during the comparison operation.
        """

        if self.flags['S'] == 1:
            label = self.memory[self.pc][1]
            if label in self.labels:
                self.pc = self.labels[label]
            else:
                raise ValueError(f"Undefined label: {label}")
    
    def jc(self):
        """
        Jumps to a label if the carry flag was activated during the comparison operation.
        """

        if self.flags['C'] == 1:
            label = self.memory[self.pc][1]
            if label in self.labels:
                self.pc = self.labels[label]
            else:
                raise ValueError(f"Undefined label: {label}")
    
    def jo(self):
        """
        Jumps to a label if the overflow flag was activated during the comparison operation.
        """

        if self.flags['O'] == 1:
            label = self.memory[self.pc][1]
            if label in self.labels:
                self.pc = self.labels[label]
            else:
                raise ValueError(f"Undefined label: {label}")

        
        
    @staticmethod
    def size(file_name):
        """
        Returns the size of the program loaded from the given file, meaning the number of lines/instructions in it.
        :param file_name: The name of the file with extension.
        :return: The size of the program (number of lines).
        :requires: file_name includes the .json extension && the file exists
        :rtype: int
        """
        return len(Storage.load_file_lines(file_name))


    
    def load_program(self, file_name):
        """
        Load a program into memory from a JSON file.
        :param file_name: The name of the file with extension.
        :requires: file_name includes the .json extension && the file exists
        :rtype: None
        """
    
        program_lines = Storage.load_file_lines(file_name)

        program = []

        for i, line in enumerate(program_lines):
            line.lstrip().strip('"').strip('\"')
            if not line:
                continue
            if line.startswith(";"):
                continue
            if ";" in line:
                line = line.split(";")[0]

            instruction = line.replace(",", " ").split()  #loads directly the entire program into memory except blank lines and comments
            program.append(instruction)
            print(f"\nCARREGOU {i}")
        
        
        Storage.save_file(file_name, program)
        self.memory = program
        print("\nACABOU DE LER AS INSTRUÇÕES\n")               

    
    def fetch_instruction(self, address):
        """
        Should get the first element of a list element in memory, which is the instruction.
        """
        return self.memory[address][0]
    

    
    def validate_fetch(self):
        """
        Validates an instruction fetched from memory and its operands.
        :return: True if the instruction and operands are valid, False otherwise.
        :rtype: bool
        """
        self.instruction = self.fetch_instruction(self.pc)
        if self.instruction not in self.labels:
            operand_count = self.get_operand_number(self.pc)      

            if self.instruction not in self.valid_instructions:
                print(f"Not supported instruction: {self.instruction}")
                return False

            if operand_count != self.valid_instructions[self.instruction]:
                print(f"Invalid number of operands for \"{self.instruction}\": expected {self.valid_instructions[self.instruction]}, got {operand_count}")
                return False

        return True
    
    
    def get_operand_number(self,address):
        """
        Should get the number of operands of a list element in memory.
        :param address: The memory address of the instruction.
        :return: The number of operands.
        :rtype: int
        :requires: address is a valid memory address
        """
        return len(self.memory[address]) - 1  # Subtract 1 for the instruction itself


    
    def get_operand1(self,address):
        """
        Should get the second element of a list element in memory, which is the first operand.
        """
        return self.memory[address][1]
    

    
    def get_operand2(self, address):
        """
        Should get the third element of a list element in memory, which is the second operand.
        """
        return self.memory[address][2]
    

    def select_operand(self, operand):
        """
        Selects the appropriate register or memory location based on the operand string.
        :param operand: The operand string (e.g., 'rax', '[rbx]', etc.).
        :return: The corresponding Register object or memory address.
        :raises ValueError: If the operand is invalid.
        """
        if operand == 'rax':
            return ( lambda:self.rax._64, lambda v: setattr(self.rax, '_64', v) )
        elif operand == 'eax':
            return ( lambda:self.rax._32, lambda v: setattr(self.rax, '_32', v) )
        elif operand == 'ax':
            return ( lambda:self.rax._16, lambda v: setattr(self.rax, '_16', v) )
        elif operand == 'al':
            return ( lambda:self.rax.L8, lambda v: setattr(self.rax, 'L8', v) )
        elif operand == 'ah':
            return ( lambda:self.rax.H8, lambda v: setattr(self.rax, 'H8', v) )
        elif operand == 'rbx':
            return ( lambda:self.rbx._64, lambda v: setattr(self.rbx, '_64', v) )
        elif operand == 'ebx':
            return ( lambda:self.rbx._32, lambda v: setattr(self.rbx, '_32', v) )
        elif operand == 'bx':
            return ( lambda:self.rbx._16, lambda v: setattr(self.rbx, '_16', v) )
        elif operand == 'bl':
            return ( lambda:self.rbx.L8, lambda v: setattr(self.rbx, 'L8', v) )
        elif operand == 'bh':
            return ( lambda:self.rbx.H8, lambda v: setattr(self.rbx, 'H8', v) )
        elif operand == 'rcx':
            return ( lambda:self.rcx._64, lambda v: setattr(self.rcx, '_64', v) )
        elif operand == 'ecx':
            return ( lambda:self.rcx._32, lambda v: setattr(self.rcx, '_32', v) )
        elif operand == 'cx':
            return ( lambda:self.rcx._16, lambda v: setattr(self.rcx, '_16', v) )
        elif operand == 'cl':
            return ( lambda:self.rcx.L8, lambda v: setattr(self.rcx, 'L8', v) )
        elif operand == 'ch':
            return ( lambda:self.rcx.H8, lambda v: setattr(self.rcx, 'H8', v) )
        elif operand == 'rdx':
            return ( lambda:self.rdx._64, lambda v: setattr(self.rdx, '_64', v) )
        elif operand == 'edx':
            return ( lambda:self.rdx._32, lambda v: setattr(self.rdx, '_32', v) )
        elif operand == 'dx':
            return ( lambda:self.rdx._16, lambda v: setattr(self.rdx, '_16', v) )
        elif operand == 'dl':
            return ( lambda:self.rdx.L8, lambda v: setattr(self.rdx, 'L8', v) )
        elif operand == 'dh':
            return ( lambda:self.rdx.H8, lambda v: setattr(self.rdx, 'H8', v) )
        elif operand in ['rsi', 'esi', 'si', 'sil']:
            raise ValueError("rsi register not valid for this operation.")
        elif operand == "rdi":
            return ( lambda:self.rdi._64, lambda v: setattr(self.rdi, '_64', v) )
        elif operand in ['edi', 'di', 'dil']:
            raise ValueError("rdi register not valid for this operation.")
        #Needs changing to support memory addressing
        elif operand == 'rsp':
            raise ValueError("rsp register not valid for this operation.")
        elif operand in ['esp', 'sp']:
            raise ValueError("rsp register not valid for this operation.")
        #Needs changing to support memory addressing
        elif operand == 'rbp':
            raise ValueError("rbp register not valid for this operation.")
        elif operand in ['ebp', 'bp']:
            raise ValueError("rbp register not valid for this operation.")
        elif operand == 'r8':
            return ( lambda:self.r8._64, lambda v: setattr(self.r8, '_64', v) )
        elif operand == 'r8d':
            return ( lambda:self.r8._32, lambda v: setattr(self.r8, '_32', v) )
        elif operand == 'r8w':
            return ( lambda:self.r8._16, lambda v: setattr(self.r8, '_16', v) )
        elif operand == 'r8b':
            return ( lambda:self.r8.L8, lambda v: setattr(self.r8, 'L8', v) )
        elif operand == 'r9':
            return ( lambda:self.r9._64, lambda v: setattr(self.r9, '_64', v) )
        elif operand == 'r9d':
            return ( lambda:self.r9._32, lambda v: setattr(self.r9, '_32', v) )
        elif operand == 'r9w':
            return ( lambda:self.r9._16, lambda v: setattr(self.r9, '_16', v) )
        elif operand == 'r9b':
            return ( lambda:self.r9.L8, lambda v: setattr(self.r9, 'L8', v) )
        elif operand == 'r10':
            return ( lambda:self.r10._64, lambda v: setattr(self.r10, '_64', v) )
        elif operand == 'r10d':
            return ( lambda:self.r10._32, lambda v: setattr(self.r10, '_32', v) )
        elif operand == 'r10w':
            return ( lambda:self.r10._16, lambda v: setattr(self.r10, '_16', v) )
        elif operand == 'r10b':
            return ( lambda:self.r10.L8, lambda v: setattr(self.r10, 'L8', v) )
        elif operand == 'r11':
            return ( lambda:self.r11._64, lambda v: setattr(self.r11, '_64', v) )
        elif operand == 'r11d':
            return ( lambda:self.r11._32, lambda v: setattr(self.r11, '_32', v) )
        elif operand == 'r11w':
            return ( lambda:self.r11._16, lambda v: setattr(self.r11, '_16', v) )
        elif operand == 'r11b':
            return ( lambda:self.r11.L8, lambda v: setattr(self.r11, 'L8', v) )
        elif operand == 'r12':
            return ( lambda:self.r12._64, lambda v: setattr(self.r12, '_64', v) )
        elif operand == 'r12d':
            return ( lambda:self.r12._32, lambda v: setattr(self.r12, '_32', v) )
        elif operand == 'r12w':
            return ( lambda:self.r12._16, lambda v: setattr(self.r12, '_16', v) )
        elif operand == 'r12b':
            return ( lambda:self.r12.L8, lambda v: setattr(self.r12, 'L8', v) )
        elif operand == 'r13':
            return ( lambda:self.r13._64, lambda v: setattr(self.r13, '_64', v) )
        elif operand == 'r13d':
            return ( lambda:self.r13._32, lambda v: setattr(self.r13, '_32', v) )
        elif operand == 'r13w':
            return ( lambda:self.r13._16, lambda v: setattr(self.r13, '_16', v) )
        elif operand == 'r13b':
            return ( lambda:self.r13.L8, lambda v: setattr(self.r13, 'L8', v) )
        elif operand == 'r14':
            return ( lambda:self.r14._64, lambda v: setattr(self.r14, '_64', v) )
        elif operand == 'r14d':
            return ( lambda:self.r14._32, lambda v: setattr(self.r14, '_32', v) )
        elif operand == 'r14w':
            return ( lambda:self.r14._16, lambda v: setattr(self.r14, '_16', v) )
        elif operand == 'r14b':
            return ( lambda:self.r14.L8, lambda v: setattr(self.r14, 'L8', v) )
        elif operand == 'r15':
            return ( lambda:self.r15._64, lambda v: setattr(self.r15, '_64', v) )
        elif operand == 'r15d':
            return ( lambda:self.r15._32, lambda v: setattr(self.r15, '_32', v) )
        elif operand == 'r15w':
            return ( lambda:self.r15._16, lambda v: setattr(self.r15, '_16', v) )
        elif operand == 'r15b':
            return ( lambda:self.r15.L8, lambda v: setattr(self.r15, 'L8', v) )
        # else:
        #     if operand.startswith('[') and operand.endswith(']'):
        #         for i in range(len(self.data_segment)):
        #             if operand[1:-1] == list(self.data_segment.keys())[i]:
        #                 return (lambda: self.data_segment[list(self.data_segment.keys())[i]]['value'], lambda v: self.data_segment[list(self.data_segment.keys())[i]].__setitem__('value', v))
        #             elif operand[1:-1] == list(self.bss_segment.keys())[i]:
        #                 if self.bss_segment[list(self.bss_segment.keys())[i]][0]['value'] == 0:
        #                     raise ValueError(f"Variable {operand[1:-1]} in BSS segment is uninitialized.")
        #                 return (lambda: self.bss_segment[0]['value'], lambda v: self.bss_segment.__setitem__(0, {'size': self.bss_segment[0]['size'], 'value': v}))
        #             elif operand[1:-1] == list(self.rodata_segment.keys())[i]:
        #                 return (lambda: self.rodata_segment[list(self.rodata_segment.keys())[i]]['value'], lambda v: self.rodata_segment[list(self.rodata_segment.keys())[i]].__setitem__('value', v))
        #     else:
        #         #memory addressing not yet supported
        #         raise ValueError(f"Invalid operand or unsupported: {operand}")

        elif operand.startswith('[') and operand.endswith(']'):
            var_name = operand[1:-1]
            if var_name in self.data_segment:
                return (lambda: self.data_segment[var_name]['value'],
                        lambda v: self.data_segment[var_name].__setitem__('value', v))
            elif var_name in self.bss_segment:
                # Considera usar o primeiro elemento do array
                return (lambda: self.bss_segment[var_name][0]['value'],
                        lambda v: self.bss_segment[var_name].__setitem__(0, {'size': self.bss_segment[var_name][0]['size'], 'value': v}))
            elif var_name in self.rodata_segment:
                return (lambda: self.rodata_segment[var_name]['value'],
                        lambda v: self.rodata_segment[var_name].__setitem__('value', v))
            else:
                raise ValueError(f"Invalid operand or unsupported: {operand}")
    
    
    @staticmethod                
    def is_register(operand):
        """
        Checks if the operand is a register.
        :return: True if the operand is a register, False otherwise.
        :rtype: bool
        """
        registers = [
            'rax', 'eax', 'ax', 'al', 'ah',
            'rbx', 'ebx', 'bx', 'bl', 'bh',
            'rcx', 'ecx', 'cx', 'cl', 'ch',
            'rdx', 'edx', 'dx', 'dl', 'dh',
            'rsi', 'esi', 'si', 'sil',
            'rdi', 'edi', 'di', 'dil',
            'rsp', 'esp', 'sp',
            'rbp', 'ebp', 'bp',
            'r8', 'r8d', 'r8w', 'r8b',
            'r9', 'r9d', 'r9w', 'r9b',
            'r10', 'r10d', 'r10w', 'r10b',
            'r11', 'r11d', 'r11w', 'r11b',
            'r12', 'r12d', 'r12w', 'r12b',
            'r13', 'r13d', 'r13w', 'r13b',
            'r14', 'r14d', 'r14w', 'r14b',
            'r15', 'r15d', 'r15w',  'r15b'
        ]
        return operand in registers
    

    def get_size(self, operand):
        """
        Returns the size of the operand in bits.
        :return: Size of the operand in bits.
        :rtype: int
        """
        if self.is_register(operand):
            if operand in ['rax', 'rbx', 'rcx', 'rdx', 'rsi', 'rdi', 'rsp', 'rbp', 'r8', 'r9', 'r10', 'r11', 'r12', 'r13', 'r14', 'r15']:
                return 64
            elif operand in ['eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'esp', 'ebp', 'r8d', 'r9d', 'r10d', 'r11d', 'r12d', 'r13d', 'r14d', 'r15d']:
                return 32
            elif operand in ['ax', 'bx', 'cx', 'dx', 'si', 'di', 'sp', 'bp',  'r8w', 'r9w', 'r10w', 'r11w', 'r12w', 'r13w', 'r14w', 'r15w']:
                return 16
            elif operand in ['al', 'ah', 'bl', 'bh', 'cl', 'ch', 'dl', 'dh',  'sil', 'dil',  'r8b', 'r9b', 'r10b', 'r11b', 'r12b', 'r13b', 'r14b',  'r15b']:
                return 8
        else:
            if operand.startswith('[') and operand.endswith(']') and (operand[1:-1] in self.data_segment  or operand[1:-1] in self.bss_segment or operand[1:-1] in self.rodata_segment):
                size_str = self.data_segment[operand[1:-1]]['size']
                if size_str == 'db':
                    return 8
                elif size_str == 'dw':
                    return 16
                elif size_str == 'dd':
                    return 32
                elif size_str == 'dq':
                    return 64
                size_str = self.bss_segment[operand[1:-1]]['size']
                if size_str == 'resb':
                    return 8
                elif size_str == 'resw':
                    return 16
                elif size_str == 'resd':
                    return 32
                elif size_str == 'resq':
                    return 64
                size_str = self.rodata_segment[operand[1:-1]]['size']
                if size_str == 'db':
                    return 8
                elif size_str == 'dw':
                    return 16
                elif size_str == 'dd':
                    return 32
                elif size_str == 'dq':
                    return 64
                else:
                    print(f"Size specifier not found for variable {operand[1:-1]}.")
                    raise ValueError
            else:
                print(f"Invalid operand or unsupported: {operand}")
                raise ValueError
            

    
    def is_syscall(self):
        if self.rax._64 == 60 and self.rdi._64 == 0:  # Exit syscall
            print("Program exited successfully.")
            sys.exit(0)
        elif self.rax._64 == 1 and self.rdi._64 == 1 and int(self.rdx._64): # Print syscall
            print(self.rsi._64[:self.rdx._64 -1])
        else:
            print(f"Unsupported syscall with rax={self.rax}. Halting execution.")
            self.halted = True
        
