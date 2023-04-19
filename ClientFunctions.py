#!/usr/bin/python
import os
import time
import json
import requests
import vdf
import re
import time
import sqlite3
from SQLFunctions import *
from sys import platform

def CreateClient(IDNum, ClientName, ConfigPath, HomePath, SteamPath, RomPath):
    print("Registering new client with database...")
    SQLCreateEntry('Clients',{'ClientID':IDNum, 'ClientName':ClientName, 'HomeDir':HomePath, 'SteamPath':SteamPath})
    print("Client Successfully registered!")
    print("Writing client configuration to " + ConfigPath + "...")
    os.makedirs(HomePath + '/.config/SteamSync/', exist_ok=True)
    File = open(ConfigPath, "w+")
    File.write("ClientID=" + str(IDNum) + '\n')
    File.write("ClientName=" + ClientName + '\n')
    File.write("HomeDir=" + HomePath + "/" +'\n')
    File.write("SteamPath=" + SteamPath + "/" + '\n')
    if RomPath:
        File.write("ROMs=" + RomPath)
    print("Local configuration file successfully created!")
    return 0
    

def ReadClientConfig(ConfigPath):
    ReturnDictionary = {}
    File = open(ConfigPath, "r")
    Lines = File.readlines()
    for line in Lines:
        TempSplit = line.split('=')
        if ':' not in TempSplit[0] and TempSplit[0] != 'ROMs':
            ReturnDictionary[TempSplit[0]] = TempSplit[1].replace('\n','')
        elif ':' in TempSplit[0]:
            Tag = TempSplit[0].split(':')[1]
            ReturnDictionary["ROMS/" + Tag] = {}
            ReturnDictionary["ROMS/" + Tag] = {'Tag':Tag, 'Subfolder':True, 'Path':TempSplit[1].replace('\n','')}
        else:
            ReturnDictionary["ROMS"] = {}
            ReturnDictionary["ROMS"] = {'Tag': '', 'Subfolder':False, 'Path':TempSplit[1].replace('\n','')}
    if "ClientID" in ReturnDictionary:
        ReturnDictionary["ClientID"] = int(ReturnDictionary["ClientID"])
    else:
        ReturnDictionary["ClientID"] = 0
    return ReturnDictionary

def InteractiveClientCreation():
    Clients = SQLGetEntry('Clients',{},[])
    ClientID = len(Clients)
    ExitFlag = False
    HomeDir = os.path.expanduser('~')
    SteamDir = ''
    RomDir = ''
    ConfigPath = HomeDir + '/.config/SteamSync/config'
    if os.path.isfile(ConfigPath):
        print('Warning! A config file was detected at ' + ConfigPath)
        print('Continuing to run this program may overwrite your current configuration, and incorrectly sync your save files.')
        print('Please make sure you aren\'t using this client with multiple SteamSync Servers before proceeding.')
        response = input('Please confirm whether to proceed with client creation in database and overwriting the present config file [y/N]: ')
        if response.lower() in ['y','yes']:
            ExitFlag = False
        else:
            ExitFlag = True
    if not ExitFlag:
        print("This program will create a new client in the SteamSync database and create a local config file at " + ConfigPath)
        response = input('Please type a friendly name for this client: ')
        ClientName = response
        response = input('Please specify the path to your steam install: (default: ' + HomeDir + '/.local/share/Steam/ ): ')
        while (not os.path.isdir(response)) and response != '':
            response = input('The specified path could not be found, please try again (or leave blank for the default path): ')
        if response != '':
            SteamDir = response
        else:
            SteamDir = HomeDir + '/.local/share/Steam'
        response = input('Please specify a path to your ROMs folder (or leave blank to skip Syncing ROMs on this client): ')
        if response:
            RomDir = response
        print("Creating New Client...")
        CreateClient(ClientID, ClientName, ConfigPath, HomeDir, SteamDir, RomDir)
        print("Client Successfully Created!")
        return 0
        
def InteractiveDatabaseManagement():
    return 0        
        

