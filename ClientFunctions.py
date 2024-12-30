#!/usr/bin/python
import os
import time
import json
import requests
import vdf
import re
import datetime
import sqlite3
from SQLFunctions import *
from SyncFunctions import *
from Setup import *
from sys import platform



#A helper function to register a new client to the database and create our config file
def CreateClient(IDNum, ClientName, ConfigPath, HomePath, SteamPath, RomPath):
    print("Registering new client with database...")
    #This is where the client gets registered to the database
    SQLCreateEntry('Clients',{'ClientID':IDNum, 'ClientName':ClientName, 'HomeDir':HomePath, 'SteamPath':SteamPath})
    print("Client Successfully registered!")
    print("Writing client configuration to " + ConfigPath + "...")
    #This is where we make our config path and write to the config file
    os.makedirs(HomePath + '/.config/SaveSync/', exist_ok=True)
    File = open(ConfigPath, "w+")
    File.write("ClientID=" + str(IDNum) + '\n')
    File.write("ClientName=" + ClientName + '\n')
    File.write("HomeDir=" + HomePath + "/" +'\n')
    File.write("SteamPath=" + SteamPath + "/" + '\n')
    #We don't always sync ROMs, so we make sure at least one ROM Path was specified before writing the ROMPath to the config file
    if RomPath:
        File.write("ROMs=" + RomPath)
    print("Local configuration file successfully created!")
    return 0
    
#NOTE: This currently only checks to makes sure the number of needed tables are present, needs to be revised to also check all table names and their columns.
#This function is used to make sure the database is how we expect it to be and usable as a result
def CheckDBIntegrity():
    print('Checking database integrity...')
    LibraryConnection = sqlite3.connect('saves.db')
    if LibraryConnection:
        Cursor = LibraryConnection.cursor()
        Tables = Cursor.execute("""SELECT name FROM sqlite_master WHERE type='table'""").fetchall()
        if len(Tables) != 15:
            InitializeDatabase()
            print('Database repaired.')
        else:
            print('Database integrity successfully verified.')
    else:
        print('ERROR: Could not establish connection to database file.')


#This function reads in the values from the 
def ReadClientConfig(ConfigPath):
    #Variable Initialization
    ReturnDictionary = {}
    #Opening our file to read from
    File = open(ConfigPath, "r")
    #We get a list of individual lines from the config file
    Lines = File.readlines()
    #We iterate through every line in the config
    for line in Lines:
        #We split on the = sign within the file, and always know that our dictionary key is the first item in the list, and the second item in the list is our value
        #We have to handle ROM Folders differently
        TempSplit = line.split('=')
        if ':' not in TempSplit[0] and TempSplit[0] != 'ROMs':
            ReturnDictionary[TempSplit[0]] = TempSplit[1].replace('\n','')
        #: being in the first item in the list means that we're dealing with a ROM Subfolder
        elif ':' in TempSplit[0]:
            #We pull the subfolder name/tag by taking everything after the : character but before the =
            Tag = TempSplit[0].split(':')[1]
            ReturnDictionary["ROMS/" + Tag] = {}
            #We then add the new subfolder to our return dictionary
            ReturnDictionary["ROMS/" + Tag] = {'Tag':Tag, 'Subfolder':True, 'Path':TempSplit[1].replace('\n','')}
        else:
            #This is information for our ROM root folder, which is directly synced with ./ROMs/
            ReturnDictionary["ROMS"] = {}
            ReturnDictionary["ROMS"] = {'Tag': '', 'Subfolder':False, 'Path':TempSplit[1].replace('\n','')}
    #We need to make sure a Client ID is specified, but if it's not we just default to 0
    if "ClientID" in ReturnDictionary:
        ReturnDictionary["ClientID"] = int(ReturnDictionary["ClientID"])
    else:
        ReturnDictionary["ClientID"] = 0
    return ReturnDictionary

#This function is used to help users add a non-Steam game to the database without the need to use command line arguments
def NonSteamEntryHelperFunction(PathToSteam, ClientID, HomeDir, GameID=0):
    print('This is a function for adding a non-Steam Game to the SaveSync database or manually specifying a local savepath .')
    #We initialize our NewGameID value and read in a list of non-Steam games
    NewGameID = 0
    NonSteamGamesList = SQLGetEntry('NonSteamApps',{}, [])
    RelativeSavePath = ''
    #Being passed a GameID of 0 indicates we're creating a new save entry in the database
    if GameID == 0:
        #Prompt user for the game's title, technically this isn't required but without it it'll be a lot harder for the user to identify games later
        GameTitle = input('Please input a title for this game: ')
        #Quick catch to make sure the user isn't trying to exit the program
        if GameTitle.lower() not in ['q', 'quit', 'exit' ]:
            #Prompt the user for the game's save game path
            print('You can specify a PC specific generated directory with { UID }')
            LocalSavePath = input('Please type the path to this game\'s saves: ')
            #Extra check to make sure the user isn't trying to quit the program
            if LocalSavePath.lower() not in ['q', 'quit', 'exit' ]:
                #We get the Maximum ID value from our list of non-steam games and add 1 to create the new GameID
                #NOTE I initially wanted to just use the length of the list, but we can't do that, since a user can add a game, then add a second game, then delete the first game, resulting in the system trying to create 2 games with the same GameID
                if len(NonSteamGamesList) > 0:
                    NewGameID = SQLGetMinMax('NonSteamApps','GameID', {})[0]['MaxVal'] + 1
                #We can't use the min/max function on an empty list, so if the list is empty we just set the game id to 1
                else:
                    NewGameID = '1'
                #We read our local save path into our Relative save path before making any substitutions
                RelativeSavePath = LocalSavePath
                ContinueFlag = True
                if '{ UID }' in LocalSavePath:
                    SavePathList = UIDFinder(LocalSavePath)
                    if len(SavePathList) == 0:
                        print('ERROR: No matching filepaths were found.')
                        ContinueFlag = False
                    elif len(SavePathList) > 1:
                        print('ERROR: UID Tag should be used to distinguish PC specific filepaths')
                        print('If you are trying to add a game with multiple save paths, it is recommended you add the individual saves as separate non-Steam games.')
                        ContinueFlag = False
                    else:
                        LocalSavePath = SavePathList[0]
                #We consider any path with the string drive_c in it to be a wine prefix
                #Technically there is potential for false positives here, but it should be pretty low likelihood
                if ContinueFlag:
                    if 'drive_c' in RelativeSavePath:
                        #We consider everything prior to the drive_c string to be the path to our wine prefix
                        WinePrefix = RelativeSavePath.split('drive_c')[0]
                        #We substitute in { WINE PREFIX } so that we know where to look when we sync on new clients
                        RelativeSavePath = RelativeSavePath.replace(WinePrefix, '{ WINE PREFIX }')
                    #We need to check whether the home path is somewhere in the remaining file path, this will only happen if we didn't already label this game as being installed to a wine prefix
                    elif HomeDir in RelativeSavePath:
                        #We replace the string in our relative save path, and write the new entries to the database
                        RelativeSavePath = RelativeSavePath.replace(HomeDir, '{ HOME }')
                    SQLCreateEntry('NonSteamApps', {'GameID': NewGameID, 'Title': GameTitle, 'RelativeSavePath': RelativeSavePath, 'MostRecentSaveTime': 0})
                    SQLCreateEntry('NonSteamClientSaves', {'GameID': NewGameID, 'ClientID':ClientID, 'LocalSavePath':LocalSavePath, 'MostRecentSaveTime': 0 })
        #If a GameID was passed in, we need to handle it differently, since that indicates we're syncing an existing known non-Steam game to a custom location
    else:
        #Prompt user for the save game path
        LocalSavePath = input('Please type the path to this game\'s saves: ')
        #Checking to make sure the user doesn't actually want to quit from this program
        if LocalSavePath.lower() not in [ 'q', 'quit', 'exit' ]:
            #We check the database to see if the game has already registered a save path on this client
            LocalGameEntryCheck = SQLGetEntry('NonSteamClientSaves', {'GameID': GameID, 'ClientID': ClientID},[])
            #If the game is already registered we update the value in the database
            if len(LocalGameEntryCheck) > 0 and LocalSavePath.lower() not in [ 'q', 'quit', 'exit' ]:
                SQLUpdateEntry('NonSteamClientSaves', { 'LocalSavePath': LocalSavePath }, { 'GameID': GameID, 'ClientID': ClientID })
            #But if it's not registered, we create a new value in the database for the game
            elif LocalSavePath.lower()  not in [ 'q', 'quit', 'exit' ]:
                SQLCreateEntry('NonSteamClientSaves', { 'GameID': GameID, 'ClientID': ClientID, 'LocalSavePath': LocalSavePath })
    #Terminal output to keep the user updated on whether the non-steam game was created successfully or not
    if GameTitle.lower() not in [ 'q', 'quit', 'exit' ] and LocalSavePath.lower() not in [ 'q', 'quit', 'exit' ]:        
        print('Non-Steam game successfully set in Database!')
        print('Game save will be synced on next full or non-steam sync.')
    return 0

