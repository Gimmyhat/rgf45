import os
import sys
from waitress import serve

script_directory = os.path.dirname(os.path.abspath("main.py"))
sys.path.append(script_directory)

if __name__ == "__main__":
    from app import create_app

    app = create_app()
    serve(app, listen='*:8000')
