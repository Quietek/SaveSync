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
        print(Tables)
        if ('ClientSaveInfo',) not in Tables:
            LibraryConnection.execute("""CREATE TABLE ClientSaveInfo (
            AppID INT NOT NULL,
            Skipped INT,
            ClientID INT NOT NULL,
            InstallPath TEXT,
            MostRecentSaveTime REAL,
            ProtonPrefix TEXT);""")
        if ('ClientPrefixes',) not in Tables:
            LibraryConnection.execute("""CREATE TABLE ClientPrefixes (
            AppID INT NOT NULL,
            ClientID INT NOT NULL,
            Prefix TEXT);""")
        if ('ClientSuffixes',) not in Tables:
            LibraryConnection.execute("""CREATE TABLE ClientSuffixes (
            AppID INT NOT NULL,
            ClientID INT NOT NULL,
            Suffix TEXT);""")
        if ('SteamApps',) not in Tables:
            LibraryConnection.execute("""CREATE TABLE SteamApps (
            AppID INT PRIMARY KEY NOT NULL,
            AlwaysSkipped INT,
            Title TEXT,
            MostRecentSaveTime REAL);""")
        if ('SaveTimestamps',) not in Tables:
            LibraryConnection.execute(""" CREATE TABLE SaveTimestamps (
            AppID INT PRIMARY KEY NOT NULL,
            Timestamp REAL);""")
        if ('SavePathFixes',) not in Tables:
            LibraryConnection.execute("""CREATE TABLE SavePathFixes (
            AppID INT NOT NULL,
            IncorrectString TEXT,
            FixedString TEXT);""")
        if ('FileExclusions',) not in Tables:
            LibraryConnection.execute("""CREATE TABLE FileExclusions (
            AppID INT NOT NULL,
            Filename TEXT );""")
        if ('RelativeSavePaths',) not in Tables:
            LibraryConnection.execute("""CREATE TABLE RelativeSavePaths (
            AppID INT NOT NULL,
            RelativePath TEXT );""")
        if ('Clients',) not in Tables:
            LibraryConnection.execute(""" CREATE TABLE Clients (
            ClientID INT PRIMARY KEY NOT NULL,
            LastSyncTime REAL,
            SteamPath TEXT,
            HomeDir TEXT,
            ClientName TEXT)""")

        GenerateFileExclusions()
        GenerateSavePathFixes()
        Tables = Cursor.execute("""SELECT name FROM sqlite_master WHERE type='table'""").fetchall()
        print(Tables)

        LibraryConnection.commit()
        LibraryConnection.close()
