import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from ui.dashboard import run_app

if __name__ == "__main__":
    run_app()
