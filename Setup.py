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
from ClientFunctions import *
from sys import platform


def GenerateFileExclusions():
    #This Function is used to create a list of folder or file names that should be ignored when UID Finder is called
    #Metro 2033 and Metro Last Light both have folders that need to be ignored, titled 2033 and pc respectively
    SQLCreateEntry('FileExclusions',{'AppID':287390, 'Filename':'pc'})
    SQLCreateEntry('FileExclusions',{'AppID':286690, 'Filename':'2033'})
    #Star Wars X-Wing Alliance matches on .plt files, but we can ignore the test files
    SQLCreateEntry('FileExclusions',{'AppID':361670, 'Filename':'Test0.plt'})
    SQLCreateEntry('FileExclusions',{'AppID':361670, 'Filename':'Test1.plt'})
    return 0

def GenerateSkippedGames():
    #This Function is used to create a list of games that are always skipped in the databasei
    #This prevents unnecessary PCGW Requests each time we run this, since a missing PCGW page doesn't necessarily indicate that it should always be skipped
    #Hyper Light Drifter uses PC specific save files
    SQLCreateEntry('SteamApps',{'AppID':257850, 'AlwaysSkipped':1, 'Title':'Hyper Light Drifter'})
    #Valve games with no local save data
    SQLCreateEntry('SteamApps',{'AppID':570, 'AlwaysSkipped':1, 'Title':'Dota 2 Beta'})
    SQLCreateEntry('SteamApps',{'AppID':730, 'AlwaysSkipped':1, 'Title':'Counter-Strike: Global Offensive'})
    SQLCreateEntry('SteamApps',{'AppID':583950, 'AlwaysSkipped':1, 'Title':'Artifact'})
    #Other Always online games or games that have no save data associated
    SQLCreateEntry('SteamApps',{'AppID':331670, 'AlwaysSkipped':1, 'Title':'The Jackbox Party Pack'})
    SQLCreateEntry('SteamApps',{'AppID':397460, 'AlwaysSkipped':1, 'Title':'The Jackbox Party Pack 2'})
    SQLCreateEntry('SteamApps',{'AppID':434170, 'AlwaysSkipped':1, 'Title':'The Jackbox Party Pack 3'})
    SQLCreateEntry('SteamApps',{'AppID':610180, 'AlwaysSkipped':1, 'Title':'The Jackbox Party Pack 4'})
    SQLCreateEntry('SteamApps',{'AppID':774461, 'AlwaysSkipped':1, 'Title':'The Jackbox Party Pack 5'})
    SQLCreateEntry('SteamApps',{'AppID':1005300, 'AlwaysSkipped':1, 'Title':'The Jackbox Party Pack 6'})
    SQLCreateEntry('SteamApps',{'AppID':1211630, 'AlwaysSkipped':1, 'Title':'The Jackbox Party Pack 7'})
    #Various Steam and proton executables which don't have save data associated
    SQLCreateEntry('SteamApps',{'AppID':228980, 'AlwaysSkipped':1, 'Title':'Steamworks Common Redistributables'})
    SQLCreateEntry('SteamApps',{'AppID':1070560, 'AlwaysSkipped':1, 'Title':'Steam Linux Runtime'})
    SQLCreateEntry('SteamApps',{'AppID':1391110, 'AlwaysSkipped':1, 'Title':'Steam Linux Runtime - Soldier'})
    SQLCreateEntry('SteamApps',{'AppID':1493710, 'AlwaysSkipped':1, 'Title':'Proton Experimenta'})
    SQLCreateEntry('SteamApps',{'AppID':1826330, 'AlwaysSkipped':1, 'Title':'Proton EasyAntiCheat Runtime'})
    SQLCreateEntry('SteamApps',{'AppID':1628350, 'AlwaysSkipped':1, 'Title':'Proton Steam Linux Runtime - Sniper'})
    SQLCreateEntry('SteamApps',{'AppID':1161040, 'AlwaysSkipped':1, 'Title':'Proton BattlEye Runtime'})
    SQLCreateEntry('SteamApps',{'AppID':2180100, 'AlwaysSkipped':1, 'Title':'Proton Hotfix'})
    SQLCreateEntry('SteamApps',{'AppID':2230260, 'AlwaysSkipped':1, 'Title':'Proton Next'})
    SQLCreateEntry('SteamApps',{'AppID':961940, 'AlwaysSkipped':1, 'Title':'Proton 3.16'})
    SQLCreateEntry('SteamApps',{'AppID':858280, 'AlwaysSkipped':1, 'Title':'Proton 3.7'})
    SQLCreateEntry('SteamApps',{'AppID':1113280, 'AlwaysSkipped':1, 'Title':'Proton 4.11'})
    SQLCreateEntry('SteamApps',{'AppID':1054830, 'AlwaysSkipped':1, 'Title':'Proton 4.2'})
    SQLCreateEntry('SteamApps',{'AppID':1245040, 'AlwaysSkipped':1, 'Title':'Proton 5.0'})
    SQLCreateEntry('SteamApps',{'AppID':1420170, 'AlwaysSkipped':1, 'Title':'Proton 5.13'})
    SQLCreateEntry('SteamApps',{'AppID':1580130, 'AlwaysSkipped':1, 'Title':'Proton 6.3'})
    SQLCreateEntry('SteamApps',{'AppID':1887720, 'AlwaysSkipped':1, 'Title':'Proton 7.0'})
    SQLCreateEntry('SteamApps',{'AppID':2348590, 'AlwaysSkipped':1, 'Title':'Proton 8.0'})
    return 0

