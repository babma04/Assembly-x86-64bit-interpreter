import json
import os


"""
Utility class for file storage operations.
Takes care of all creation, reading and writing operations to files.
All file creations are done in the project directory and to a JSON file format.
Contains static methods only.
"""

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))  # folder of the current script

class Storage:
    
    @staticmethod
    def convert_to_json(file_name):
        """
        Convert any given file to a JSON file.
        :param file_name: The name of the file with extension.
        :return: The name of the new JSON file and creates a .json file with the same content.
        :requires: file_name includes the extension
        :rtype: str
        """
        new_file_name = file_name.split(".")[0] + ".json"
        
        raw_text = Storage.load_file(file_name).split("\n")
        clean_lines = []

        for line in raw_text:
            if ";" in line:
                line = line.split(";")[0]
                if line == "":
                    continue
            clean_lines.append(line.strip())
            
        Storage.save_file(new_file_name, clean_lines)
        return new_file_name
        

    @staticmethod
    def save_file(file_name, data):
        """
        Save data to a JSON file in the project folder.
        :param file_name: The name of the file (without extension).
        :param data: The data to save (must be serializable to JSON).
        :requires: file_name includes the .json extension
        :rtype: None
        """
        file_path = os.path.join(PROJECT_DIR, file_name)
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)


    @staticmethod
    def load_file(file_name):
        """
        Load account information from a file and returns it in json format.
        :param file_name: The name of the file with extension.
        :param file_path: The full path to the JSON file.
        :return: The file's data, or None if the file doesn't exist.
        :requires: file_name includes the .json extension && the file exists
        """
        file_path = os.path.join(PROJECT_DIR, file_name)
        try:
            with open(file_path) as f:
                return f.read()
        except FileNotFoundError:
            print(f"Something went wrong! File {file_name} cound't be opened.")
            return None
    

    @staticmethod
    def load_file_lines(file_name):
        """
        Returns the contents of a JSON file previously converted into a single String as a list of every line in the file.
        Searches for line breaks to define new lines
        :param file_name: The name of the file with extension.
        :return: A list of strings, each representing a line in the file.
        :requires: file_name includes the .json extension && the file exists 
        """
        file_path = os.path.join(PROJECT_DIR, file_name)
        with open(file_name, "r") as f:
            return json.load(f)