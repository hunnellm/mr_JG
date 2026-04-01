import importlib
import os


def load_all():
    module_dict = {}
    # Get the current directory of the script
    current_dir = os.path.dirname(os.path.realpath(__file__))
    
    # Iterate over all files in the current directory
    for filename in os.listdir(current_dir):
        # Check for .py files excluding this file
        if filename.endswith('.py') and filename != 'load_all.py':
            module_name = filename[:-3]  # Remove the .py extension
            module_dict[module_name] = importlib.import_module(module_name)
    return module_dict


if __name__ == '__main__':
    loaded_modules = load_all()
    print('Loaded modules:', list(loaded_modules.keys()))