def GenerateAutoDetectedNonSteamGames():
    #Emulator Auto Detection
    SQLCreateEntry('NonSteamApps',{'GameID': 1, 'Title': 'Dolphin Gamecube Saves', 'RelativeSavePath': '{ HOME }.local/share/dolphin-emu/GC/', 'MostRecentSaveTime': 0 }) 
    SQLCreateEntry('NonSteamApps',{'GameID': 2, 'Title': 'Dolphin Wii Saves', 'RelativeSavePath': '{ HOME }.local/share/dolphin-emu/Wii/title/00010000', 'MostRecentSaveTime': 0 }) 
    SQLCreateEntry('NonSteamApps',{'GameID': 3, 'Title': 'Yuzu Saves', 'RelativeSavePath':'{ HOME }.local/share/yuzu/nand/user/save/0000000000000000/{ UID }', 'MostRecentSaveTime': 0 })
    SQLCreateEntry('NonSteamApps',{'GameID': 4, 'Title': 'Yuzu Keys', 'RelativeSavePath': '{ HOME }.local/share/yuzu/keys/', 'MostRecentSaveTime': 0 })
    SQLCreateEntry('NonSteamApps',{'GameID': 5, 'Title': 'Ryujinx Saves', 'RelativeSavePath': '{ HOME }.config/Ryujinx/bis/user/save/0000000000000001', 'MostRecentSaveTime': 0 })
    SQLCreateEntry('NonSteamApps',{'GameID': 6, 'Title': 'Ryujinx Keys', 'RelativeSavePath': '{ HOME }.config/Ryujinx/system/', 'MostRecentSaveTime': 0 })
    SQLCreateEntry('NonSteamApps',{'GameID': 7, 'Title': 'Ryujinx Firmware', 'RelativeSavePath': '{ HOME }.config/Ryujinx/bis/system/contents/', 'MostRecentSaveTime': 0 })
    SQLCreateEntry('NonSteamApps',{'GameID': 8, 'Title': 'Duckstation Memory Cards', 'RelativeSavePath': '{ HOME }.local/share/duckstation/memcards/', 'MostRecentSaveTime': 0 })
    SQLCreateEntry('NonSteamApps',{'GameID': 9, 'Title': 'Duckstation BIOS', 'RelativeSavePath': '{ HOME }.local/share/duckstation/bios/', 'MostRecentSaveTime': 0 })
    SQLCreateEntry('NonSteamApps',{'GameID': 10, 'Title': 'PCSX2 Memory Cards', 'RelativeSavePath': '{ HOME }.config/PCSX2/memcards/', 'MostRecentSaveTime': 0 })
    SQLCreateEntry('NonSteamApps',{'GameID': 11, 'Title': 'PCSX2 BIOS', 'RelativeSavePath':'{ HOME }.config/PCSX2/bios/', 'MostRecentSaveTime': 0 })
    #You will need to install firmware sperately? Maybe there's a way to sync the firmware too?
    SQLCreateEntry('NonSteamApps',{'GameID': 12, 'Title': 'RPCS3 Saves', 'RelativeSavePath':'{ HOME }/.config/rpcs3/dev_hdd0/home/00000001/savedata', 'MostRecentSaveTime': 0})

    return 0