#This is a function that will generate a new config file for the current client, this is generally only called when a config file doesn't already exist
def InteractiveClientCreation(ConfigPath):
    #We get a list of our clients and initialize other releveant variables
    Clients = SQLGetEntry('Clients',{},[])
    ClientID = len(Clients)
    ExitFlag = False
    HomeDir = os.path.expanduser('~')
    SteamDir = ''
    RomDir = ''
    #We double check to make sure the user wants to overwrite the config file if the config already exists. Defaults to a response of no if the response isn't some variation of y or yes
    if os.path.isfile(ConfigPath):
        print('Warning! A config file was detected at ' + ConfigPath)
        print('Continuing to run this program may overwrite your current configuration, and incorrectly sync your save files.')
        print('Please make sure you aren\'t using this client with multiple SaveSync Servers before proceeding.')
        response = input('Please confirm whether to proceed with client creation in database and overwriting the present config file [y/N]: ')
        #We set an exit flag parameter to tell us if the user actually wants to exit
        if response.lower() in ['y','yes']:
            ExitFlag = False
        else:
            ExitFlag = True
    #If we make it past this, we know the user does indeed want to create a new client config
    if not ExitFlag:
        print("This program will create a new client in the SaveSync database and create a local config file at " + ConfigPath)
        #Prompt the user for a client name
        #Technically this isn't used for anything, but it may be needed at some point
        response = input('Please type a friendly name for this client: ')
        ClientName = response
        #We prompt the user for the path to their steam install, if they don't respond we default to ~/.local/share/Steam/ since that's typically where steam is installed.
        #As a note this is untested for custom locations, which may be a problem for Flatpak users?
        response = input('Please specify the path to your steam install (default: ' + HomeDir + '/.local/share/Steam/ ): ')
        #We make sure the path actually exists before moving on
        #NOTE: does not check whether the default path exists before writing it to the config file.
        while (not os.path.isdir(response)) and response != '':
            response = input('The specified path could not be found, please try again (or leave blank for the default path): ')
        #An empty resonse means we're using the default, otherwise we are using the response
        if response != '':
            SteamDir = response
        else:
            SteamDir = HomeDir + '/.local/share/Steam'
        #We then prompt the user for a path to their ROMs if they choosing to.
        #An Empty response indicates they aren't syncing ROMs 
        response = input('Please specify a path to your ROMs folder (or leave blank to skip Syncing ROMs on this client): ')
        #If we got a response, we save it as our ROM path, but otherwise we just leave it as an empty value
        if response:
            RomDir = response
        #We check to see if the database exists and initialize it if it doesn't exist
        if not os.path.isfile('./saves.db'):
            print('No Database Detected! Initializing new SQLite Database...')
            InitializeDatabase()
            print('Database Successfully Created')
        #We finally call our client creation function to register the client to the database and write our config file
        print("Creating New Client...")
        CreateClient(ClientID, ClientName, ConfigPath, HomeDir, SteamDir, RomDir)
        print("Client Successfully Created!")
    return 0


#This is a function that will read a list of games, print the list of games with formatting, and returns a list of all the game ids in the passed in game list
def GameListReadAndPrint(IDType, GameList):
    #Return Value initialization
    IDList = []
    #We take an extra step for formatting to keep it consistent, since GameID is 6 characters but AppID is 5
    if len(IDType) == 5:
        print(IDType.upper() + '                     TITLE')
    elif len(IDType) == 6:
        print(IDType.upper() + '                    TITLE')
    #We iterate through our list of games
    for entry in GameList:
        #We add each GameID to our return list
        IDList.append(entry[IDType])
        #Variable initialization
        PrefixStr = ''
        #Formatting to keep AppIDs and GameIDs justified the same way
        if len(str(entry[IDType])) < 10:
            for i in range(10 - len(str(entry[IDType]))):
                PrefixStr = PrefixStr + ' '
        #We read the title from our game list if we can
        if 'Title' in entry:
            Title = entry['Title']
        #If we can't find a title in our current dictionary, we query the database for it
        else:
            if IDType == 'AppID':
                Title = SQLGetEntry('SteamApps',{ 'AppID': entry['AppID'] }, [])[0]['Title']
            else:
                Title = SQLGetEntry('NonSteamApps', { 'GameID': entry['GameID'] }, [])[0]['Title']
        #We print our game entry to the console with our extra formatting
        print(PrefixStr + str(entry[IDType]) + '                ' + Title)
    return IDList

