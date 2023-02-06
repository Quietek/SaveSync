#!/usr/bin/python
import os
import time
import json
import requests
import vdf
import re
import time
import sqlite3
from sys import platform


def GenerateFileExclusions():
    return 0

def GenerateSavePathFixes():
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
            Timestamp REAL)""")
        Tables = Cursor.execute("""SELECT name FROM sqlite_master WHERE type='table'""").fetchall()
        if len(Tables) == 10:
            print("All Tables Needed Present in Database.")
        else:
            print("Still Missing Tables! Consider deleting your saves.db file and rerunning setup.py")
        GenerateFileExclusions()
        GenerateSavePathFixes()
        LibraryConnection.commit()
        LibraryConnection.close()