def GenerateGlobalVars():
    response = input("Please specify the maximum number of saves you wish to keep backed up (default: 10): ")
    MaxSaves = 0
    IncludeSteamCloud = False
    if response == '':
        MaxSaves = 10
    else:
        MaxSaves = int(response)
    response = input("Do you wish to include Steam Cloud saves in your save game syncs? [y/N]: ")
    if response.lower() not in ['y','yes']:
        IncludeSteamCloud = False
    else:
        IncludeSteamCloud = True
    ExistingSteamCloudEntry = SQLGetEntry('GlobalVars',{'Key':'IncludeSteamCloud'},[])
    ExistingMaxSavesEntry = SQLGetEntry('GlobalVars',{'Key':'MaxSaves'},[])
    if len(ExistingSteamCloudEntry) != 0:
        SQLUpdateEntry('GlobalVars',{'Value':str(IncludeSteamCloud)},{'Key':'IncludeSteamCloud'})
    else:
        SQLCreateEntry('GlobalVars',{'Key':'IncludeSteamCloud','Value':str(IncludeSteamCloud)})
    if len(ExistingMaxSavesEntry) != 0:
        SQLUpdateEntry('GlobalVars',{'Value':str(MaxSaves)})
    else:
        SQLCreateEntry('GlobalVars',{'Key':'MaxSaves','Value':str(MaxSaves)})
    return 0

