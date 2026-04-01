import importlib.util
import os


def load_all():
    """Import all .py files in the same directory as this module (non-recursive).

    Returns a dict mapping module_name -> module for each successfully
    imported module.  Excludes load_all.py itself.
    """
    module_dict = {}
    current_dir = os.path.dirname(os.path.realpath(__file__))

    for filename in sorted(os.listdir(current_dir)):
        if not filename.endswith('.py') or filename == 'load_all.py':
            continue
        module_name = filename[:-3]
        filepath = os.path.join(current_dir, filename)
        try:
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            if spec is None:
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module_dict[module_name] = module
        except Exception:
            pass

    return module_dict


if __name__ == '__main__':
    loaded_modules = load_all()
    print('Loaded modules:', list(loaded_modules.keys()))
