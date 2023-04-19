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
    #This Function is used to create a list of games that are always skipped in the database
    #Hyper Light Drifter is always skipped since it uses PC specific save files
    SQLCreateEntry('SteamApps',{'AppID':257850, 'AlwaysSkipped':1, 'Title':'Hyper Light Drifter'})
    return 0

def GenerateGlobalVars():
    response = input("Please specify the maximum number of saves you wish to keep backed up (default: 50): ")
    MaxSaves = 0
    IncludeSteamCloud = False
    if response == '':
        MaxSaves = 50
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


#Define Main Function
if (__name__ == "__main__"):
    LibraryConnection = sqlite3.connect('saves.db')
    if LibraryConnection:
        Cursor = LibraryConnection.cursor()
        Tables = Cursor.execute("""SELECT name FROM sqlite_master WHERE type='table'""").fetchall()
        if len(Tables) != 0:
            print("Tables Already Present in Database")
            print("Checking for missing tables...")
        else:
            print("No Tables in Database")
            print("Creating Database tables...")
        if ('ClientSaveInfo',) not in Tables:
            print("Creating ClientSaveInfo Table...")
            LibraryConnection.execute("""CREATE TABLE ClientSaveInfo (
            AppID INT NOT NULL,
            Skipped INT,
            ClientID INT NOT NULL,
            InstallPath TEXT,
            MostRecentSaveTime REAL,
            ProtonPrefix TEXT);""")
            print("ClientSaveInfo Table successfully created!")
        if ('ClientPrefixes',) not in Tables:
            print("Creating ClientPrefixes Table...")
            LibraryConnection.execute("""CREATE TABLE ClientPrefixes (
            AppID INT NOT NULL,
            ClientID INT NOT NULL,
            Prefix TEXT);""")
            print("ClientPrefixes Table successfully created!")
        if ('ClientSuffixes',) not in Tables:
            print("Creating ClientSuffixes Table...")
            LibraryConnection.execute("""CREATE TABLE ClientSuffixes (
            AppID INT NOT NULL,
            ClientID INT NOT NULL,
            Suffix TEXT);""")
            print("ClientSuffixes Table successfully created!")
        if ('SteamApps',) not in Tables:
            print("Creating SteamApps Table...")
            LibraryConnection.execute("""CREATE TABLE SteamApps (
            AppID INT PRIMARY KEY NOT NULL,
            AlwaysSkipped INT,
            Title TEXT,
            MostRecentSaveTime REAL);""")
            print("SteamApps Table successfully created!")
        if ('SaveTimestamps',) not in Tables:
            print("Creating SaveTimestamps Table...")
            LibraryConnection.execute(""" CREATE TABLE SaveTimestamps (
            AppID INT PRIMARY KEY NOT NULL,
            Timestamp REAL);""")
            print("SaveTimestamps Table successfully created!")
        if ('SavePathFixes',) not in Tables:
            print("Creating SavePathFixes Table...")
            LibraryConnection.execute("""CREATE TABLE SavePathFixes (
            AppID INT NOT NULL,
            IncorrectString TEXT,
            FixedString TEXT);""")
            print("SavePathFixes Table successfully created!")
        if ('FileExclusions',) not in Tables:
            print("Creating FileExclusions Table...")
            LibraryConnection.execute("""CREATE TABLE FileExclusions (
            AppID INT NOT NULL,
            Filename TEXT );""")
            print("FileExclusions Table successfully created!")
        if ('RelativeSavePaths',) not in Tables:
            print("Creating RelativeSavePaths Table...")
            LibraryConnection.execute("""CREATE TABLE RelativeSavePaths (
            AppID INT NOT NULL,
            RelativePath TEXT );""")
            print("RelativeSavePaths Table successfully created!")
        if ('Clients',) not in Tables:
            print("Creating Clients Table...")
            LibraryConnection.execute(""" CREATE TABLE Clients (
            ClientID INT PRIMARY KEY NOT NULL,
            LastSyncTime REAL,
            SteamPath TEXT,
            HomeDir TEXT,
            ClientName TEXT)""")
            print("Clients Table successfully created!")
        if ('ROMSaves',) not in Tables:
            print("Creating ROMSaves Table...")
            LibraryConnection.execute("""CREATE TABLE ROMSaves (
            FileName TEXT NOT NULL,
            SubFolder TEXT,
            Timestamp REAL);""")
            print("ROMSaves Table successfully created!")
        if ('RomSaveTimestamps',) not in Tables:
            print("Creating ROMSaves Table...")
            LibraryConnection.execute("""CREATE Table RomSaveTimestamps (
            FileName TEXT NOT NULL,
            Timestamp REAL);""")
            print("RomSaveTimestamps Table successfully created!")
        if ('NonSteamApps',) not in Tables:
            print("Creating NonSteamApps Table...")
            LibraryConnection.execute(""" CREATE TABLE NonSteamApps (
            GameID INT NOT NULL,
            Title TEXT,
            RelativeSavePath TEXT,
            MostRecentSaveTime REAL);""")
            print("NonSteamApps Table successfully created!")
        if ('NonSteamClientSaves',) not in Tables:
            print("Creating NonSteamClientSaves Table...")
            LibraryConnection.execute("""CREATE TABLE NonSteamClientSaves (
            GameID INT NOT NULL,
            ClientID INT NOT NULL,
            LocalSavePath TEXT);""")
            print("NonSteamClientSaves Table successfully created!")
        if ('NonSteamSaveTimestamps',) not in Tables:
            print("Creating NonSteamSaveTimestamps Table...")
            LibraryConnection.execute("""CREATE TABLE NonSteamSaveTimestamps (
            GameID INT NOT NULL,
            Timestamp REAL);""")
            print("NonSteamSaveTimestamps Table successfully created!")
        if ('GlobalVars',) not in Tables:
            print("Creating GlobalVars Table...")
            LibraryConnection.execute("""CREATE TABLE GlobalVars (
            Key Text,
            Value TEXT);""")
            print("GlobalVars Table successfully created!")
        Tables = Cursor.execute("""SELECT name FROM sqlite_master WHERE type='table'""").fetchall()
        if len(Tables) == 15:
            print("All Tables Needed Present in Database.")
        else:
            print("Still Missing Tables! Consider deleting your saves.db file and rerunning setup.py")
        GenerateFileExclusions()
        GenerateSkippedGames()
        GenerateGlobalVars()
        InteractiveClientCreation()
        LibraryConnection.commit()
        LibraryConnection.close()
