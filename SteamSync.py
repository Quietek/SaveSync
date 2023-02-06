#!/usr/bin/python
import sqlite3
import time
import os
import requests
import json
import vdf
import re
import subprocess
import shutil
from SQLFunctions import *
from ClientFunctions import *
from SyncFunctions import *



if (__name__ == "__main__"):
    HomeDir = os.path.expanduser('~')
    ConfigFile = HomeDir + "/.config/SteamSync/config"
    SyncRoms = False
    RomPathList = []
    if os.path.isfile(ConfigFile):
        ClientDictionary = ReadClientConfig(ConfigFile)
    else:
        InteractiveClientCreation()
        ClientDictionary = ReadClientConfig(ConfigFile)
    for key in ClientDictionary:
        if 'ROM' in key:
            RomPathList.append(ClientDictionary[key])
            SyncRoms = True
    if SyncRoms:
        FullSync(ClientDictionary["SteamPath"], ClientDictionary["ClientID"], ClientDictionary["SteamCloud"], RomPathList)
    else:
        FullSync(ClientDictionary["SteamPath"], ClientDictionary["ClientID"], ClientDictionary["SteamCloud"], [])
