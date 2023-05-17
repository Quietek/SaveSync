#!/usr/bin/env python
import os
import time
import json
import requests
import vdf
import re
import time
import sqlite3
from sys import platform
from SQLFunctions import *

#Define Main Function
if (__name__ == "__main__"):

    print("Beginning Unit Tests...")
    print("Testing Entry Creation...")
    SteamAppDict = {}
    SteamAppDict['AppID'] = 1
    SteamAppDict['Title'] = 'TestVal'
    SteamAppDict['SaveType'] = 'Directory'
    SteamAppDict['REPattern'] = ''
    SteamAppDict['MostRecentSaveTime'] = 1
    TableName = 'SteamApps'
    ColumnsWanted = []
    
    ReturnVal = SQLCreateEntry(TableName, SteamAppDict)
    if ReturnVal != 0:
        print("ERROR creating entry in SQLite Database!")
    else:
        print("Test Entry Successfully Created!")
    print("Testing Full Entry Retrieval...")
    ReturnVal = SQLGetEntry(TableName,SteamAppDict, ColumnsWanted)
    
    if len(ReturnVal) > 0:
        print("Successfully found at least one entry...")
        if ReturnVal != [{'AppID': 1, 'Title': 'TestVal', 'SaveType': 'Directory', 'REPattern': '', 'MostRecentSaveTime': 1}]:
            print("ERROR: unexpected entry found")
            print("Expected: [{'AppID': 1, 'Title': 'TestVal', 'SaveType': 'Directory', 'REPattern': '', 'MostRecentSaveTime': 1}]")
            print("Found: " + str(ReturnVal))
        else:
            print("Test Entry Fully Retrieved Successfully!")
            print("Retrieved Entry: " + str(ReturnVal))
    else:
        print("ERROR Retrieving entry from SQLite Database!")

    ColumnsWanted = ['AppID','Title']
    ReturnVal = SQLGetEntry(TableName, SteamAppDict, ColumnsWanted)
    print("Testing Partial Entry Retrieval...")
    if len(ReturnVal) > 0:
        print("Successfully found at least one entry...")
        if ReturnVal != [{'AppID': 1, 'Title': 'TestVal'}]:
            print("ERROR: unexpected entry found")
            print("Expected: [{'AppID': 1, 'Title': 'TestVal'}]")
            print("Found: " + str(ReturnVal))
        else:
            print("Test Entry Partially Retrieved Successfully!")
            print("Retrieved Entry: " + str(ReturnVal))

    ColumnsWanted = []
    print("Testing Entry Revision...")
    UpdatedAppDict = {}
    UpdatedAppDict['AppID'] = 1
    UpdatedAppDict['Title'] = 'TestVal'
    UpdatedAppDict['SaveType'] = 'Directory'
    UpdatedAppDict['REPattern'] = ''
    UpdatedAppDict['MostRecentSaveTime'] = 2

    ReturnVal = SQLUpdateEntry(TableName, UpdatedAppDict, SteamAppDict)
    if ReturnVal != 0:
        print("ERROR Updating entry in SQLite Database!")
    else:
        print("Entry Updated...")
        print("Retrieving Updated Entry...")
        ReturnVal = SQLGetEntry(TableName, UpdatedAppDict, ColumnsWanted)
        if len(ReturnVal) > 0:
            print("Successfully found at least one matching entry!")
            if ReturnVal != [{'AppID': 1, 'Title': 'TestVal', 'SaveType': 'Directory', 'REPattern': '', 'MostRecentSaveTime': 2}]:
                print("ERROR: unexpected entry found")
                print("Expected: [{'AppID': 1, 'Title': 'TestVal', 'SaveType': 'Directory', 'REPattern': '', 'MostRecentSaveTime': 2}]")
                print("Found: " + str(ReturnVal))
            else:
                print("Test Entry Updated Successfully!")
                print("Updated Entry: " + str(ReturnVal))

    print("Testing Entry Deletion...")
    ReturnVal = SQLDeleteEntry(TableName, UpdatedAppDict)
    if ReturnVal != 0:
        print("ERROR Deleting entry from SQLite Database!")
    else:
        print("Entry Deleted...")
        print("Attempting to retrieve deleted entry...")
        ReturnVal = SQLGetEntry(TableName, UpdatedAppDict, ColumnsWanted)
        
        if len(ReturnVal) > 0:
            print("ERROR: a matching entry was found when none were expected.")
            print(ReturnVal)
        else:
            print("Successfully deleted test entry!")

    print("Unit Tests Completed, Goodbye!")