def InitializeDatabase():
    LibraryConnection = sqlite3.connect('saves.db')
    if LibraryConnection:
        Cursor = LibraryConnection.cursor()
        Tables = Cursor.execute("""SELECT name FROM sqlite_master WHERE type='table'""").fetchall()
        if len(Tables) != 0:
            print("Tables Already Present in Database")
            print("Checking for missing tables...")
        else:
            print("No tables in database")
            print("Creating database tables...")
        if ('ClientSaveInfo',) not in Tables:
            print("Creating ClientSaveInfo table...")
            LibraryConnection.execute("""CREATE TABLE ClientSaveInfo (
            AppID INT NOT NULL,
            Skipped INT,
            ClientID INT NOT NULL,
            InstallPath TEXT,
            MostRecentSaveTime REAL,
            ProtonPrefix TEXT);""")
            print("ClientSaveInfo table successfully created!")
        if ('ClientPrefixes',) not in Tables:
            print("Creating ClientPrefixes Table...")
            LibraryConnection.execute("""CREATE TABLE ClientPrefixes (
            AppID INT NOT NULL,
            ClientID INT NOT NULL,
            Prefix TEXT);""")
            print("ClientPrefixes table successfully created!")
        if ('ClientSuffixes',) not in Tables:
            print("Creating ClientSuffixes table...")
            LibraryConnection.execute("""CREATE TABLE ClientSuffixes (
            AppID INT NOT NULL,
            ClientID INT NOT NULL,
            Suffix TEXT);""")
            print("ClientSuffixes Table successfully created!")
        if ('SteamApps',) not in Tables:
            print("Creating SteamApps table...")
            LibraryConnection.execute("""CREATE TABLE SteamApps (
            AppID INT PRIMARY KEY NOT NULL,
            AlwaysSkipped INT,
            Title TEXT,
            MostRecentSaveTime REAL);""")
            GenerateSkippedGames()
            print("SteamApps table successfully created!")
        if ('SaveTimestamps',) not in Tables:
            print("Creating SaveTimestamps table...")
            LibraryConnection.execute(""" CREATE TABLE SaveTimestamps (
            AppID INT  NOT NULL,
            Timestamp REAL);""")
            print("SaveTimestamps Table successfully created!")
        if ('SavePathFixes',) not in Tables:
            print("Creating SavePathFixes table...")
            LibraryConnection.execute("""CREATE TABLE SavePathFixes (
            AppID INT NOT NULL,
            IncorrectString TEXT,
            FixedString TEXT);""")
            print("SavePathFixes table successfully created!")
        if ('FileExclusions',) not in Tables:
            print("Creating FileExclusions table...")
            LibraryConnection.execute("""CREATE TABLE FileExclusions (
            AppID INT NOT NULL,
            Filename TEXT );""")
            GenerateFileExclusions()
            print("FileExclusions table successfully created!")
        if ('RelativeSavePaths',) not in Tables:
            print("Creating RelativeSavePaths table...")
            LibraryConnection.execute("""CREATE TABLE RelativeSavePaths (
            AppID INT NOT NULL,
            RelativePath TEXT );""")
            print("RelativeSavePaths Table successfully created!")
        if ('Clients',) not in Tables:
            print("Creating Clients table...")
            LibraryConnection.execute(""" CREATE TABLE Clients (
            ClientID INT PRIMARY KEY NOT NULL,
            LastSyncTime REAL,
            SteamPath TEXT,
            HomeDir TEXT,
            ClientName TEXT)""")
            print("Clients table successfully created!")
        if ('ROMSaves',) not in Tables:
            print("Creating ROMSaves table...")
            LibraryConnection.execute("""CREATE TABLE ROMSaves (
            FileName TEXT NOT NULL,
            SubFolder TEXT,
            Timestamp REAL);""")
            print("ROMSaves table successfully created!")
        if ('RomSaveTimestamps',) not in Tables:
            print("Creating ROMSaves table...")
            LibraryConnection.execute("""CREATE TABLE RomSaveTimestamps (
            FileName TEXT NOT NULL,
            Timestamp REAL);""")
            print("RomSaveTimestamps table successfully created!")
        if ('NonSteamApps',) not in Tables:
            print("Creating NonSteamApps table...")
            LibraryConnection.execute(""" CREATE TABLE NonSteamApps (
            GameID INT NOT NULL,
            Title TEXT,
            RelativeSavePath TEXT,
            MostRecentSaveTime REAL);""")
            GenerateAutoDetectedNonSteamGames()
            print("NonSteamApps table successfully created!")
        if ('NonSteamClientSaves',) not in Tables:
            print("Creating NonSteamClientSaves table...")
            LibraryConnection.execute("""CREATE TABLE NonSteamClientSaves (
            GameID INT NOT NULL,
            ClientID INT NOT NULL,
            MostRecentSaveTime REAL,
            LocalSavePath TEXT);""")
            print("NonSteamClientSaves table successfully created!")
        if ('NonSteamSaveTimestamps',) not in Tables:
            print("Creating NonSteamSaveTimestamps Table...")
            LibraryConnection.execute("""CREATE TABLE NonSteamSaveTimestamps (
            GameID INT NOT NULL,
            Timestamp REAL);""")
            print("NonSteamSaveTimestamps table successfully created!")
        if ('GlobalVars',) not in Tables:
            print("Creating GlobalVars table...")
            LibraryConnection.execute("""CREATE TABLE GlobalVars (
            Key Text,
            Value TEXT);""")
            GenerateGlobalVars()
            print("GlobalVars table successfully created!")
        Tables = Cursor.execute("""SELECT name FROM sqlite_master WHERE type='table'""").fetchall()
        if len(Tables) == 15:
            print("All tables needed present in database.")
            print('Database successfully initialized!')
        else:
            print("Still missing tables! Consider deleting your saves.db file and rerunning SteamSync.py")
        LibraryConnection.commit()
        LibraryConnection.close()
