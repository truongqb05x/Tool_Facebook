# -*- coding: utf-8 -*-
"""
Main Script: FB Spam Comment Group with Multi-threading & Persistent Proxies
"""
import time
import shutil
import os
import random
import json
import base64
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from selenium.webdriver.common.by import By

KIOT_PROXY_LOCK = threading.Lock()
KIOT_PROXY_CACHE = {}


from utils.file_utils import read_file
from config import config

# Modular imports
from utils.locks import FILE_LOCK


import sys
import json
import os
from config import config
from core.modes import *

if __name__ == '__main__':
    run_cli()
