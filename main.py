import os
import sys
from storage import Storage
from Cpu import CPU

def main():
    """
    Main funtion just reads a file/file paths (as a funtion argument or as an input if no arguments are given) for an asm file and builds a CPU object to execute the file.
    The file does not need to be in the same path as the folder as long as the full path is copied as an argument/input.
    In order for the file to be executed correctly or as intended it must be valid for the CPU class used (read docstring for cpu.py in this file).
    """
    while True:
        if (len(sys.argv) != 2):
            file = input("No file provided.\nPlease enter the path to the assembly file: ")
        else:
            file = sys.argv[1]

        if not os.path.isfile(file):    
            print("File not found. Please try again.")
        else:
            break
    
    cpu = CPU(file)
    cpu.execute()


if __name__ == "__main__":
    main()