import os

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR = os.path.dirname(_CURRENT_DIR)
_PROJECT_ROOT = os.path.dirname(_SRC_DIR)
DB_DIR = os.path.join(_PROJECT_ROOT, "db")

print("test path" ,os.path.abspath(__file__))
print("get current working directory" , os.getcwd())

print(f"\n source dir {_SRC_DIR}")
print(f"\n project dir {_PROJECT_ROOT}")
print(f"\n database dir {DB_DIR}")