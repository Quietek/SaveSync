#!/usr/bin/env python
import sqlite3
import time
import os
import requests
import json
import vdf
import re
import subprocess
import shutil
import sys
from SQLFunctions import *
from ClientFunctions import *
from SyncFunctions import *


#Our main executable
#Starts the interactive database manager by default
#supports a number of other command line options to add non-steam games, bring up a help menu, or perform a full sync on this client
if (__name__ == "__main__"):
    #Various variable initializations
    FirstRunFlag = False
    args = sys.argv
    CommandFlag = ''
    AppID = ''
    GameID = ''
    NewPath = ''
    GameTitle = ''
    ConfigPath = ''
    RomPathList = []
    #We check our first passed command line argument for one of the expected potential argument flags
    if len(sys.argv) > 1:
        if args[1].lower() == '--add' or args[1] == '-a':
            CommandFlag = 'add'
        elif args[1].lower() == '--sync' or args[1].lower() == '-s':
            CommandFlag = 'sync'
        elif args[1].lower() == '--silent' or args[1].lower() == '-si':
            CommandFlag = 'silent'
        elif args[1].lower() == '--help' or args[1].lower() == '-h':
            CommandFlag = 'help'
        elif args[1].lower() == '--list' or args[1].lower() == '-l':
            CommandFlag = 'list'
    #We iterate through all of our arguments to read in the passed in arguments after the first command line argument
    for argument in args:
        if '=' in argument:
            SplitArg = argument.split('=')
            if SplitArg[0].lower() == 'gameid':
                GameID = SplitArg[1]
            elif SplitArg[0].lower() == 'path':
                NewPath = SplitArg[1]
            elif SplitArg[0].lower() == 'config':
                ConfigPath = SplitArg[1]
            elif SplitArg[0].lower() == 'title':
                GameTitle = SplitArg[1]
    #We check if the SteamSync database has been initialized, and if it hasn't flag that this is a first run
    if not os.path.isfile('./saves.db'):
        FirstRunFlag = True
        InitializeDatabase()
    #We check if a custom configuration path was specified, and if not default to the file created at $HOME/.config/SteamSync/config
    if ConfigPath == '':
        ConfigPath = os.path.expanduser('~') + '/.config/SteamSync/config'
    #We check if the config exists, and flag this as the first run if the config file doesn't exist
    if not os.path.isfile(ConfigPath):
        InteractiveClientCreation(ConfigPath)
        FirstRunFlag = True
    #We read in the data from our config
    ClientDictionary = ReadClientConfig(ConfigPath)
    #We check if the commandflag is sync or silent, both of which ultimately mean we're just running our sync function
    #TODO need to add in silent functionality to actually mute the terminal output
    if CommandFlag == 'sync' or CommandFlag == 'silent' or FirstRunFlag:
        #We give the user a big of extra information if it's the first run, since we don't want them to be surprised when it takes a while
        if FirstRunFlag:
            print('This next part is probably going to take a while...')
            print('It should be a bit faster on subsequent runs.')
        else:
            print('Syncing, this may take a while...')
        #Our flag for if we're running it silent mode or not
        silent = False
        if CommandFlag == 'silent':
            silent = True
        #We pull in our global variables from the database
        SyncRoms = False
        MaxSaves = int(SQLGetEntry('GlobalVars',{'Key':'MaxSaves'},[])[0]['Value'])
        RawSteamCloud = SQLGetEntry('GlobalVars',{'Key':'IncludeSteamCloud'},[])[0]['Value']
        if RawSteamCloud == 'True':
            IncludeSteamCloud = True
        else:
            IncludeSteamCloud = False
        #We read in our config
        ClientDictionary = ReadClientConfig(ConfigPath)
        RomPathList = []
        #We pull our ROM folders from the config, flagging that we need to sync ROMs if we find at least one ROM path
        for key in ClientDictionary:
            if 'ROM' in key:
                RomPathList.append(ClientDictionary[key])
                SyncRoms = True
        #Our sync function calls, with a slight difference depending on if we're syncing ROMs or not
        if SyncRoms:
            FullSync(ClientDictionary["SteamPath"], ClientDictionary["ClientID"], IncludeSteamCloud, RomPathList, MaxSaves, silent, ClientDictionary["HomeDir"])
        else:
            FullSync(ClientDictionary["SteamPath"], ClientDictionary["ClientID"], IncludeSteamCloud, [], MaxSaves, silent, ClientDictionary["HomeDir"])
        #Extra terminal output for first runs to give the users ome extra information
        if FirstRunFlag:
            print('First Sync successfully completed!')
            print('To run another full system sync, execute ./SteamSync.py --sync from a terminal.')
            print('To add a new non-Steam game, execute ./SteamSync.py --add title={ GAME TITLE HERE } path={ PATH TO GAME SAVE DIRECTORY HERE }')
            print('If you want to use a custom path to sync an already backed up non-Steam game, execute ./SteamSync.py --add gameid={ GAMEID HERE } path={PATH TO GAME SAVE DIRECTORY HERE}')
            print('You can also run ./SteamSync.py with no command line arguments again to get an interactive client for all of these functions.')
    #The next section revolves around the add command line argument, which indicates we are either syncing a custom path for a known non-Steam game or adding a new non-Steam game
    elif CommandFlag == 'add':
        #If a game ID is specified and a path is specified, we treat this as if we are syncing a known game with the client
        if GameID != '' and NewPath != '':
            #We check to make sure the game actually exists in the database before attempting to sync it
            GameIDEntry = SQLGetEntry('NonSteamApps',{ 'GameID': int(GameID) })
            if len(GameIDEntry) > 0:
                MaxSaves = int(SQLGetEntry('GlobalVars',{'Key':'MaxSaves'},[])[0]['Value'])
                #We pull the client save information to check if the game exists in the database already, updating the database instead of creating a new entry if we do
                ClientSaveEntry = SQLGetEntry('NonSteamClientSaves',{ 'GameID': int(GameID), 'ClientID': int(ClientDictionary['ClientID']) })
                if len(ClientSaveEntry) > 0:
                    SQLUpdateEntry('NonSteamClientSaves',{ 'LocalSavePath': NewPath }, { 'GameID': int(GameID), 'ClientID': int(ClientDictionary['ClientID'])})
                else:
                    SQLCreateEntry('NonSteamClientSaves',{ 'GameID': int(GameID), 'ClientID': int(ClientDictionary['ClientID']), 'MostRecentSaveTime': 0, 'LocalSavePath': NewPath })
                    MostRecentSaveTime = GameIDEntry[0]['MostRecentSaveTime']
                    UIDFolderFlag = False
                    TempSplit = GameIDEntry[0]['RelativeSavePath'].split('/')
                    if len(TempSplit)> 1:
                        if TempSplit[-1] != '':
                            if '{ UID }' in TempSplit[-1]:
                                UIDFolderFlag = True
                        elif '{ UID }' in TempSplit[-2]:
                                UIDFolderFlag = True
                    SyncNonSteamGame(int(GameID), NewPath, MostRecentSaveTime, int(ClientDictionary['ClientID']), MaxSaves, UIDFolderFlag, True)
            else:
                print('ERROR: No game with GameID ' + GameID + ' in database, rerun this command without the GameID specified to add it as a new non-Steam game.')
        #If no GameID was specified, but we correctly read in a path and a title from the command line
        elif NewPath != '' and GameTitle != '':
            #We pull our list of games from the SQL database
            GameList = SQLGetEntry('NonSteamApps', { })
            #If we have at least one non-Steam game, we use the maximum gameid in the database + 1 as the new game ID
            #NOTE this means that the GameIDs actually represent the order games were added to the database
            if len(GameList) > 0:
                NewGameID = SQLGetMinMax('NonSteamApps', 'GameID', {}, False)[0]['MaxVal'] + 1
            else:
                NewGameID = 1
            #We use a seperate value to hold the relative save path
            RelativeSavePath = NewPath
            if '{ UID }' in NewPath:
                PathList = UIDFinder(NewPath)
                if len(PathList) > 1:
                    print("ERROR: The non-Steam UID tag was used on a folder with multiple entries. The UID tag is intended to be used for PC-specific filepaths.")
                elif len(PathList) == 0:
                    print('ERROR: No matching Paths Found.')
                else:
                    NewPath = PathList[0]
            #if we see a folder named drive_c we assume we're inside of a wine prefix
            if 'drive_c' in RelativeSavePath:
                #We split on drive_c, in order to get the path both before and after the wine prefix's root folder
                WinePrefix = RelativeSavePath.split('drive_c')[0]
                #We substitute in our { WINE PREFIX } string in the relative save path, so we can reference it later if we need to
                RelativeSavePath = RelativeSavePath.replace(WinePrefix, '{ WINE PREFIX }')
            #We replace any instances of $HOME with { HOME } in order to signal that the save is located somewhere within the home folder that isn't a wine prefix
            elif ClientDictionary['HomeDir'] in RelativeSavePath:
                RelativeSavePath = RelativeSavePath.replace(ClientDictionary['HomeDir'], '{ HOME }')
            #SQL entry creation for the new game save we just added
            SQLCreateEntry('NonSteamApps', {'GameID': NewGameID, 'Title': GameTitle, 'RelativeSavePath': RelativeSavePath, 'MostRecentSaveTime': 0})
            SQLCreateEntry('NonSteamClientSaves', {'GameID': NewGameID, 'ClientID':ClientDictionary['ClientID'], 'LocalSavePath':NewPath, 'MostRecentSaveTime': 0})
        #Extra end-user information if we couldn't either read in a GameID and path or a Title and a path
        else:
            print('ERROR: Make sure you only specify one game at a time, in one of the following formats:')
            print('./SteamSync.py --add path={ Save Path } TITLE={ TITLE } to add a new non-steam game')
            print('./SteamSync.py --add GameID={ Game ID } PATH={ SAVE PATH } to manually specify a save path for a client\'s install of a non-steam game')
    #We use this to list all the known steam and non-steam games for the user
    elif CommandFlag == 'list':
        SteamGames = SQLGetEntry('Steamapps', {})
        NonSteamGames = SQLGetEntry('NonSteamApps', {})
        AppIDList = GameListReadAndPrint('AppID', SteamGames)
        GameIDList = GameListReadAndPrint('GameID', NonSteamGames)
    #Help menu, displays information on how to use SteamSync
    elif CommandFlag == 'help':
        print('To bring up this help menu, run ./SteamSync.py --help')
        print('GENERAL INFORMATION: ')
        print('[]\'s indicate optional command line arguments')
        print('If {}\'s are listed in a formatting tooltip, that means to replace the contents with your custom values.')
        print('AppID\'s are Valve\'s method of identifying individual games within your library.')
        print('GameID\'s are a SteamSync specific value that are generated each time a new non-Steam game is added.')
        print('There are Three GAME TYPES: ROMs, Steam, and non-Steam')
        print('==============================================================================================================')
        print('COMMAND LINE OPTIONS:')
        print('To bring up this menu run ./SteamSync.py --help')
        print('To get a list of games run ./SteamSync.py  --list [GAMETYPE={ GAME TYPE }] [INSTALLED={ TRUE OR FALSE }]')
        print('         INSTALLED command line argument will limit output to only games that are registered to this client.')
        print('         GAMETYPE command line argument will limit the output to a specific game type.')
        print('         NOTE: ROMs and ROM Saves are not currently supported by this function')
        print('To run a full system scan and sync, run ./SteamSync.py --sync in a terminal')
        print('To add a new non-steam game, run ./SteamSync.py --add [GAMEID={ GAMEID }] TITLE={ GAME TITLE } PATH={ SAVE PATH }')
        print('         Optional command line argument GAMEID is to be used when specifying a custom save path for an already backed up non-Steam save.')
        print('==============================================================================================================')
        print('INTERACTIVE MODE:')
        print('By default, SteamSync will run in interactive mode when no command line arguments are passed or if the command line arguments passed couldn\'t be parsed.')
        print('1. Sync all games')
        print('         Performs a full system sync.')
        print('2. Help me add a new non-Steam Game')
        print('         Launches a helper function to help you add a non-Steam game to the database. Can be used to specify either a custom save path for an existing non-Steam game, or to add a brand new non-Steam game to the database.')
        print('3. Help me add a new ROM Folder')
        print('         Launches a helper function to help you add a new ROM folder to your configuration.')
        print('4. Sync ROM Folders')
        print('         Only syncs your ROM Folders and ROM Savegames.')
        print('         NOTE: Only .sav files for ROM Saves are currently detected and rollback for them is not currently supported.')
        print('5. Sync non-Steam Library')
        print('         Syncs only your non-Steam games.')
        print('         Will also check your ~/Games and { STEAM PATH }/steamapps/compatdata/ directories for existing non-Steam saves.')
        print('6. Sync specific Steam game')
        print('         Syncs saves for a specific steam game that is specified by it\'s AppID')
        print('7. Sync specific non-Steam game')
        print('         Syncs saves for a specific non-Steam game, specified by it\'s GameID')
        print('8. Manually update entry for Steam game')
        print('         Allows you manually edit database entries for a Steam game.')
        print('         You can use this function to specify file paths if the PCGW data is missing information or is incorrect.')
        print('         If the PC Gaming Wiki page is missing or has an incorrect save file path, consider contributing!')
        print('         More information available at: https://www.pcgamingwiki.com')
        print('9. Manually update entry for non-Steam game')
        print('         Allows you to manually edit database entries for a non-Steam game.')
        print('10. Delete Steam game Entry')
        print('         Deletes information on a steam game from the database.')
        print('         Can be used to delete global information, or client specific information.')
        print('11. Delete non-Steam game Entry')
        print('         Deletes information on a non-Steam game from the database.')
        print('         Can be used to delete global information, or client specific information.')
        print('12. Rollback game save [EXPERIMENTAL]')
        print('         WARNING: The save rollback feature is still actively being tested and developed, while it shouldn\'t delete your saves backed up with SteamSync, it will overwrite Game Saves on your PC. Use at your own risk.')
        print('         Rolls back a save for an installed game to an earlier version, and updates the database with the current time as the new save timestamp.')
        print('         This will only work if the game is installed on the client you are trying to roll back.')
        print('13. Verify database integrity')
        print('         This will check the database to make sure all tables exist and create any that are missing.')
        print('         NOTE: This does not verify integrity of individual records or column presence.')
        print('==============================================================================================================')
        print('UPDATES:')
        print('There currently isn\'t an automated function to check or update SteamSync.')
        print('If the version you are using appears to be broken, check https://www.github.com/Quietek/SteamSync to manually update SteamSync.')
        print('To manually update, simply download the newest release from github, extract, and copy and overwrite into your current SteamSync directory.')
    #If no command flag was found, we run our interactive database manager instead
    else:
       InteractiveDatabaseManager(ClientDictionary['SteamPath'], ConfigPath)