#This function is a very comprehensive interactive CLI for interacting with the database
def InteractiveDatabaseManager(PathToSteam, PathToConfig):
    #We read the config and initialize our variables
    ClientDictionary = ReadClientConfig(PathToConfig)
    if 'HomeDir' in ClientDictionary:
        HomeDir = ClientDictionary['HomeDir']
    else:
        HomeDir = os.path.expanduser('~')
    RomPathList = []
    LibList = []
    SyncRoms = False
    #We need to open our steam library vdf
    #TODO add in file existence check
    PathToVDF = PathToSteam + "steamapps/libraryfolders.vdf"
    LibraryVDFDict = vdf.load(open(PathToVDF))
    #We iterate through our various steam libraries, these are generally steam games installed to drives that aren't the root filesystem
    for Library in LibraryVDFDict['libraryfolders']:
        #We load the path from the library we're currently looking at
        LibList.append(Library)
    #We pull our global values from the database
    MaxSaves = int(SQLGetEntry('GlobalVars',{'Key':'MaxSaves'},[])[0]['Value'])
    RawSteamCloud = SQLGetEntry('GlobalVars',{'Key':'IncludeSteamCloud'},[])[0]['Value']
    #We Read in our ROM Paths from our dictionary of config values for later
    for key in ClientDictionary:
        if 'ROM' in key:
            RomPathList.append(ClientDictionary[key]) 
            SyncRoms = True
    #The steam cloud value is going to back as a string, so we need to conver to a boolean
    if RawSteamCloud == 'True':
        IncludeSteamCloud = True
    else:
        IncludeSteamCloud = False
    #Main CLI menu prompt, stays open until the user manually quits or exits
    response = ''
    while response.lower() not in [ 'q', 'quit', 'exit' ]:
        #we consider any time response is empty to be the first run
        #Technically gives false positives, and will redisplay if the user doesn't input anything when prompted
        if response == '':
            print('Welcome to SaveSync\'s interactive database management system!')
            print('If you find an error in a steam game\'s save path, please consider helping others out too and updating it\'s entry on PCGamingWiki!')
        #We make sure that the response is eligible before moving on and let the user know we can't interpret their input
        elif response not in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13' ]:
            print('ERROR: ' + response + ' is not a recognized option, please select a valid entry from the list below: ')
        #Main menu prompt, with 13 functions to choose from
        else:
            print('Please make a selection from the list below: ')
        print('1. Sync all games')
        print('2. Help me add a new non-Steam Game to the Client or Server')
        print('3. Help me add a new ROM Folder')
        print('4. Sync ROM Folders')
        print('5. Sync non-Steam Library')
        print('6. Sync specific Steam game')
        print('7. Sync specific non-Steam game')
        print('8. Manually update entry for Steam game')
        print('9. Manually update entry for non-Steam game')
        print('10. Delete Steam game Entry')
        print('11. Delete non-Steam game Entry')
        print('12. Rollback game save')
        print('13. Verify database integrity')
        print('Type q, quit, or exit to quit this program')
        response = input('Please select an entry (1-13): ')
        #We perform a full system sync
        if response == '1':
            #Technically I believe this is unnecessary since if no ROM paths are read in RomPathList will be an empty list, but regardless we execute the command slightly differently depending on if we're syncing ROMs or not
            if SyncRoms:
                FullSync(ClientDictionary["SteamPath"], ClientDictionary["ClientID"], IncludeSteamCloud, RomPathList, MaxSaves, False, HomeDir)
            else:
                FullSync(ClientDictionary["SteamPath"], ClientDictionary["ClientID"], IncludeSteamCloud, [], MaxSaves, False, HomeDir)
        #The user wants to add a non-steam game
        elif response == '2':
            #We prompt the user asking whether they are trying to add a path for an already known non-Steam game or if they are adding a brand new game
            print('1. Manually specify a Local Save Path for an existing non-Steam game')
            print('2. Add a brand new non-Steam game to the database')
            Selection = input('Please select an entry (1-2): ')
            #We check to make sure we have a selection that we can interpret before moving forward
            while Selection.lower() not in ['1', '2', 'q', 'quit', 'exit' ]:
                print('ERROR: ' + Selection + 'is not a recognized selection')
                Selection = input('Please select an entry (1-2): ')
            #The user wants to add a local save path for a game that already exists
            if Selection == '1':
                #We get a list of all the known non-Steam games
                NonSteamGames = SQLGetEntry('NonSteamApps', {}, [])
                #We only go forward if we have at least 1 non-Steam game
                if len(NonSteamGames) > 0:
                    #We print the list of GameIDs and their titles, and ask the user for a gameID that they wish to update
                    GameIDList = GameListReadAndPrint('GameID', NonSteamGames)
                    LinkedGameID = input('Please select an entry by typing it\'s GameID: ')
                    #We make sure we can interpret the users input before moving forward
                    while LinkedGameID not in GameIDList and LinkedGameID.lower() not in [ 'q', 'quit', 'exit' ]:
                        print('ERROR: ' + LinkedGameID + 'is not a recognized selection.')
                        LinkedGameID = input('Please select an entry by typing it\'s GameID: ')
                    NonSteamEntryHelperFunction(PathToSteam, ClientDictionary['ClientID'], ClientDictionary['HomeDir'], LinkedGameID)
            #If we are creating a new non-Steam game, we just have to call the helper function since we don't need any other information
            elif Selection == '2':
                NonSteamEntryHelperFunction(PathToSteam, ClientDictionary['ClientID'], ClientDictionary['HomeDir'])
        #The user wants to add a new ROM Folder
        elif response == '3':
            #We proceed based on whether there is a ROM folder or not
            if SyncRoms == True:
                print('This function is used to help you add a new ROM folder to your SaveSync Library.')
                print('NOTE: You may also add new ROM folder by writing new entries in the format ROMS:{subfolder}={path}')
                #TODO Add help entries for formatting and other tips
                #Prompt the user for the file paths and a name for their new ROM Folder
                Subfolder = input('Please input a friendly name for the new SAveSync ROM folder: ')
                print(Subfolder)
                LocalPath = input('Please type out the path to the ROM folder to sync to: ')
                print(LocalPath)
                #We open teh config file, and append the new rom folder to the file
                ConfigFile = open(PathToConfig, "a")
                ConfigFile.write('ROMS:' + Subfolder + '=' + LocalPath)
                ConfigFile.close()
                print('Successfully added new ROM folder to config!')
                print('ROMs will be synced on next full or ROM Sync.')
                print('Please note you need to restart this program before performing a ROM sync to get the new folder interpreted correctly')
            #We set the new ROM folder as a root ROM folder if we didn't already have a ROM folder
            else:
                print('No Local ROM Folders Known!')
                ROMFolder = input('Please type the path to your ROM folder: ')
                print('Adding ROM Folder to local config...')
                ConfigFile = open(ConfigPath, "a")
                ConfigFile.write('ROMS=' + ROMFolder)
                ConfigFile.close()
                print('ROM Folder successfully added!')
                print('Please note you need to restart this program before performing a ROM sync to get the new folder interpreted correctly')
        #The user wants to sync their ROM folders
        elif response == '4':
            #We check for the existence of a ROM folder before proceeding
            if SyncRoms:
                #We handle it differently if more than one ROM folder is specified
                if len(RomPathList) > 1:
                    #Variable initialization
                    ServerSubFolders = []
                    RomRootFolder = ''
                    NonRootFolders = []
                    #We iterate through the list of ROM Paths
                    for RomFolder in RomPathList:
                            #We make sure subfolders are noted and added to a dedicated list for later
                            if RomFolder["Subfolder"]:
                                    ServerSubFolders.append(RomFolder["Tag"])
                                    NonRootFolders.append(RomFolder)
                            #We read in any other folder as a ROM root folder, where we sync any unspecified sub folders
                            else:
                                    RomRootFolder = RomFolder["Path"] 
                    #We call our sync ROM function on our root folder, excluding the noted subfolders
                    if RomRootFolder != '':
                        SyncRomFolder(RomRootFolder,"./ROMs/",ServerSubFolders, MaxSaves)
                    #We iterate through our list of subfolders and sync those to their specified paths as well
                    for folder in NonRootFolders:
                        if folder['Path'] != '':
                            SyncRomFolder(folder["Path"],"./ROMs/" + folder["Tag"],[], MaxSaves)
                #If there's only 1 ROM folder, we only need to call our SyncROMFolder function once
                elif len(RomPathList) == 1:
                    if RomPathList[0]['Path'] != '':
                        SyncRomFolder(RomPathList[0]['Path'], "./ROMs/", [], MaxSaves)
            #If they tried to sync their ROM folder but none were found, we display an error to the user letting them know they need to add a ROM folder before trying to sync ROMs 
            else:
                print('ERROR: No known ROM folders, to add one please add a line to your configuration in the format ROMS={path}.')
        #The user is syncing their non-Steam library
        elif response == '5':
            SyncNonSteamLibrary(ClientDictionary["ClientID"], ClientDictionary["SteamPath"], HomeDir, MaxSaves)
        #The user wants to sync a specific steam game
        elif response == '6':
            #We read in our list of installed steam games
            LocalSteamGames = SQLGetEntry('ClientSaveInfo', {'ClientID': ClientDictionary["ClientID"]}, [])
            LocalAppIDList = GameListReadAndPrint('AppID', LocalSteamGames)
            #We prompt the user for the AppID they want to sync
            ResponseAppID = input('Please select an entry by typing it\'s AppID: ')
            #Other variable initializations
            i = 0
            found = False
            AppListFlag = False
            #We make sure that we get a response we can interpret correctly before proceeding
            while not ResponseAppID.isnumeric() and ResponseAppID.lower() not in ['q', 'quit', 'exit'] and not AppListFlag:
                #We let the user know when an AppID isn't found in the local AppIDList
                if ResponseAppID != '':
                    print('ERROR: ' + ResponseAppID + ' is not a recognized selection.')
                    print('A locally installed App ID must be selected!')
                    print('If you are trying to sync a newly installed Steam Game, please use the sync all games feature instead.')
                #prompt the user for the appID they want to sync
                ResponseAppID = input('Please select an entry by typing it\'s AppID: ')
                #We make sure that the AppID is a number before trying to convert the data type to an integer
                if ResponseAppID.isnumeric():
                    #Then we check if the value is valid and exists in our locally installed games list
                    if int(ResponseAppID) in LocalAppIDList:
                        #Once it passes those checks, we know we have a valid AppID to sync
                        AppListFlag = True
            #We iterate though our steam libraries to find where the game is installed
            while (not found and i < len(LibList)) and (ResponseAppID.lower() not in [ 'q', 'quit', 'exit' ]):
                TempLibrary = LibList[i]
                #Once we find the library the game is installed to
                if ResponseAppID in LibraryVDFDict['libraryfolders'][TempLibrary]['apps']:
                    #We load in the path for the library we found where the game is installed
                    LibraryPath = LibraryVDFDict['libraryfolders'][TempLibrary]['path']
                    #We mark the game as found to prevent needlessly iterating through other libraries
                    found = True
                    print('Syncing game with AppID ' + ResponseAppID + '...')
                    #We sync the game we just located
                    SyncGame(ResponseAppID, ClientDictionary["SteamPath"], LibraryPath, ClientDictionary["ClientID"], IncludeSteamCloud, MaxSaves, HomeDir)
                    print('Finished syncing!')
                i += 1
            #We tell the user if there's an error and we weren't able to find the game we were looking for
            if not found and ResponseAppID.lower() not in [ 'q', 'quit', 'exit' ]:
                print("ERROR: Expected installed game not found in any Steam Library!")
                print("Please verify the game is locally installed in steam and try again.")
        #The user wants to sync a specific non-Steam gaem
        elif response == '7':
            #We get our list of non-Steam games that are known on this client
            LocalNonSteamGames = SQLGetEntry('NonSteamClientSaves', { 'ClientID': ClientDictionary["ClientID"] }, [])
            LocalGameIDList = []
            #If we have at least one known installed non-Steam game
            if len(LocalNonSteamGames) > 0:
                #We read in our list of game IDs that are installed and display them to the user
                GameIDList = GameListReadAndPrint('GameID', LocalNonSteamGames)
                #Variable initializiation
                ResponseGameID = ""
                ResponseGameIDFlag = False
                #We prompt the user until they give us a response we can interpret
                while ResponseGameID.lower() not in [ 'q', 'quit', 'exit' ] and not ResponseGameIDFlag:
                    #We let the user know if we couldn't interpret their response
                    #We exclude an empty string since that generally indicates that the user hasn't actually input anything
                    if ResponseGameID != "":
                        print("ERROR: No known saves for game: " + ResponseGameID)
                        print("Please enter a valid game ID or type q to quit.")
                    ResponseGameID = input('Please select an entry by typing it\'s GameID: ')
                    #Check to make sure it's a number before converting to an integer
                    if ResponseGameID.isnumeric():
                        #We check whether the response is in our list or not and exit the while loop if it is
                        if int(ResponseGameID) in GameIDList:
                            ResponseGameIDFlag = True
                #We check if the Response we got was numeric, since if it's not that means they were trying to exit
                if ResponseGameID.isnumeric():
                    #variable initialization
                    found = False
                    i = 0
                    #We iterate through our list of non-Steam games until we either find the one we're looking for or we run out of non-Steam games to check
                    while not found and i < len(LocalNonSteamGames):
                        #We pull the game's server save information from our database
                        ServerSaveInformation = SQLGetEntry('NonSteamApps', { 'GameID': ResponseGameID },[])[0]
                        #We mark it as found when the users response matches the non-Steam GameID we're trying to find
                        if LocalNonSteamGames[i]['GameID'] == int(ResponseGameID):
                            #Mark found to exit the loop
                            found = True
                            #And we sync the non-Steam game
                            print('Syncing Game with GameID ' + ResponseGameID + '...')
                            SyncNonSteamGame(ResponseGameID, LocalNonSteamGames[i]['LocalSavePath'], ServerSaveInformation['MostRecentSaveTime'], ClientDictionary['ClientID'], MaxSaves)
                            print('Finished Sync!')
                        else: 
                            i += 1
            #Let the user know if there are no known installed non-Steam games
            else:
                print('ERROR: No known installed non-Steam games.')
                print('If you are trying to detect a non-Steam game to sync located in ' + ClientDictionary['SteamPath'] + '/steamapps/compatdata/ please try a full sync')
                print('If a full sync does not detect the game you can add the game save with the helper function by typing 2 at the main menu or by using the --add command line argument.')
        #This is for manually updating a steam games entry
        elif response == '8':
            print('This function is for manually editing an entry for a Steam game.')
            print('1. I want to add or edit an entry for all synced clients.')
            print('2. I want to edit an entry just for this client.')
            #We prompt the user to find out if we're editing something for the local install, or we're editing something for all clients
            Selection = input('Please select an entry by the corresponding number (1-2):' )
            #Make sure we can interpret their response
            while Selection.lower() not in ['1', '2', 'q', 'quit', 'exit' ]:
                print('ERROR: please make a valid selection or type q to quit.')
                Selection = input('Please select an entry by the corresponding number (1-2): ')
            #This means we're editing information for all clients
            if Selection == '1':
                #We pull our Game List from our database
                SteamGameList = SQLGetEntry('SteamApps',{ }, [])
                #We get a list of AppIDs and print them to the end user
                AppIDList = GameListReadAndPrint('AppID', SteamGameList)
                Selection = input('Please type the AppID you wish to edit: ')
                #We check to make sure we can interpret the response
                while not Selection.isnumeric() and Selection.lower() not in ['q', 'quit', 'exit']:
                    print('ERROR: Expecting a number, please make a valid selection or type q to quit.')
                    Selection = input('Please type the AppID you wish to edit: ')
                #We make sure that the user isn't trying to quit
                if Selection.lower() not in ['q', 'quit', 'exit']:
                    #We read in teh AppID from their selection
                    AppID = Selection
                    #We try to find the relative save path and steam app entry for our AppID response
                    SteamAppEntry = SQLGetEntry('SteamApps', { 'AppID': AppID }, [])
                    PathEntry = SQLGetEntry('RelativeSavePaths', { 'AppID': AppID }, [])
                    #We display the information for the steam app if we found it
                    if len(SteamAppEntry) > 0:
                        print('Entry found for AppID: ' + Selection)
                        print('App ID: ' + str(SteamAppEntry[0]['AppID']))
                        print('1. Title: ' + SteamAppEntry[0]['Title'])
                        if SteamAppEntry[0]['AlwaysSkipped']:
                            print('2. Always Skipped: True')
                        else:
                                print('2. Always Skipped: False')
                        #We only display the relative path if one is found
                        if len(PathEntry) > 0:
                            print('3. Relative Save Path: ' + PathEntry[0]['RelativePath'])
                        else:
                            print('3. Relative Save Path: ')
                        Selection = input('Please select an entry you wish to edit by the corresponding number (1-3):')
                        #Let the user know if we can't interpret their response
                        while Selection.lower() not in ['1', '2', '3', 'q', 'quit', 'exit']:
                            print(Selection.lower())
                            print('ERROR: expecting a number between 1 and 3 or q to quit.')
                            Selection = input('Please select an entry you wish to edit by the corresponding number (1-3):')
                        #We want to edit the title in the database
                        if Selection == '1':
                            #We prompt the user for the new title and update it in the database
                            NewTitle = input('Please type the new title for this game: ')
                            if NewTitle.lower() not in [ 'q', 'quit', 'exit' ]:
                                SQLUpdateEntry('SteamApps', {'Title': NewTitle }, {'AppID': AppID })
                        #We change whether the game is skipped or not
                        elif Selection == '2':
                            if SteamAppEntry['AlwaysSkipped']:
                                SQLUpdateEntry('SteamApps', {'AlwaysSkipped': 0}, {'AppID': AppID })
                                print('Successfully set SteamApp to no longer skip on sync.')
                            else:
                                SQLUpdateEntry('SteamApps',{'AlwaysSkipped': 1}, {'AppID': AppID })
                                print('Successfully set SteamApp to never skip on sync.')
                        #We are editing the game's relative save path, or creating a new one
                        elif Selection == '3':
                            #We give the user information on how to specify a relative save path within the database
                            print('We are now going to update the relative save path of AppID: ' + AppID)
                            print('Indicate the game\'s install directory by typing { INSTALL PATH }')
                            print('Indicate the game\'s Proton Prefix by typing { PROTON PREFIX }')
                            print('Indicate the user\'s home directory by typing { HOME }')
                            #We prompt them for the save path
                            NewSavePath = input('Please type the new relative save path: ')
                            #We update or create the entry depending on if the AppID we're editing has a relative save path on file or not
                            if len(PathEntry) > 0 and NewSavePath.lower() not in [ 'q', 'quit', 'exit' ]:
                                SQLUpdateEntry('RelativeSavePaths', {'RelativePath': NewSavePath}, {'AppID': AppID})
                            elif NewSavePath.lower() not in [ 'q', 'quit', 'exit' ]:
                                SQLCreateEntry('RelativeSavePaths', {'AppID': AppID, 'RelativePath': NewSavePath })
                    #The AppID the user input isn't in the database
                    #We give them the option to create a new entry for the AppID
                    else:
                        print('No Entry Exists for AppID: ' + AppID)
                        AlwaysSkipped = 0
                        Selection = input ('Do you wish to create a new one? (y/n)')
                        #We make sure we can actually interpret their respoonse
                        while Selection.lower() not in ['yes', 'y', 'n', 'no', 'q', 'quit', 'exit']:
                            print('ERROR: please indicate whether to proceed by typing y or n, or type q to quit.') 
                            Selection = input ('Do you wish to create a new one? (y/n)')
                        #We only move on if the user confirmed they want to create a new entry
                        if Selection.lower() in ['yes', 'y']:
                            #Prompts for our new custom AppID values
                            print('We will now generate a new entry for this AppID.')
                            Title = input('Please type the title: ')
                            AlwaysSkippedStr = input('Do you wish to always skip this title when syncing? (y/n): ')
                            while AlwaysSkippedStr.lower() not in [ 'y', 'yes', 'n', 'no' ]:
                                print('invalid selection, please type yes or no to continue.')
                                AlwaysSkippedStr = input('Do you wish to always skip this title when syncing? (y/n): ')
                            if AlwaysSkippedStr.lower() in ['y','yes']:
                                AlwaysSkipped = 1
                            else:
                                AlwaysSkipped = 0
                            #We prompt the user for a relative save path
                            print('We are now going to create the relative save path of AppID: ' + AppID)
                            print('Indicate the game\'s install directory by typing { INSTALL PATH }')
                            print('Indicate the game\'s Proton Prefix by typing { PROTON PREFIX }')
                            print('Indicate the user\'s home directory by typing { HOME }')
                            NewSavePath = input('Please type the new relative save path: ')
                            #If they didn't intentionally quit, we proceed with creating the AppID's entry
                            if NewSavePath not in [ 'q', 'quit', 'exit' ]:
                                SQLCreateEntry('SteamApps', { 'AppID': AppID, 'Title': Title, 'AlwaysSkipped': AlwaysSkipped })
                                SQLCreateEntry('RelativeSavePaths', { 'AppID': AppID, 'RelativePath': NewSavePath })
            #We're editing the entry on just this client
            elif Selection == '2':
                #We pull our list of installed steam games, display them, and load the AppIDs into a list we can reference later
                LocalSteamGames = SQLGetEntry('ClientSaveInfo', {'ClientID': ClientDictionary["ClientID"] }, [])
                LocalAppIDList = GameListReadAndPrint('AppID',LocalSteamGames)
                ResponseAppID = input('Please select an entry by typing it\'s AppID: ')
                LocalGameFlag = False
                #We keep prompting the user until we get an AppID that we've already synced at least one save from or they quit
                while not ResponseAppID.isnumeric() and ResponseAppID.lower() not in [ 'q', 'quit', 'exit' ] and not LocalGameFlag:
                    print('ERROR: Steam game with App ID: ' + ResponseAppID + ' not detected, please make sure the game you wish to edit the entry for is installed on this client and you have at least one save synced.')
                    #We prompt the user for an AppID
                    RespnoseAppID = input('Please select an entry by typing it\'s AppID: ')
                    #We make sure they input a number before trying to convert to an integer
                    if ResponseAppID.isnumeric():
                        #We check the app ID list we created earlier to check whether the Game is in it, and only proceed if we can find it
                        if int(ResponseAppID) in LocalAppIDList or ResponseAppID in LocalAppIDList:
                            LocalGameFlag = True
                #We've now either found teh game or the user wants to quit.
                #If their response is a number, we can safely assume that it's an installed game 
                if ResponseAppID.isnumeric():
                    #Pulling the relevant local information for the AppID they selected
                    ClientSaveInfo = SQLGetEntry('ClientSaveInfo', { 'AppID': int(ResponseAppID), 'ClientID': ClientDictionary['ClientID'] }, [])
                    GamePrefixInfo = SQLGetEntry('ClientPrefixes', { 'AppID': int(ResponseAppID), 'ClientID': ClientDictionary['ClientID'] }, [])
                    GameSuffixInfo = SQLGetEntry('ClientSuffixes', { 'AppID': int(ResponseAppID), 'ClientID': ClientDictionary['ClientID'] }, [])
                    #If the game is marked as skipped, we assume that there is no Install Path or Proton Prefix in the database
                    if ClientSaveInfo[0]['Skipped']:
                        print('1. Skip on this client: True')
                        print('2. Install Path: ')
                        print('3. Proton Prefix: ')
                    #If it's not skipped, we must have the install path and proton prefix in the database
                    else:
                        print('1. Skip on this client: False')
                        print('2. Install Path: ' + ClientSaveInfo[0]['InstallPath'])
                        print('3. Proton Prefix: ' + ClientSaveInfo[0]['ProtonPrefix'])
                    #We print all the different prefixes
                    #NOTE there is a limit of one prefix per game, so this should always only ever display once
                    if len(GamePrefixInfo) > 0:
                        for prefix in GamePrefixInfo:
                            print('4. Save Prefix: ' + prefix['Prefix'])
                    else:
                        print('4. Save Prefix: ')
                    print('5. Edit Suffixes ')
                    #Getting the users response and making sure we can interpret it
                    Selection = input('Please select an entry with the corresponding number (1-5):')
                    while Selection.lower() not in ['1', '2', '3', '4', '5', 'q', 'quit', 'exit']:
                        print('ERROR: Invalid Selection, please type a valid selection or q to quit.')
                        Selection = input('Please select an entry with the corresponding number (1-5): ')
                    #They want to switch whether the game is skipped on this client or not
                    if Selection == '1':
                        #If the game is set to be skipped, we need to set it to no longer skip
                        if ClientSaveInfo[0]['Skipped']:
                            #Update the game to no longer be skipped on this client
                            SQLUpdateEntry('ClientSaveInfo', {'Skipped': 0 }, {'AppID': int(ResponseAppID), 'ClientID': int(ClientDictionary['ClientID'])})
                            print('Updated entry to no longer skip this game on this client.')
                            #We check whether the game was globally skipped as well
                            #If it was, we update it to no longer skip this game
                            if SQLGetEntry('SteamApps', {'AppID': int(ResponseAppID), 'ClientID': int(ClientDictionary['ClientID'])}, [])[0]['AlwaysSkipped']:
                                print('Updating to globally no longer skip this game...')
                                SQLUpdateEntry('SteamApps', { 'AlwaysSkipped': 0 }, {'AppID': int(ResponseAppID)})
                                print('Game will no longer be skipped on sync!')
                        #If the game isn't skipped, we can safely just update the value to skip on this client
                        else:
                            SQLUpdateEntry('ClientSaveInfo', {'Skipped': 1 }, {'AppID': int(ResponseAppID), 'ClientID': int(ClientDictionary['ClientID'])})
                            print('Updated entry to skip this game on this client')
                    #They want to change the game's install path
                    #NOTE I don't think this is really all that relevant since we don't really care too much where the game is installed, just where save data is located
                    elif Selection == '2':
                            #We prompt the user for the new install path, and then update the entry
                            NewInstallPath = input('Please type in the new install path: ')
                            if NewInstallPath.lower() not in [ 'q', 'quit', 'exit' ]:
                                print('Updating the install path...')
                                SQLUpdateEntry('ClientSaveInfo', { 'InstallPath': NewInstallPath }, { 'AppID': AppID, 'ClientID': ClientDictionary['ClientID']})
                                print('Install path successfully updated!')
                    #They want to edit the proton prefix path
                    elif Selection == '3':
                            #Read the user's input and update the database if they aren't trying to quit
                            NewProtonPrefix = input('Please type in the new proton prefix path: ')
                            if NewProtonPrefix.lower() not in [ 'q', 'quit', 'exit' ]:
                                print('Updating the proton prefix path...')
                                SQLUpdateEntry('ClientSaveInfo', { 'ProtonPrefix': NewProtonPrefix }, { 'AppID': AppID, 'ClientID': ClientDictionary['ClientID']})
                                print('proton prefix successfully updated!')
                    #They want to edit the save prefix to specify a new path
                    #NOTE calling them prefixes is probably kinda confusing, but the gist is that this is the filepath up until it splits into multiple directories, or if there's only one filepath that we're interpreting, then the full filepath to there
                    elif Selection == '4':
                            print('Save prefixes are used to distinguish between multiple profiles being saved, or if there is only one profile this is the full path to the save file or directory.')
                            print('Type out the path before where it splits into the user profile/saves, or type out the full path if you only have one path to sync.')
                            NewSavePrefix = input('Please type in the new save prefix: ')
                            #Make sure the user isn't trying to quit
                            if NewSavePrefix.lower() not in [ 'q', 'quit', 'exit' ]:
                                print('updating save prefix...')
                                SQLUpdateEntry('ClientPrefixes', { 'Prefix': NewSavePrefix }, { 'AppID': AppID, 'ClientID': ClientDictionary['ClientID'] })
                                print('Save prefix successfully updated!')
                    #They want to edit the save suffixes
                    elif Selection == '5':
                            print('Save Suffixes are used to distinguish between multiple profiles being used')
                            print('For most games this value will be empty unless multiple save matching save paths are found.')
                            print('Type out the path AFTER where it splits into user profiles/saves')
                            #We check whether a suffix even exists
                            if len(GameSuffixInfo) >  0:
                                #We print all the known suffixes for the game we're editing
                                for i in range (0, len(GameSuffixInfo)):
                                    print(str(i + 1) + ' ' + GameSuffixInfo[i]['Suffix'])
                                Selection = input('Please select an entry with the corresponding number you wish to edit (1-' + str(len(GameSuffixInfo))+ ') or type a to add a new entry: ')
                                #We check whether the selection is able to be interpreted correctly
                                ExitFlag = False
                                while Selection.lower() not in [ 'q', 'quit', 'exit', 'a' ] and not ExitFlag:
                                    print('ERROR: ' + Selection + ' is not a valid selection. Please select a number from the list above, type a to add a new entry, or type q to quit.')
                                    Selection = input('Please select an entry with the corresponding number you wish to edit (1-' + str(len(GameSuffixInfo)) + ' or type a to add a new entry: ')
                                    if Selection.isnumeric():
                                        if int(Selection) < len(GameSuffixInfo) + 1:
                                            ExitFlag = True
                                #We have a valid suffix we're editing
                                if Selection.isnumeric() and int(Selection) < len(GameSuffixInfo):
                                    print('Now editing suffix: ' + GameSuffixInfo[int(Selection)-1])
                                    #We need to save the old save suffix so we don't accidentally write to every save suffix for this game
                                    OldSaveSuffix = GameSuffixInfo[int(Selection)-1] 
                                    #Prompt the user for the new save suffix and update the entry accordingly so long as they aren't trying to quit
                                    NewSaveSuffix = input('Please type in the new save suffix: ')
                                    if NewSaveSuffix.lower() not in [ 'q', 'quit', 'exit' ]:
                                        SQLUpdateEntry('ClientSuffixes', {'Suffix': NewSaveSuffix}, { 'AppID': AppID, 'ClientID': ClientDictionary['ClientID'], 'Suffix': OldSaveSuffix })
                                        print('Successfully updated suffix')
                                #We're adding a new save suffix
                                elif Selection == 'a':
                                    #We prompt the user for the new save suffix
                                    NewSaveSuffix = input('Please type in the new save suffix: ')
                                    #We make sure the user isn't trying to exit, then create the new entry
                                    if NewSaveSuffix.lower() not in [ 'q', 'quit', 'exit' ]:
                                        print('Creating new save suffix ' + NewSaveSuffix + '...')
                                        SQLCreateEntry('ClientSuffixes', {'Suffix': NewSaveSuffix, 'AppID': AppID, 'ClientID': ClientDictionary['ClientID']})
                                        print('Save suffix successfully created')
                            #We have no save suffixes on file, so we know we're creating a new one
                            else:
                                #Prompt the user for the new save suffix, and create it so long as they aren't trying to quit the program.
                                NewSaveSuffix = input('Please type in the new save suffix: ')
                                if NewSaveSuffix.lower() not in ['q', 'quit', 'exit']:
                                    print('Creating new save suffix ' + NewSaveSuffix + '...')
                                    SQLCreateEntry('ClientSuffixes', {'Suffix': NewSaveSuffix, 'AppID': AppID, 'ClientID': ClientDictionary['ClientID']})
                                    print('Save suffix successfully created')
        #The user wants to edit an entry for a non-Steam game
        elif response == '9':
            print('This function is for manually editing entries non-Steam games')
            print('1. I want to edit an entry for all synced clients')
            print('2. I want to edit an entry just for this client')
            #We prompt the user with our valid options and keep them respondidng until we get something we can interpret
            Selection = input('Please select an entry by the corresponding number (1-2): ')
            while Selection.lower() not in [ '1', '2', 'q', 'quit', 'exit' ]:
                print('ERROR: please make a valid selection or type q to quit.')
                Selection = input('Please select an entry by the corresponding number (1-2): ')
            #The user wants to edit an entry for all clients
            if Selection == '1':
                #We pull our list of Non-Steam games
                NonSteamGames = SQLGetEntry('NonSteamApps', { }, [])
                #We make sure there's at least one Non-Steam game in the database
                if len(NonSteamGames) > 0:
                    #We get our valid GameIDs and print them to the user
                    GameIDList = GameListReadAndPrint('GameID', NonSteamGames)
                    #Variable initialization
                    IDFlag = False
                    ResponseFlag = False
                    ResponseGameID = ""
                    #We need to make sure the user inputs an option we can interpret
                    while not ResponseFlag and ResponseGameID.lower() not in [ 'q', 'quit', 'exit' ]:
                        if ResponseGameID != "":
                            print('ERROR: selected Game ID not in known non-steam games.')
                        ResponseGameID = input('Please select an entry with it\'s GameID: ')
                        if ResponseGameID.isnumeric():
                            if int(ResponseGameID) in GameIDList:
                                ResponseFlag = True
                    #If we got here and the GameID is a number, we know it was a valid Game ID choice from our while loop above
                    if ResponseGameID.isnumeric():
                        #We pull the global entry for the requested game ID
                        NonSteamGameSQLEntry = SQLGetEntry('NonSteamApps', { 'GameID': ResponseGameID }, [])[0]
                        print('1. Title: ' + NonSteamGameSQLEntry['Title'])
                        print('2. Relative Save Path: ' + NonSteamGameSQLEntry['RelativeSavePath'])
                        Selection = ''
                        #We make sure we get a response we can interpret
                        while Selection.lower() not in ['1', '2', 'q', 'quit', 'exit']:
                            if Selection != '':
                                print('ERROR: invalid selection. Please make a choice from the list above or type q to quit.')
                            Selection = input('Please indicate which field you\'d like to edit by the number on the corresponding line: ')
                        #The user wants to edit the title of the game
                        if Selection == '1':
                            #Prompt the user for the updated title and update the database with the new title.
                            NewTitle = input('Please input your new title: ')
                            SQLUpdateEntry('NonSteamApps', { 'Title': NewTitle }, { 'GameID': ResponseGameID })
                        #The user wants to edit the game's relative save path
                        elif Selection == '2':
                            #We let the user know how to indicate certain generic paths
                            print('You can indicate a game\'s wineprefix by typing { WINE PREFIX }')
                            print('You can indicate the user\'s home folder by typing { HOME }')
                            #We get the new path from the users input
                            NewRelativePath = input('Please type the new relative save path: ')
                            #We make sure the user isn't trying to exit before writing the new relative path to the database
                            if NewRelativePath.lower() not in [ 'q', 'quit', 'exit' ]:
                                SQLUpdateEntry('NonSteamApps', { 'RelativeSavePath': NewRelativePath }, { 'GameID': ResponseGameID })
                #We kick the user to the non-Steam game helper function if no steam games were found
                else:
                    print('No non-Steam games detected, creating a new one...')
                    print('If you do not intend to create a new non-Steam Entry, type q to quit.')
                    NonSteamEntryHelperFunction(PathToSteam, ClientDictionary['ClientID'], ClientDictionary['HomeDir'])
            #The user wants to edit an entry just for this client
            elif Selection == '2':
                #We get a list of our known, locally installed non-Steam games
                LocalNonSteamGames = SQLGetEntry('NonSteamClientSaves', { 'ClientID': ClientDictionary['ClientID'] }, [])
                #We make sure there is at least one non-Steam game detected
                if len(LocalNonSteamGames) > 0:
                    #We read our valid game ID selections into a dedicated list, and print valid options to the end user
                    GameIDList = GameListReadAndPrint('GameID', LocalNonSteamGames)
                    #Variable initialization
                    ResponseGameID = ""
                    ResponseFlag = False
                    #We make sure we can interpret the user's response before moving forward
                    while not ResponseFlag and ResponseGameID.lower() not in [ 'q', 'quit', 'exit' ]:
                        if ResponseGameID != "":
                            print('ERROR: GameID not in list of installed games.')
                            print('Please use the add a non-Steam game function if you need to manually specify a savepath for a locally installed non-Steam game.')
                            print('You may quit this program by typing q.')
                        ResponseGameID = input('Please select an entry with it\'s GameID: ')
                        if ResponseGameID.isnumeric():
                            if int(ResponseGameID) in GameIDList:
                                ResponseFlag = True
                    #We know that if it's a number, its a valid game id selection since that's a requirement to get out of the previous while loop
                    if ResponseGameID.isnumeric():
                        #We Pull the game's SQL data, and let the user know that the only thing they can edit for this specific client is the local save path
                        GameSaveSQLEntry = SQLGetEntry('NonSteamClientSaves', { 'ClientID': ClientDictionary['ClientID'], 'GameID': ResponseGameID }, [])[0]
                        print('Local Path: ' + GameSaveSQLEntry['LocalSavePath'])
                        print('The only editable entry for this selection is the Local Save Path.')
                        #Prompt the user for the new save path
                        NewPath = input('Please type the new save path for this game: ')
                        #Make sure the user isn't trying to quit before pushing the change to the save path
                        if NewPath.lower() not in [ 'q', 'quit', 'exit' ]:
                            SQLUpdateEntry('NonSteamClientSaves', { 'LocalSavePath': NewPath }, { 'ClientID': ClientDictionary['ClientID'], 'GameID': ResponseGameID })
                #We kick the user over to the non-Steam helper function if we didn't find any locally installed non-Steam games
                else:
                    print('No locally installed non-Steam games found...')
                    print('Adding new entry for local non-Steam game...')
                    NonSteamEntryHelperFunction(PathToSteam, ClientDictionary['ClientID'], ClientDictionary['HomeDir'])
        #the user wants to delete a steam game's entry from the database
        elif response == '10':
            #We prompt the user asking whether they want to delete the entry globally or if they only want to delete it for this client
            #Also display a warning to make sure they understand that they are deleting information in the database about the game they select
            print('WARNING: This function is to delete an entry for a steam game within the SaveSync Database.')
            print('This process is irreversible in it\'s impact on the database, but your save data will continue to be stored by SaveSync unless manually deleted.')
            print('1. Delete entry for ALL clients')
            print('2. Delete entry for this client.')
            Selection = ''
            #We make sure we get a response we can interpret
            while Selection.lower() not in [ '1', '2', 'q', 'quit', 'exit' ]:
                if Selection != '':
                    print('ERROR: ' + Selection + ' is not a recognized selection. Please make a valid choice from the list above or type q to quit.')
                Selection = input('Please indicate an option: ')
            #We are deleting a game for every client
            if Selection == '1':
                #Display an extra warning before deleting anything
                print('WARNING: this will delete ALL database entries related to the indicated AppID')
                print('If you do not wish to proceed, type q to quit.')
                #Get our list of steam apps, as well as a list of valid AppID selections, and display them to the user
                SteamApps = SQLGetEntry('SteamApps', {}, [])
                AppIDList = GameListReadAndPrint('AppID', SteamApps)
                #Variable initialization
                Selection = ''
                AppIDFlag = False
                #We make sure we can interpret the user's selection before moving on
                while not Selection.isnumeric() and Selection.lower() not in [ 'q', 'quit', 'exit' ] and not AppIDFlag:
                    if Selection != '':
                        print('ERROR: ' + Selection + 'is not a recognized selection. Please type a valid AppID or type q to quit.')
                    Selection = input('Please type the AppID of the game you wish to delete, or type q to quit: ')
                    if Selection.isnumeric():
                        if int(Selection) in AppIDList:
                            AppIDFlag = True
                #If we got here we know it's a valid AppID or they were trying to quit the program.
                if Selection.lower() not in [ 'q', 'quit', 'exit' ]:
                    #Delete the relevant entries from each table
                    SQLDeleteEntry('SteamApps', { 'AppID': Selection })
                    SQLDeleteEntry('ClientSaveInfo', { 'AppID': Selection })
                    SQLDeleteEntry('ClientPrefixes', { 'AppID': Selection })
                    SQLDeleteEntry('ClientSuffixes', { 'AppID': Selection })
                    SQLDeleteEntry('SaveTimestamps', {'AppID': Selection })
                    SQLDeleteEntry('RelativeSavePaths', {'AppID': Selection})
                    print('Entries deleted from tables.')
            #We are deleting an entry just for this client
            elif Selection == '2':
                #Display an extra warning to the user, can never be too careful
                print('WARNING: This will delete ALL database entries for the selected AppID related to this client.')
                print('If you do not wish to proceed, type q to quit.')
                #We get our list of valid AppIDs as well as displaying them to the end user
                SteamApps = SQLGetEntry('ClientSaveInfo', { 'ClientID': ClientDictionary['ClientID'] }, [])
                AppIDList = GameListReadAndPrint('AppID', SteamApps)
                #Variable Initialization
                Selection = ''
                LocalInstallFlag = False
                AppIDFlag = False
                #We make sure we get a response we can interpret before moving on
                while not Selection.isnumeric() and Selection.lower() not in ['q', 'quit', 'exit' ] and not AppIDFlag:
                    if Selection != '':
                        print('ERROR: ' + Selection + ' is not a recognized selection. Please type a valid AppID or type q to quit.')
                    Selection = input('Please type the AppID of the game you wish to delete for this client, or type q to quit: ')
                    if Selection.isnumeric():
                        if int(Selection) in AppIDList:
                            AppIDFlag = True
                #If we made it here and aren't trying to quit, it means we have a valid AppID selected
                if Selection.lower() not in [ 'q', 'quit', 'exit' ]:
                    #We delete the relevant entries from the database
                    SQLDeleteEntry('ClientSaveInfo', { 'AppID': Selection, 'ClientID': ClientDictionary['ClientID'] })
                    SQLDeleteEntry('ClientPrefixes', { 'AppID': Selection, 'ClientID': ClientDictionary['ClientID'] })
                    SQLDeleteEntry('ClientSuffixes', { 'AppID': Selection, 'ClientID': ClientDictionary['ClientID'] })
        #The user wants to delete a non-Steam game entry
        elif response == '11':
            #Display a warning to make sure they understand what they're doing, and ask whether they want to delete from the database entirely or if they only care about deleting the entry related to this client
            print('WARNING: This function is to delete an entry for a non-Steam game within the SaveSync Database.')
            print('This process is irreversible in it\'s impact on the database, but your save data will continue to be stored unless manually deleted.')
            print('1. Delete entry for ALL clients')
            print('2. Delete entry for this client.')
            Selection = ''
            #We make sure we get a response we can interpret
            while Selection.lower() not in [ '1', '2', 'q', 'quit', 'exit' ]:
                if Selection != '':
                    print('ERROR: ' + Selection + ' is not a recognized selection. Please make a valid choice from the list above or type q to quit.')
                Selection = input('Please indicate an option: ')
            #They want to delete all references to the game in the database
            if Selection == '1':
                #Display an extra warning to make sure they know the impact of what they're doing
                print('WARNING: this will delete ALL database entries related to the indicated GameID')
                print('If you do not wish to proceed, type q to quit.')
                print('Listing all non-steam games...')
                #We get a list of non-Steam games and valid GameIDs from the database, as well as displaying them to the user
                NonSteamGames = SQLGetEntry('NonSteamApps', {})
                GameIDList = GameListReadAndPrint('GameID',NonSteamGames)
                #Variable intiailization
                GameIDFlag = False
                ResponseGameID = ""
                #We make sure we get a response we can actually interpret before moving forward
                while not ResponseGameID.isnumeric() and ResponseGameID.lower() not in [ 'q', 'quit', 'exit' ] and not GameIDFlag:
                    if ResponseGameID != "":
                        print('ERROR: selected Game ID not in known non-steam games.')
                    ResponseGameID = input('Please select an entry with it\'s GameID: ')
                    if ResponseGameID.isnumeric():
                        if int(ResponseGameID) in GameIDList:
                            GameIDFlag = True
                #As long as the user isn't trying to quit, the only way out of the previous for loop was by making a valid GameID selection
                if ResponseGameID.lower() not in [ 'q', 'quit', 'exit' ]: 
                    #Delete all the relevant database entries
                    SQLDeleteEntry('NonSteamApps', { 'GameID': int(ResponseGameID) })
                    SQLDeleteEntry('NonSteamClientSaves', { 'GameID': int(ResponseGameID) })
                    SQLDeleteEntry('NonSteamSaveTimestamps', { 'GameID': int(ResponseGameID) })
                    print('Entries deleted from tables.')
            #They want to delete information on the game specific to this client
            elif Selection == '2':
                #Display an extra warning, making sure the user understands what they're doing
                print('WARNING: This will delete ALL database entries for the selected AppID related to this client.')
                print('This will NOT delete universal database entries or remove saves from the server.')
                print('If you do not wish to proceed, type q to quit.')
                #Variable initializations, getting our list of valid GameID selections, and any other extra information we might need from the database
                Selection = ''
                LocalNonSteamGames = SQLGetEntry('NonSteamClientSaves', { 'ClientID': ClientDictionary['ClientID'] }, [])
                GameIDList = GameListReadAndPrint('GameID', LocalNonSteamGames)
                ResponseGameID = ""
                GameIDFlag = False
                #We make sure we can interpret the user's response
                while not ResponseGameID.isnumeric() and ResponseGameID.lower() not in [ 'q', 'quit', 'exit' ] and not GameIDFlag:
                    if ResponseGameID != "":
                        print('ERROR: selected Game ID not in known installed non-steam games.')
                    ResponseGameID = input('Please select an entry with it\'s GameID: ')
                    if ResponseGameID.isnumeric():
                        if int(ResponseGameID) in GameIDList:
                            GameIDFlag = True
                #So long as they aren't trying to quit, we now know that the user made a valid GameID selection
                if Selection.lower() not in [ 'q', 'quit', 'exit' ]:
                    #Delete the relevant entry from the database
                    SQLDeleteEntry('NonSteamClientSaves', { 'GameID': ResponseGameID, 'ClientID': ClientDictionary['ClientID'] })
                    print('Entries deleted from tables.')
        #The user wants to 
        elif response == '12':
            #Display a warning to the user and prompt them to determine whether they want to rollback a steam save or a non-Steam save
            print('WARNING: This will overwrite your local save files. Make sure you don\'t unintentionally overwrite unsynced data by using this function.')
            print('ROM Save rollback (e.g. .sav files) is not currently supported')
            print('If you wish to exit from this menu, type q')
            print('1. I want to rollback or restore a Steam save')
            print('2. I want to rollback or restore a non-Steam save')
            print('3. I want to rollback or restore a ROM Save')
            #We initialize a variable to hold the users response and we make sure that we can interpret that response before moving forward
            Selection = ''
            while Selection.lower() not in [ '1', '2','3', 'q', 'quit', 'exit' ]:
                if Selection != '':
                    print('ERROR: ' + Selection  + ' is not a recognized selection. Please make a valid choice from this list or type q to quit.')
                Selection = input('Please select a function from the list above (1-2): ')
            #The user wants to rollback a steam game save
            if Selection == '1':
                #Let the user know what's happening, get a list of valid AppID's to choose from, and printing the list of AppIDs to the user
                print('Ok! We will roll back a Steam game save.')
                print('Listing Non-skipped Games in database...')
                KnownSteamGames = SQLGetEntry('SteamApps', { 'AlwaysSkipped':0 }, [])
                AppIDList = GameListReadAndPrint('AppID', KnownSteamGames)
                #Variable initialization
                AppIDResponse = ''
                AppIDFlag = False
                #We make sure we get a response we can actually interpret
                while not AppIDResponse.isnumeric() and AppIDResponse.lower() not in [ 'q', 'quit', 'exit' ] and not AppIDFlag:
                    if AppIDResponse != '':
                        print('ERROR: ' + AppIDResponse + ' is not a recognized selection, please make a valid choice from the AppID list above or type q to quit.')
                    AppIDResponse = input('Please Select a game with it\'s AppID: ')
                    if AppIDResponse.isnumeric():
                        if int(AppIDResponse) in AppIDList:
                            AppIDFlag = True
                #We only proceed if the user isn't trying to quit
                if AppIDResponse not in [ 'q', 'quit', 'exit']:
                    #We give the User a list of valid save timestamps that the database has on record
                    print('Attempting to find valid save timestamps for AppID: ' + AppIDResponse)
                    SaveTimestamps = SQLGetEntry('SaveTimestamps', { 'AppID': int(AppIDResponse) })
                    #We need to keep track of how many saves we have, so that we can know which are valid and which aren't
                    NumSaves = 0
                    #We print the various save timestamps to the user
                    for i in range(0,len(SaveTimestamps)):
                        NumSaves += 1
                        print(str(i + 1) + '. ' + datetime.datetime.fromtimestamp(SaveTimestamps[i]['Timestamp']).strftime('%Y-%m-%d_%H%M%S'))
                    #We initialize a variable to hold the user's response
                    Selection = '' 
                    #We get the current time to use as a new timestamp
                    NewTimestamp = datetime.datetime.now()
                    SelectionFlag = False
                    #We make sure that the user is making a valid selection
                    while not Selection.isnumeric() and Selection.lower() not in [ 'q', 'quit', 'exit' ] and not SelectionFlag:
                        if Selection != '':
                            print('ERROR: ' + Selection + ' is not a recognized selection. Please make a valid choice from the timestamp list above or type q to quit.')
                        Selection = input('Please make a selection from the list above by typing the numebr next to the timestamp you wish to roll back to: ')
                        #We make sure that the user's response is a number before trying to convert it to an integer
                        if Selection.isnumeric():
                            if int(Selection) <= MaxSaves:
                                SelectionFlag = True
                    #We make sure the user isn't trying to quit
                    if Selection.lower() not in [ 'q', 'quit', 'exit' ]:
                        #We let the user know the timestamp they selected
                        print('Restoring Save with timestamp: ' + datetime.datetime.fromtimestamp(SaveTimestamps[int(Selection)-1]['Timestamp']).strftime('%Y-%m-%d_%H%M%S'))
                        #We get our needed SQL information
                        PrefixEntry = SQLGetEntry('ClientPrefixes',{ 'AppID': int(AppIDResponse), 'ClientID': ClientDictionary['ClientID']})[0]
                        Suffixes = SQLGetEntry('ClientSuffixes',{ 'AppID': int(AppIDResponse), 'ClientID': ClientDictionary['ClientID']})
                        ClientSaveInfo = SQLGetEntry('ClientSaveInfo', {'AppID': int(AppIDResponse), 'ClientID': ClientDictionary['ClientID']})
                        #We initialize a variable to hold our suffixes
                        FormattedSuffixList = []
                        for suffix in Suffixes:
                            FormattedSuffixList.append(suffix['Suffix'])
                        #Extra data sanitation check, shouldn't be necessary but I added it so it probably was relevant at one point and I'd rather not risk breaking something by mistake
                        if FormattedSuffixList == '':
                            FormattedSuffixList = ['']
                        #We make sure that there is an entry related to this client for this game before proceeding
                        #We don't want to rollback a save if there's no game to rollback to. Technically it shouldn't matter, but for peace of mind to potentially avoid weird cross communication when rolling back a game without updating a local save.
                        if PrefixEntry:
                            #We check how many saves we're allowed to have
                            MaxSaves = SQLGetEntry('GlobalVars', {'Key': 'MaxSaves'})[0]['Value']
                            #We update our tables with the new save timestamp
                            SQLUpdateEntry('SteamApps', { 'MostRecentSaveTime': SaveTimestamps[int(Selection)-1]['Timestamp'] },{ 'AppID': int(AppIDResponse) })
                            SQLCreateEntry('SaveTimestamps', { 'AppID': int(AppIDResponse), 'Timestamp': datetime.datetime.timestamp(NewTimestamp)})
                            SQLDeleteEntry('SaveTimestamps', { 'AppID': int(AppIDResponse), 'Timestamp': SaveTimestamps[int(Selection)-1]['Timestamp'] })
                            SQLUpdateEntry('ClientSaveInfo', { 'MostRecentSaveTime': datetime.datetime.timestamp(NewTimestamp) },{ 'AppID': int(AppIDResponse), 'ClientID': ClientDictionary['ClientID'] })
                            #We copy the save from the server to the client
                            CopySaveFromServer({ 'AppID': AppIDResponse, 'Timestamp': SaveTimestamps[int(Selection)-1]['Timestamp'], 'Prefix':PrefixEntry['Prefix'], 'Suffixes': FormattedSuffixList, 'ProtonPath': ClientSaveInfo[0]['ProtonPrefix'], 'InstallDir': ClientSaveInfo[0]['InstallPath'], 'SteamPath': ClientDictionary['SteamPath'], 'Home': HomeDir})
                            #Then we copy the save back to the server with the new save timestamp
                            CopySaveToServer({ 'AppID': AppIDResponse, 'Timestamp': datetime.datetime.timestamp(NewTimestamp), 'Prefix':PrefixEntry['Prefix'], 'Suffixes': FormattedSuffixList, 'ProtonPath': ClientSaveInfo[0]['ProtonPrefix'], 'InstallDir': ClientSaveInfo[0]['InstallPath'], 'SteamPath': ClientDictionary['SteamPath'], 'Home': HomeDir}, int(MaxSaves))
                            TimeObj = datetime.datetime.fromtimestamp(SaveTimestamps[int(Selection)-1]['Timestamp'])
                            shutil.rmtree('./Backups/' + AppIDResponse + '/' + TimeObj.strftime('%Y-%m-%d_%H%M%S'))
                        #We let the user know if they selected a game that wasn't installed on this client
                        else:
                            print('ERROR: Save restoration is only supported on machines with the selected GameID installed. Your Selection does not appear to be installed on this client.')
                            print('If this is incorrect, run a full sync to see if the local save data can be recognized.')
                            print('If this client is still unable to locate your save, you may need to manually add or edit it\'s entry using one of the other options in this program.')
                            print('Or this program may just be broken right now :(')
            #The user wants to rollback a non-Steam game's save
            elif Selection == '2':
                #We let the user know what we're doing, read in a list of valid GameID selections, and list all valid gameIDs to the user
                print('Ok! We will roll back a non-Steam game save.')
                print('Listing Non-Steam Games in database...')
                KnownNonSteamGames = SQLGetEntry('NonSteamApps', {}, [])
                GameIDList = GameListReadAndPrint('GameID', KnownNonSteamGames)
                #Variable initialization
                GameIDResponse = ''
                GameIDFlag = False
                #We make sure we get a response we can interpret before moving forward
                while not GameIDResponse.isnumeric() and GameIDResponse.lower() not in [ 'q', 'quit', 'exit' ] and not GameIDFlag:
                    if GameIDResponse != '':
                        print('ERROR: ' + GameIDResponse + ' is not a recognized selection, please make a valid choice from the AppID list above or type q to quit.')
                    GameIDResponse = input('Please select a game with it\'s gameID above: ')
                    #We need to make sure that the user's response is a number before attempting to convert it to an integer
                    if GameIDResponse.isnumeric():
                        if int(GameIDResponse) in GameIDList:
                            GameIDFlag = True
                #We make sure the user wasn't trying to quit
                if GameIDResponse.lower() not in [ 'q', 'quit', 'exit' ]:
                    #We get all of our save timestamps from the server
                    print('Attempting to find valid save timestamps for GameID: ' + GameIDResponse)
                    SaveTimestamps = SQLGetEntry('NonSteamSaveTimestamps', { 'GameID': int(GameIDResponse) })
                    #We initialize a variable to keep track of how many selections they could choose from
                    NumSaves = 0
                    #We print each valid save timestamp to the user
                    for i in range(0,len(SaveTimestamps)):
                        NumSaves += 1
                        print(str(i+1) + '. ' + datetime.datetime.fromtimestamp(SaveTimestamps[i]['Timestamp']).strftime('%Y-%m-%d_%H%M%S'))
                    #We initialize variables for interpreting the user's response
                    Selection = '' 
                    SelectionFlag = False
                    #We need to get our new timestamp for the save to overwrite the previous one
                    NewTimestamp = datetime.datetime.now()
                    #We make sure we can interpret the user's response before moving forward
                    while Selection.lower() not in [ 'q', 'quit', 'exit' ] and not SelectionFlag:
                        if Selection != '':
                            print('ERROR: ' + Selection + ' is not a recognized selection. Please make a valid choice from the timestamp list above or type q to quit.')
                        Selection = input('Please make a selection from the list above by typing the number next to the timestamp you wish to roll back to: ')
                        #We make sure that the user's response is a number before converting it to an integer
                        if Selection.isnumeric():
                            if int(Selection) <= NumSaves:
                                SelectionFlag = True
                    #We make sure the user isn't trying to quit
                    if Selection.lower() not in [ 'q', 'quit', 'exit' ]:
                        #We print the selected timestamps information to the user
                        print('Restoring Save from timestamp: ' + datetime.datetime.fromtimestamp(SaveTimestamps[int(Selection)-1]['Timestamp']).strftime('%Y-%m-%d_%H%M%S'))
                        #We pull the relevant information on the game that is specific to our client
                        ClientSaveInfo = SQLGetEntry('NonSteamClientSaves', {'GameID': GameIDResponse, 'ClientID':ClientDictionary['ClientID']})
                        #We make sure that the game is locally installed before proceeding
                        if ClientSaveInfo:
                            #We get the filepaths to the save we're backing up from, as well as the new directory we're going to be writing to with our new timestamp
                            OldDirectory = "./NonSteamSaves" + "/" + GameIDResponse + "/" + datetime.datetime.fromtimestamp(SaveTimestamps[int(Selection)-1]['Timestamp']).strftime('%Y-%m-%d_%H%M%S')
                            NewDirectory = "./NonSteamSaves" + "/" + GameIDResponse + "/" + datetime.datetime.fromtimestamp(datetime.datetime.timestamp(NewTimestamp)).strftime('%Y-%m-%d_%H%M%S')
                            #We make the new directory we're copying the save into
                            os.makedirs(NewDirectory,exist_ok=True)
                            #We copy the save into the new directory
                            NumericTimestamp = datetime.datetime.timestamp(NewTimestamp)
                            SQLCreateEntry('NonSteamSaveTimestamps', { 'GameID': int(GameIDResponse), 'Timestamp': NumericTimestamp }) 
                            shutil.copytree(OldDirectory,NewDirectory, dirs_exist_ok=True)
                            shutil.rmtree(OldDirectory)
                            SQLDeleteEntry('NonSteamSaveTimestamps', { 'GameID': int(GameIDResponse), 'Timestamp': SaveTimestamps[int(Selection)-1]['Timestamp']})
                            #We update the database with the new save timestamp
                            SQLUpdateEntry('NonSteamApps',{ 'MostRecentSaveTime': datetime.datetime.timestamp(NewTimestamp) }, { 'GameID': int(GameIDResponse)})
                            #We call our sync function, which should overwrite the local save since the timestamp on the server is based on the current date/time
                            RelativePath = SQLGetEntry('NonSteamApps', {'GameID': int(GameIDResponse) })[0]['RelativeSavePath']
                            TempSplit = RelativePath.split('/')
                            UIDFolderFlag = False
                            if len(TempSplit) > 1:
                                if TempSplit[-1] != '':
                                    if '{ UID }' in TempSplit[-1]:
                                        UIDFolderFlag = True
                                    elif '{ UID }' in TempSplit[-2]:
                                        UIDFolderFlag = True
                                SyncNonSteamGame(int(GameIDResponse), ClientSaveInfo[0]['LocalSavePath'], datetime.datetime.timestamp(NewTimestamp), ClientDictionary['ClientID'], MaxSaves, UIDFolderFlag)

                        #We let the user know that rollback is only supported on games that are known to be locally installed
                        #This may not be 100% necessary and may still work even if the game isn't installed locally, but we want to avoid potential issues with cross communication with a client that does have the game installed locally.
                        else:
                            print('ERROR: Save restoration is only supported on machines with the selected GameID installed. Your Selection does not appear to be installed on this client.')
                            print('If this is incorrect, run a full sync to see if the local save data can be recognized.')
                            print('If this client is still unable to locate your save, you may need to manually add or edit it\'s entry using one of the other options in this program.')
                            print('Or this program may also just be broken right now :(')
            elif Selection == '3':
                print('OK! We will roll back a ROM Save.')
                print('Listing ROM Saves in database...')
                ROMSaveList = SQLGetEntry('ROMSaves', {})
                FilenameList = []
                ContinueFlag = False
                ROMSaveFilename = ''
                SubFolder = ''
                SelectedROMSave = ''
                for entry in ROMSaveList:
                    FilenameList.append(entry['FileName'])
                for i in range(0,len(FilenameList)):
                    print(str(i+1) + '. ' + FilenameList[i])
                while not ContinueFlag and SelectedROMSave.lower() not in [ 'q', 'quit', 'exit' ]:
                    if SelectedROMSave != '':
                        print('ERROR: ' + SelectedROMSave + ' is not a recognized selection. Please make a valid selection from the list above.')
                    SelectedROMSave = input('Please select an entry from the list above by typing the corresponding number: ')
                    if SelectedROMSave.isnumeric():
                        if int(SelectedROMSave) < len(ROMSaveList) + 1:
                            ContinueFlag = True
                            SubFolder = ROMSaveList[int(SelectedROMSave)-1]['SubFolder']
                if ContinueFlag:
                    ValidSelectionFlag = False
                    OldTimestamp = 0
                    ROMSaveFilename = FilenameList[int(SelectedROMSave) - 1]
                    print('Attempting to find valid timestamps for ROM ' + ROMSaveFilename + '...')
                    ROMSaveTimestamps = SQLGetEntry('ROMSaveTimestamps', { 'FileName': ROMSaveFilename })
                    for j in range(0,len(ROMSaveTimestamps)):
                        print(str(j+1) + '. ' + datetime.datetime.fromtimestamp(ROMSaveTimestamps[j]['Timestamp']).strftime('%Y-%m-%d_%H%M%S'))
                    SelectedTimestamp = ''
                    while not ValidSelectionFlag and SelectedTimestamp.lower() not in [ 'q', 'quit', 'exit' ]:
                        if SelectedTimestamp != '':
                            print('ERROR: ' + SelectedTimestamp + ' is not a recognized selection. Please make a valid selection from the list above.')
                        SelectedTimestamp = input('Please select a timestamp above by typing the corresponding number: ')
                        if SelectedTimestamp.isnumeric():
                            if int(SelectedTimestamp) < len(ROMSaveTimestamps) + 1:
                                ValidSelectionFlag = True
                    RootPath = ''
                    SavePath = ''
                    NewTimestamp = datetime.datetime.now()
                    if ValidSelectionFlag: 
                        print('Restoring Save from timestamp: ' + datetime.datetime.fromtimestamp(ROMSaveTimestamps[int(SelectedTimestamp)-1]['Timestamp']).strftime('%Y-%m-%d_%H%M%S'))
                        for rompath in RomPathList:
                            print(rompath['Path'] + '/' + SubFolder + '/')
                            if os.path.isfile(rompath['Path'] + '/' + SubFolder + '/' + ROMSaveFilename): 
                                SavePath = rompath['Path'] + '/' + SubFolder
                            elif os.path.isfile(rompath['Path'] + '/' + ROMSaveFilename):
                                SavePath = rompath['Path']
                        if SavePath == '' and RootPath != '':
                            SavePath = RootPath + '/' + SubFolder + '/'
                        if os.path.isfile(SavePath + ROMSaveFilename) and SavePath != '':
                            os.remove(SavePath + ROMSaveFilename)
                        if os.path.isfile('./ROMs/' + SubFolder + '/' + ROMSaveFilename):
                            os.remove('./ROMs/' + SubFolder + '/' + ROMSaveFilename)
                        OldPath = './ROMSaves/' + SubFolder + '/' + ROMSaveFilename.split('.')[0] + '/' + datetime.datetime.fromtimestamp(ROMSaveTimestamps[int(SelectedTimestamp)-1]['Timestamp']).strftime('%Y-%m-%d_%H%M%S')
                        NewPath = './ROMSaves/' + SubFolder + '/' + ROMSaveFilename.split('.')[0] + '/' + NewTimestamp.strftime('%Y-%m-%d_%H%M%S')
                        os.makedirs(NewPath, exist_ok=True)
                        shutil.copy(OldPath + '/' + ROMSaveFilename, NewPath + '/' + ROMSaveFilename)
                        shutil.copy(OldPath + '/' + ROMSaveFilename, './ROMs/' + SubFolder + '/' + ROMSaveFilename)
                        if SavePath != '':
                            shutil.copy(OldPath + '/' + ROMSaveFilename, SavePath + ROMSaveFilename)
                        SQLCreateEntry('ROMSaveTimestamps', { 'FileName': ROMSaveFilename, 'Timestamp': datetime.datetime.timestamp(NewTimestamp) })
                        SQLDeleteEntry('ROMSaveTimestamps', { 'Filename': ROMSaveFilename, 'Timestamp': ROMSaveTimestamps[int(SelectedTimestamp)-1]['Timestamp']})
                        shutil.rmtree(OldPath)
        #The user wants to verify that the database is ok and doesn't have any issues
        elif response == '13':
            #We call our initialize database function, which checks to make sure the needed tables are present in the database and will create any that are missing.
            #NOTE this does not currently verify the contents of the database as valid, so in some rare cases if a table gets created with an error in it's columns or it's data it may cause issues.
            InitializeDatabase()
    return 0

