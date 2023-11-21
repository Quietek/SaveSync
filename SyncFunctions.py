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
import datetime
from SQLFunctions import *

#Function to copy data from the server to the current client
def CopySaveFromServer(SaveDict):
    #Terminal output to tell us information on the current process
    print("Copying Save From Server...")
    #initiate our filename variable
    FileName = ''
    #Create our backup directory variable with the AppID and the timestamp of the save
    BackupDirectory = "./Backups" + "/" + SaveDict['AppID'] + "/" + datetime.datetime.fromtimestamp(SaveDict['Timestamp']).strftime('%Y-%m-%d_%H%M%S')
    #Initiate our destination directory from our Prefix value
    DestinationDirectory = SaveDict['Prefix']
    #For each of our suffix values
    for suffix in SaveDict['Suffixes']:
        #if the suffix isn't just a null value
        if suffix != '':
            #We need to get our relative suffix, in case the prefix is only root
            RelativeSuffix = GetRelativePath(SaveDict,'/' + suffix)
            #Split our suffix by each folder
            TempSplit = suffix.split('/')
            #If our last value from the split isn't blank, we use that as our filename
            if TempSplit[-1] != '':
                FileName = TempSplit[-1]
            #if our last value from teh split is blank, we use the second to last value as the filename instead
            else:
                FileName = TempSplit[-2]
            #We get our preceding folders by splitting on the filename and using the path before the filename
            PrecedingFolders = RelativeSuffix.split(FileName)[0]
            #The path to the file or folder we are copying is based on our backup directory, and then our suffix and filename
            Source = BackupDirectory + '/' + PrecedingFolders + FileName
            #the path to our destination is the prefix and suffix combined together
            Destination = SaveDict['Prefix'] + '/' + suffix
            #we perform a check to see if our source value is a file or directory
            if os.path.isdir(Source):
                #Terminal output for debugging
                print("Source: " + Source)
                print("Destination: " + Destination)
                #We make the destination drectory if it doesn't already exist
                os.makedirs(Destination.replace(FileName,''),exist_ok=True)
                #Copy our folder to the destination
                shutil.copytree(Source,Destination, dirs_exist_ok=True)
                print("Save Successfully Copied!")
            #If the source is a file as opposed to a folderprint
            elif os.path.isfile(Source):
                #Terminal output for debugging
                print("Source: " + Source)
                print("Destination: " + Destination)
                #Make our preceding folders for the destination file if they don't exist
                os.makedirs(Destination.replace(FileName,''),exist_ok=True)
                #If our destination file already exists, we need to delete it to prevent a file exists error
                if os.path.isfile(Destination):
                    os.remove(Destination)
                #Copy our file to the destination
                shutil.copy(Source,Destination)
                print("Save Successfully Copied!")
        else:
            #When our suffix is empty, we know we only need to use the prefix to determine our file information
            TempSplit = SaveDict['Prefix'].split('/')
            #Get our filename, using the last value of our directory split if it's not blank
            if TempSplit[-1] != '':
                FileName = TempSplit[-1]
            #if it is blank, we need to use the value preceding the last value as our filename
            else:
                FileName = TempSplit[-2]
        #Since we have no suffix, our source file is going to be just the filename in the backup directory
        Source = BackupDirectory + '/'  + FileName
        #And our destination is just our prefix
        Destination = SaveDict['Prefix']
        #Check to see if our source is a directory or a file
        if os.path.isdir(Source):
            #Terminal output for debugging
            print("Source: " + Source)
            print("Destination: " + Destination)
            #Make the preceding directories for our destination directory if it doesn't exist, since it may not exist before we run a game
            os.makedirs(Destination.replace(FileName,''),exist_ok=True)
            #If our destination is a directory and it already exists, we need to remove it to prevent file exists errors
            if os.path.isdir(Destination):
                shutil.rmtree(Destination)
            #Copy our directory to our destination
            shutil.copytree(Source,Destination, dirs_exist_ok=True)
            print("Save Successfully Copied!")
        #Check to see if our source is a file
        elif os.path.isfile(Source):
            #Terminal output for debugging
            print("Source: " + Source)
            print("Destination: " + Destination)
            #Make the preceding directories for our destination if it doesn't exist
            os.makedirs(Destination.replace(FileName,''),exist_ok=True)
            #If our destination already exists as a file, we need to remove it
            if os.path.isfile(Destination):
                os.remove(Destination)
            #Copy our file to the destination
            shutil.copy(Source,Destination)
            print("Save Successfully Copied!")
    return 0

def CopySaveToServer(SaveDict, MaxSaves):
    #Terminal Output for debugging
    print("Copying Save To Server...")
    BackupDirectory = "./Backups" + "/" + SaveDict['AppID'] + "/" + datetime.datetime.fromtimestamp(SaveDict['Timestamp']).strftime('%Y-%m-%d_%H%M%S')
    SaveDirectory = "./Backups" + '/' + SaveDict['AppID'] + '/'
    if not os.path.isdir(BackupDirectory):
        os.makedirs(BackupDirectory,exist_ok=True)
    #Initialize our filename variable as an empty value for use later
    FileName = ''
    SortedSaves = sorted(os.listdir(SaveDirectory))
    if len(SortedSaves) > MaxSaves:
        print("Reached Maximum number of saves...")
        print("Removing oldest save from backups folder...")
        print("Deleting Directory: " + SaveDirectory + SortedSaves[0])
        OldestTimestamp = SQLGetMinMax('SaveTimestamps', 'Timestamp', {'AppID': SaveDict['AppID'] },True)[0]['MinVal']
        SQLDeleteEntry('SaveTimestamps', {'AppID': SaveDict['AppID'], 'Timestamp':OldestTimestamp })
        if os.path.isdir(SaveDirectory + '/' + SortedSaves[0]):
            shutil.rmtree(SaveDirectory + SortedSaves[0])
        print("Directory Successfully Deleted!")
    #If our suffixes are a length of 0 or 1, we know that we only need to worry about 1 file/folder
    if len(SaveDict['Suffixes']) == 0 or (len(SaveDict['Suffixes']) == 1 and SaveDict['Suffixes'] == ['']):
        #Generate the list of preceding directories using our prefix
        SplitPath = SaveDict['Prefix'].split('/')
        #Initiate filename based on the final non-blank value of our previous split
        if SplitPath[-1] != '':
            FileName = SplitPath[-1]
        else:
            FileName = SplitPath[-2]
        #We check to see if our prefix value is a directory
        if os.path.isdir(SaveDict['Prefix']):
            #Terminal output for debugging
            print("Source: " + SaveDict['Prefix'])
            print("Destination: " + BackupDirectory + '/' + FileName)
            #Copy our directory into our backups folder
            shutil.copytree(SaveDict['Prefix'],BackupDirectory + '/' + FileName,dirs_exist_ok=True)
            print("Save Successfully Copied!")
        #if our value is not a folder, it must be a file
        #NOTE we already know that the file MUST exist from our earlier checks to get the timestamp
        else:
            #Terminal output for debugging
            print("Source: " + SaveDict['Prefix'])
            print("Destination: " + BackupDirectory + '/' + FileName)
            #Copy our file into our backup directory
            shutil.copy(SaveDict['Prefix'],BackupDirectory + '/' + FileName)
            print("Save Successfully Copied!")
    #If the length of our suffixes isn't 0 or 1, we know we have multiple files to backup
    else:
        #We iterate through our list of suffixes
        for suffix in SaveDict['Suffixes']:
            #We get our relative suffix, since the prefix could be the root directory, and we need to make the structure compatible across clients
            RelativeSuffix= GetRelativePath(SaveDict,'/' + suffix)
            #We split our suffix to get our filename
            TempSplit = suffix.replace('////','/').replace('///','/').replace('//','/').split('/')
            #Pull our filename from the last non blank value of our suffix
            if TempSplit[-1] != '':
                FileName = TempSplit[-1]
            else:
                FileName = TempSplit[-2]
            #Get the preceding folders to our filename by splitting on the filename and taking the first value
            PrecedingFolders = RelativeSuffix.split(FileName)[0]
            #Make our destination directories for our save
            os.makedirs(BackupDirectory+'/'+PrecedingFolders,exist_ok=True)
            #We check to see if our source is a directory
            if os.path.isdir(SaveDict['Prefix'] + '/' + suffix):
                #Terminal output for debugging
                print("Source: " + SaveDict['Prefix'] + '/' + suffix)
                print("Destination: " + BackupDirectory + '/' + PrecedingFolders + '/' + FileName)
                #Copy our file into our backup directory
                shutil.copytree(SaveDict['Prefix'] + '/' + suffix, BackupDirectory + '/' + PrecedingFolders + '/' + FileName, dirs_exist_ok=True)
                print("Save Successfully Copied!")
            #If the preceding folders value is blank and we know our suffix isn't a directory, we need to handle it slightly differently to prevent blank/empty folder creation
            elif PrecedingFolders == '':
                print("Source: " + SaveDict['Prefix'] + '/' + suffix)
                print("Destination: " + BackupDirectory + '/' + FileName)
                #Copy our file to the backup directory
                shutil.copy(SaveDict['Prefix'] + '/' + suffix, BackupDirectory + '/' + FileName)
                print("Save Successfully Copied!")
            #Otherwise, we know to copy the file into our newly created folders
            elif '{ UID }' not in SaveDict['Prefix']:
                print("Souce: " + SaveDict['Prefix'] + '/' + suffix)
                print("Destination: " + BackupDirectory + '/' + PrecedingFolders + '/' + FileName)
                #Copy our file to the backup directory
                shutil.copy(SaveDict['Prefix'] + '/' + suffix, BackupDirectory + '/' + PrecedingFolders + '/' + FileName)
                print("Save Successfully Copied!")
    return 0

#Function to find the differences in file paths if multiple files/folders are found that we need to backup
def GetPrefixAndSuffixes(PathList):
    #initialize a min length value for us to compare against
    MinLength = 100
    for path in PathList:
        TempSplit = path.split('/')
        if len(TempSplit) < MinLength:
            MinLength = len(TempSplit)
    #initialize values to use for finding our differences
    i = 0
    index = 0
    found = False
    Prefix = ''
    Suffixes = []
    if len(PathList) != 2 or ('{ UID }' not in PathList[0] and '{ UID }' not in PathList[1]):
        #a while loop to loop through our list of directories until we find the differences
        while (i < MinLength) and (not found):
            #We use our initial path as our baseline to compare to
            ComparisonPath = PathList[0].split('/')
            #We find our total number of paths from the length of our input list
            NumPaths = len(PathList)
            #We iterate through all our paths after our baseline path
            for j in range(1,NumPaths):
                #Create a temporary variable to hold a list of all our directories
                TempSplit = PathList[j].split('/')
                #If the directory we're looking at is the same as our baseline
                if TempSplit[i] == ComparisonPath[i] and not found:
                    #and we know this is the last path in our path list we have to examine
                    if j == NumPaths-1 and not found:
                        #Add the current directory to our prefix
                        Prefix += TempSplit[i] + '/'
                #If we know this isn't the first value we're examining and we haven't found it
                elif j != 1 and not found:
                    #Our suffix is the end of the current path we're examining
                    index = len(Prefix)
                    Suffixes.append(PathList[j][index:])
                    found = True
                    #Make sure we append the paths we already checked to our suffixes
                    for k in range(1,j+1):
                        Suffixes.append(PathList[k][index:])
                #If this is the first comparison path in our path list
                elif not found:
                    #we found our differentiating index and this is the first value in our path list, so we don't need to add any already checked values to our suffixes
                    index = len(Prefix)
                    Suffixes.append(PathList[j][index:])
                    found = True
                #Add any paths after our first differentiator is found to our suffixes
                else:
                    Suffixes.append(PathList[j][index:])
            #If we found our differences, we need to append our baseline path to our suffixes
            if found:
                Suffixes.append(PathList[0][index:])
            #Otherwise, we know we need to keep iterating through our list of directories
            else:
                i += 1
    else:
        FullPath = ''
        PostUIDPath = ''
        for path in PathList:
            if '{ UID }' in path:
                PostUIDPath = path.replace('{ UID }','')
            else:
                FullPath = path
        TempVal = FullPath.replace(PostUIDPath,'')
        
        Prefix = TempVal.replace('{ UID }','')
        UID = FullPath.replace(Prefix,'').replace(PostUIDPath,'')
        Suffixes.append(UID + '/' + PostUIDPath)
        
    return (Prefix,Suffixes)

#Function to get the time modified of a file
def GetTimeModified(FilePath):
    #initialize baseline value to 
    LastTimeModified = 0
    #If our filepath is a directory
    if os.path.isdir(FilePath):
        #We use the time modified of our current directory as a baseline
        LastTimeModified = os.path.getmtime(FilePath)
        #We iterate through every file in our current directory
        for file in os.listdir(FilePath):
            #If the file is actually a file
            if os.path.isfile(FilePath + '/' + file):
                #we compare the time modified of the file to our baseline time modified and use whichever is greater as the current time modified
                if os.path.getmtime(FilePath + '/' + file) > LastTimeModified:
                    LastTimeModified = os.path.getmtime(FilePath + '/' + file)
            #If the file we're looking at is a directory and it isn't the current working directory or a parent directory 
            elif os.path.isdir(FilePath + '/' + file) and file not in ('.','..'):
                #We recursively call our function on the directory, to continue looking for modified files
                TempTimeModified = GetTimeModified(FilePath + '/' + file)
                #If our recursive function call has a more recent time modified than our last time modified we change the last time modified value to our recursive call
                if TempTimeModified > LastTimeModified:
                    LastTimeModified = TempTimeModified
    #if our filepath is a file
    elif os.path.isfile(FilePath):
        #We use the time modified of the file as our last time modified
        LastTimeModified = os.path.getmtime(FilePath)
    return LastTimeModified

#Function to check for the existence of files to potentially backup
def VerifyLocalData(ReferencePaths):
    #intialize basic values
    ReturnList = []
    SaveType = 'Unfound'
    #for each of our paths in our reference list
    for path in ReferencePaths:
        #We get a list of directories from our path to remove any blank directories from the list
        Directories = path.split('/')
        TempList = []
        for directory in Directories:
            if directory != '':
                TempList.append(directory)
        Directories = TempList
        #If we haven't found a file yet, or we have found a file and we can tell that we are looking for a file by the syntax of our reference path
        if (SaveType in ['Unfound', 'Filename'] and (Directories[-1][-1] == '*' or ('.' in Directories[-1]))):
            TempPath = ''
            #We copy our preceding folders into a temporary value
            for i in range(0,len(Directories)-1):
                TempPath += '/' + Directories[i]
            #We get our filename and replace the values with regular expression friendly syntax
            filename = Directories[-1].replace('.','\.').replace('*','.*')
            #If our preceding directory exists
            if os.path.isdir(TempPath):
                #we compile our regular expression
                regexp = re.compile(filename)
                #we check each file in our preceding folder
                for file in os.listdir(TempPath):
                    #if our regular expression matches the file we're looking at
                    if regexp.match(file):
                        #We know we are looking for individual files as opposed to directories
                        SaveType = 'Filename'
                        #We append our found file to our return value with the time modified timestamp and make it clear we found a matching value
                        ReturnPath = TempPath + '/' + file
                        ReturnList.append({'AbsolutePath':ReturnPath, 'SaveType':'Filename', 'Found':True, 'TimeModified':GetTimeModified(ReturnPath)})
        #If our path exists and we're looking for directories or we haven't determined whether we're looking for directories or files yet
        elif SaveType in ['Unfound','Directory'] and os.path.isdir(path):
            #We append our path to the return list with a timestamp and a found flag
            ReturnList.append({'AbsolutePath': path, 'SaveType':'Directory', 'Found':True, 'TimeModified': GetTimeModified(path)})
        elif '{ UID }' in path:
            ReturnList.append({'AbsolutePath': path, 'SaveType':'UID', 'Found':True, 'TimeModified': 0 })
        #otherwise, append our path to the return list and mark it as unfound
        else:
            ReturnList.append({'AbsolutePath': path, 'SaveType':'Unfound', 'Found':False})
    return ReturnList

#Function to find matching file or folder names when they need to be substituted for a unique UID
def UIDFinder(Path,Exclusions=[]):
    #Initialize Final Return Value List
    ReturnPaths = []
    #For each path in the paths list
    #Count the number of UID substitutions in our current path
    UIDCount = Path.count('{ UID }')
    #initialize flags and empty values for usage later
    FilenameFlag = False
    PartialFilenameFlag = False
    splitpath = []
    CurrentCount = 0
    #Split the path on the instances of a UserID
    #Multiple UserIDs can be present without necessarily being the same
    #UserIDs can be dependent on your steam login, or can be game specific, or be specific to other services
    SplitPath = Path.split('{ UID }')
    #remove empty values that may be present from our split on the UIDs
    if '' in SplitPath:
        SplitPath.remove('')
    #if the first character is a . after our last UID substitution, we flag that the last UID is a filename
    if SplitPath[-1][0] == '.':
        FilenameFlag = True
    #if the last character before our current sUID substitution is not a /, we flag that the current UID is a partial folder or filename
    if SplitPath[0][-1] != '/':
        PartialFilenameFlag = True
    #if we are working with a current partial file/folder name
    if PartialFilenameFlag:
        #initialize the parent path as /
        ParentPath = '/'
        #we get a list of directories preceding our partial folder/filename by splitting on each /
        parentdirectories = SplitPath[0].split('/')
        #initialize the beginning our regular expression pattern
        #uses the last value from our directory list, since it should be our partial filename
        parentpattern = parentdirectories[-1].replace('(','\(').replace(')','\)').replace('.','\.').replace('*','.*')
        #get back our path preceding the file/folder we're looking for
        for i in range(0,len(parentdirectories)-1):
            ParentPath += parentdirectories[i] + '/'
        #make sure this is an existing filepath before moving forward
        if os.path.isdir(ParentPath):
            #get a list of files/folders fromm the current path
            Files = os.listdir(ParentPath)
            #variable initialization for usage later
            TempPaths = []
            pattern = ''
            #check the length of our split path value
            #if the length is at least 2, we may need to add an ending pattern to our previously initialized patterh
            if len(SplitPath) >= 2:
                #check if we're preceding a folder
                if SplitPath[1][0] == '/':
                    #match any file with data matching our preceding pattern and any characters afterwards
                    pattern = parentpattern + '.*'
                #if we're not preceding a folder
                else:
                    #split our path after our UID sub so we can get the individual folder names and the partial filename after our substitution
                    childdirectories = SplitPath[1].split('/')
                    #sanitize the input to correctly interpret parentheses, periods, and asterisks from our partial filename
                    childpattern = childdirectories[0].replace('(','\(').replace(')','\)').replace('.','\.').replace('*','.*')
                    #create our final pattern with the partial filename preceding our UID substitution, our UID substitution, and then the partial filename after our UID substitution
                    pattern = parentpattern + '.*' + childpattern
            #if the length of splitpath is less than 2, we know we are the last portion of the filepath
            #creates a pattern with the preceding partial filepath
            else:
                pattern = parentpattern + '.*'
            #compile our regular expression using the pattern we created before
            regexp = re.compile(pattern,re.IGNORECASE)
            #initialize a variable to flag when we've found at least one match
            found = False
            #for each of our files in our parent directory
            for file in Files:
                #if our file matches our regular expression and it's not excluded in our exclusion list
                if regexp.match(file) and file not in Exclusions:
                    #create a temporary filepath to hold our currently found file path
                    temppath = ParentPath + file
                    #flag that it's been found and reduce our UIDCount to know we need one less substitution
                    if not found:
                        found = True
                        UIDCount -= 1
                    #append everything after our full filename to our 
                    temppath += SplitPath[1][SplitPath[1].find('/'):len(SplitPath[1])]
                    #append to our temporary list of paths
                    TempPaths.append(temppath)
            #Error catching for if there are too many or too few UIDs that still need to be found after our current UID in comparison to the length of our full filepath
            if UIDCount > 0:
                if UIDCount > len(SplitPath):
                    print("ERROR! More UIDs Expected to be inserted than are room for")
                elif UIDCount < len(SplitPath) - 1:
                    print("ERROR! Not enough UIDs to insert into split string")
                else:
                    #We know we have further UID Replacements to make
                    #For each path that we've found replacements for so far
                    for i in range(0,len(TempPaths)):
                        #for each UID we still need to replace
                        for j in range(0,UIDCount):
                            #we're joining on the entries past the ones we just joined (aka the first two entries in SplitPath)
                            #so our UIDs left to replace should be in the range of len(splitpath) - 1 and len(splitpath)

                            #we add an additional 1 to compensate for the fact we start at index 0
                            #this is only significant on the last UID replacement, since any before should replace by joining both entries in splitpath together
                            if len(SplitPath) < j + 2:
                                TempPaths[i] = TempPaths[i] + '{ UID }'
                            else:
                                TempPaths[i] = TempPaths[i] + '{ UID }' + SplitPath[j+1]
                            ReturnPaths.append(UIDFinder(TempPaths[i],Exclusions))
            elif UIDCount == 0 and len(SplitPath) > 2:
                print("ERROR! Expecting to fill more UIDs")
            else:
                #we can append our current paths onto our return value
                ReturnPaths.extend(TempPaths)
    #if this is the last UID replacement and we know it's a filename)
    #NOTE don't need to handle filenames unless it's the end of the path, since we know everything preceding it has to be a folder
    elif len(SplitPath) == 2 and FilenameFlag:
        #initialize our pattern, consisting of any string preceding our presumed file extension
        #replacements used to correct interpretation of patterns from PCGW
        pattern = '.*' + SplitPath[1].replace('.','\.').replace('*','.*')
        #compile our regular expression
        regexp = re.compile(pattern,re.IGNORECASE)

        #initialize our found flag
        found = False
        #check to make sure the path preceding the filename exists
        if os.path.isdir(SplitPath[0]):
            #get all the files in our directory
            files = os.listdir(SplitPath[0])
            #for each file/folder in the directory
            for file in files:
                #look for matches on our regular expression that aren't excluded
                if regexp.match(file) and file not in Exclusions:
                    #if we have a match, append it to our return value
                    ReturnPaths.append(SplitPath[0] + file)
                    #if we matched and haven't flagged that we found the value, update the flag and reduce our UIDCount for potential recursive calls
                    if not found:
                        found = True
                        UIDCount -= 1
        #if we didn't find a matching file/folder, append the path we were passed in to the return list
        if not found:
            ReturnPaths.append(Path)

        #we've passed our filename and partial filename checks
        #we know that the current substitution is a full folder name
    else:
        #initialize our found flag
        found = False
        #check to make sure the preceding path exists
        if os.path.isdir(SplitPath[0]):
            #initialize our list of files/folders and a temporary list to use
            files = os.listdir(SplitPath[0])
            TempPaths = []
            #for each file in the cucurrent directory
            for file in files:
                #make sure it's a directory, not a file
                if os.path.isdir(SplitPath[0] + file) and file not in Exclusions:
                    #we consider the file to be a match, append it to our current path and our path list
                    temppath = SplitPath[0] + file
                    TempPaths.append(temppath)
                    #update our found flag to indicate we had a match on the UID, and update UIDCount as well
                    if not found:
                        found = True
                        UIDCount -= 1
            #if we replaced the folder path, but we know that there is one more folder to replace at the end
            if UIDCount == 1 and found and len(SplitPath) == 2:
                #append a string to indicate that we need to find one more UID to sub, and recursively call the function on our new paths
                for i in range(0,len(TempPaths)):
                    TempPaths[i] += '{ UID }'
                    ReturnPaths.extend(UIDFinder(TempPaths[i],Exclusions))
            #our UIDCount is acceptable, and we have more UIDs to find/substitute
            elif UIDCount > 0 and found and UIDCount < len(SplitPath) and UIDCount >= len(SplitPath) - 2:
                #append the UID substitution string for each UID we still need to find
                for i in range(0,len(TempPaths)):
                    for j in range(0,UIDCount):
                        TempPaths[i] += '{ UID }' + SplitPath[j+2]
                #recursively call the function on our updated list of UID substitutions we still need to make
                for path in TempPaths:
                    ReturnPaths.extend(UIDFinder(path,Exclusions)) 
            elif UIDCount == 0 and found:
                if len(SplitPath) == 2:
                    for i in range(0,len(TempPaths)):
                        TempPaths[i] += SplitPath[1]
                #extend our return value with our final filepath after all the UIDs have been substituted/found
                ReturnPaths.extend(TempPaths)
            #our UIDCount was considered unacceptable, so we return the original filepath we were passed
            else:
                ReturnPaths.append(Path)
    #if we didn't find anything to return, return the original paths we were passed
    if ReturnPaths == []:
        ReturnPaths.append(Path)
    return ReturnPaths

#Function to sync a specified ROM Folder
#NOTE ROMs can be used from the same removable drive that steamsync is located, so you do not need to have multiple copies of your ROMs on the same machine if you don't want to.
#To do so, simply don't specify a ROM folder for the client in your config file located at $HOME/.config/SteamSync/
def SyncRomFolder(LocalPath, ServerPath, ExcludedFolders, MaxSaves):
    #Terminal output to give the user information on what folder we're actually copying from
    print("Syncing ROM Folder...")
    print(LocalPath)
    print("Local Path: " + LocalPath)
    print("Server Path: " + ServerPath)
    #Variable initialization
    LocalFiles = []
    ServerFiles = []
    #NOTE other save file extensions can be specified here, these are specifically for saves that are located in the same location as the ROM folders
    #These are typically only necessary for cartridge based games
    #If you have an emulator saving in a different location, add it as a non-Steam game, NOT as a file extension here
    SaveExtensions = ['sav', 'eep', 'fla', 'srm', 'ss']
    ROMExtensions = ['z64', 'gba', '3ds', 'rvz', 'iso', 'nsp', 'xci', 'cue', 'bin', 'sfc', 'nes']
    TempSplit = ServerPath.split('/')
    #We check wheter we have to flag the current folder as a subfolder
    #We use the subfolder indication to know which folders to sync from our root rom folder and which we're syncing to a different location
    if TempSplit[-1] != 'ROMs':
        SubFolder = TempSplit[-1]
    #If the folder we're syncing is just ROMs, we don't have to specify a subfolder of any sort
    else:
        SubFolder = ''
    #We check to see if the specified local path exists or not
    if os.path.isdir(LocalPath):
        LocalFiles = os.listdir(LocalPath)
    #If the folder doesn't exist, we make it
    else:
        os.makedirs(LocalPath, exist_ok=True)
    #We get a list of ROM files from the server if a ROM folder on the server exists
    if os.path.isdir(ServerPath):
        ServerFiles = os.listdir(ServerPath)
    #If the backup folder doesn't exist, we make it
    else:
        os.makedirs(ServerPath, exist_ok=True)
    #We make a ROMSaves directory too, to keep a save history for our save file extensions
    if not os.path.isdir("./ROMSaves"):
        os.makedirs("./ROMSaves")
    #we iterate through all the files that exist in the local path
    for localfile in LocalFiles:
        #We initialize a flag to indicate when we're dealing with a save file instead of a ROM file
        SaveFlag = False
        i = 0
        TempSplit = localfile.split('.')
        #We iterate through our list of save file extensions, and if the file has one, we flag that we're dealing with a save file
        while not SaveFlag and i < len(SaveExtensions) and len(TempSplit) > 1 and TempSplit[-1].lower() not in ROMExtensions:
            extension = SaveExtensions[i]
            if extension in TempSplit[-1].lower() and len(TempSplit) > 1:
                SaveFlag = True
            else:
                i += 1
        #If the file we're looking at is actually a directory and we aren't specifically excluding it to sync to a different location, we recursively call our SyncRomFolder function to sync the contents of that folder as well
        if os.path.isdir(LocalPath + '/' + localfile) and localfile not in ExcludedFolders:
            SyncRomFolder(LocalPath +'/' + localfile, ServerPath + '/' + localfile, ExcludedFolders, MaxSaves)
        #If the file is missing from the server, isn't a save, and isn't flagged as excluded from our current sync, we copy it to the server
        elif localfile not in ServerFiles and not SaveFlag and localfile not in ExcludedFolders:
            print("Copying ROM From Client...")
            print("Source: " + LocalPath + '/' + localfile)
            print("Destination: " + ServerPath + '/' + localfile)
            shutil.copy(LocalPath + '/' + localfile,ServerPath +'/' + localfile)
            print("ROM Successfully copied!")
        #If the file is a save, isn't in an excluded folder, and the file exists on both the server and the client
        elif SaveFlag and localfile in ServerFiles and localfile not in ExcludedFolders:
            #We get the local save file's timestamp from our GetTimeModified function
            LocalTimestamp = GetTimeModified(LocalPath + '/' + localfile)
            #We use a temporary value to hold our folder names
            TempSplit = ServerPath.split('/')
            #We get the save's SQL data from the server
            #We get the server saves timestamp via our SQL data
            ServerTimestamp = SQLGetMinMax('ROMSaves','Timestamp',{'Filename':localfile, 'SubFolder':SubFolder})[0]['MaxVal']
            #We get the file's extension
            Extension = localfile.split('.')[-1]
            if not ServerTimestamp:
                ServerTimestamp = GetTimeModified(ServerPath + '/' + localfile)
                SQLCreateEntry('ROMSaves',{ 'Filename':localfile, 'SubFolder': SubFolder, 'Timestamp': ServerTimestamp })
                SQLCreateEntry('ROMSaveTimestamps', { 'Filename':localfile, 'Timestamp': ServerTimestamp })
                os.makedirs("./ROMSaves/" + SubFolder + '/' + localfile.replace('.' + Extension,'') + '/' + datetime.datetime.fromtimestamp(ServerTimestamp).strftime('%Y-%m-%d_%H%M%S') + '/',exist_ok=True)
                shutil.copy(ServerPath + '/' + localfile, "./ROMSaves/" + SubFolder + '/' + localfile.replace('.' + Extension,'') + '/' + datetime.datetime.fromtimestamp(ServerTimestamp).strftime('%Y-%m-%d_%H%M%S') + '/')
            #We overwrite the local save with the server save if the server save is more recent
            if ServerTimestamp > LocalTimestamp:
                print("More Recent ROM Save found on server than on client!")
                print("Deleting local ROM Save...")
                os.remove(LocalPath + '/' + localfile)
                print("ROM Save Successfully deleted!")
                print("Copying Updated ROM Save to Client...")
                print("Source: " + ServerPath + '/' + localfile)
                print("Destination: " + LocalPath + '/' + localfile)
                shutil.copy(ServerPath + '/' + localfile,LocalPath + '/' + localfile)
                print("ROM Save successfully copied!")
            #We back up the save currently stored on the server, then copy the local file to the server if the local file is more recent
            elif LocalTimestamp > ServerTimestamp:
                print("More recent ROM Save found on client than on server!")
                print("Moving Server Save to Backup Folder...")
                print("Deleting Server ROM Save: " + ServerPath + '/' + localfile)
                print("Server ROM Save successfully delteted!")
                print("Copying Updated ROM Save to Server...")
                print("Source: " + LocalPath + '/' + localfile)
                print("Destination: " + ServerPath + '/' + localfile)
                #SQL entry updates and creation to keep track of our save timestamps
                SQLUpdateEntry('ROMSaves',{'Timestamp':LocalTimestamp},{'Filename':localfile,'SubFolder':SubFolder})
                SQLCreateEntry('ROMSaveTimestamps',{'FileName': localfile, 'Timestamp': LocalTimestamp})
                #We make the backup directory and copy the save file into it since we're overwriting our server save
                os.makedirs("./ROMSaves/" + SubFolder + '/' + localfile.replace('.' + Extension,'') + '/' + datetime.datetime.fromtimestamp(LocalTimestamp).strftime('%Y-%m-%d_%H%M%S'), exist_ok=True)
                os.remove(ServerPath + '/' + localfile)
                shutil.copy(LocalPath + '/' + localfile, ServerPath + '/' + localfile)
                shutil.copy(LocalPath + '/' + localfile, "./ROMSaves/" +  '/' + SubFolder + '/' + localfile.replace('.' + Extension,'') + '/' + datetime.datetime.fromtimestamp(LocalTimestamp).strftime('%Y-%m-%d_%H%M%S') + '/')
                #We sort the list of save timestamps we have backed up currently
                SortedSaveList = sorted(os.listdir("./ROMSaves/" + SubFolder + '/' + localfile.replace('.' + Extension,'')))
                SaveTimestampsList = SQLGetEntry('ROMSaveTimestamps', {'FileName': localfile })
                if len(SaveTimestampsList) > MaxSaves:
                    print('Maximum number of saves reached...')
                    OldestTimestamp = SQLGetMinMax('ROMSaveTimestamps','Timestamp', { 'FileName': localfile }, True)[0]['MinVal']
                    print('Deleting Oldest ROM Save Directory with timestamp: ' + datetime.datetime.fromtimestamp(OldestTimestamp).strftime('%Y-%m-%d_%H%M%S'))
                    SQLDeleteEntry('ROMSaveTimestamps',{'Timestamp': OldestTimestamp, 'FileName': localfile })
                    if os.path.isdir('./ROMSaves/' + SubFolder + '/' + localfile.replace('.' + Extension,'') + '/' + datetime.datetime.fromtimestamp(OldestTimestamp).strftime('%Y-%m-%d_%H%M%S')):
                        shutil.rmtree('./ROMSaves/' + SubFolder + '/' + localfile.replace('.' + Extension,'') + '/' + datetime.datetime.fromtimestamp(OldestTimestamp).strftime('%Y-%m-%d_%H%M%S'))
                    print('ROM Save successfully deleted!')
                #We delete the oldest save if we've reached our maximum number of backups
                print("ROM Save successfully copied!")
        #If the file is a save and doesn't exist on the server
        elif SaveFlag and localfile not in ServerFiles and localfile not in ExcludedFolders:
            print("ROM Save found on client that doesn't exist on Server!")
            #We get the file extension
            Extension = localfile.split('.')[-1]
            #We get the time modified of our local file and make new SQL entries for our new save file
            LocalTimestamp = GetTimeModified(LocalPath + '/' + localfile)
            SQLCreateEntry('ROMSaves',{'FileName':localfile, 'SubFolder':SubFolder,'Timestamp':LocalTimestamp})
            SQLCreateEntry('ROMSaveTimestamps',{'FileName':localfile,'Timestamp':LocalTimestamp})
            #User information output and copying the new save onto our server
            print("Copying local ROM Save to server...")
            print("Source: " + LocalPath + '/' + localfile)
            print("Destination: " + ServerPath + '/' + localfile)
            os.makedirs("./ROMSaves/" + SubFolder + '/' + localfile.replace('.' + Extension,'') + '/' + datetime.datetime.fromtimestamp(LocalTimestamp).strftime('%Y-%m-%d_%H%M%S'),exist_ok=True)
            shutil.copy(LocalPath + '/' + localfile, "./ROMSaves/" + SubFolder + '/' + localfile.replace('.' + Extension,'') + '/' + datetime.datetime.fromtimestamp(LocalTimestamp).strftime('%Y-%m-%d_%H%M%S') + '/')
            shutil.copy(LocalPath + '/' + localfile,ServerPath + '/' + localfile)
            print("ROM Save successfully copied!")
    #We iterate through our list of files on the server
    for serverfile in ServerFiles:
        #We recursively call this function if it's a folder
        if os.path.isdir(serverfile) and serverfile not in ExcludedFolders:
            SyncRomFolder(LocalPath + '/' + serverfile, ServerPath + '/' + serverfile, ExcludedFolders, MaxSaves)
        #If it's a file and it doesn't exist on the local machine, we copy it onto the local machine
        #NOTE we don't need to check for saves specifically since the local file check already accounts for when saves exist on both the server and the local machine.
        elif serverfile not in LocalFiles and serverfile not in ExcludedFolders:
            print("File missing from client...")
            print("Copying missing file to client...")
            print("Source: " + ServerPath + '/' + serverfile)
            print("Destination: " + LocalPath + '/' + serverfile)
            shutil.copy(ServerPath + '/' + serverfile, LocalPath + '/' + serverfile)
            print("File successfully copied!")
    return 0
 

def CheckForUpdatedROMSaves(MaxSaves):
    ROMSaves = SQLGetEntry('ROMSaves', {}, [])
    for SaveFile in ROMSaves:
        TempSplit = SaveFile['FileName'].split('.')
        Extension = TempSplit[-1]
        NoExt = TempSplit[0]
        ServerTimestamp = SQLGetMinMax('ROMSaveTimestamps','Timestamp',{'FileName':SaveFile['FileName']})[0]['MaxVal']
        TrueTimestamp = GetTimeModified('./ROMs/' + SaveFile['SubFolder'] + '/' + SaveFile['FileName'])
        if TrueTimestamp > ServerTimestamp:
            print('SteamSync local ROM Save is newer than most recent backup...')
            print('Backing up ROM Save: ' + SaveFile['FileName'])
            os.makedirs('./ROMSaves/' + SaveFile['SubFolder'] + '/' + NoExt + '/' + datetime.datetime.fromtimestamp(TrueTimestamp).strftime('%Y-%m-%d_%H%M%S'), exist_ok=True)
            shutil.copy('./ROMs/' + SaveFile['SubFolder'] + '/' + SaveFile['FileName'],  './ROMSaves/' + SaveFile['SubFolder'] + '/' + NoExt + '/' + datetime.datetime.fromtimestamp(TrueTimestamp).strftime('%Y-%m-%d_%H%M%S') +'/')
            SQLUpdateEntry('ROMSaves', { 'Timestamp': TrueTimestamp }, { 'SubFolder': SaveFile['SubFolder'], 'FileName': SaveFile['FileName'] })
            SQLCreateEntry('ROMSaveTimestamps', {'FileName': SaveFile['FileName'], 'Timestamp':TrueTimestamp })
            SaveTimestampsList = SQLGetEntry('ROMSaveTimestamps', {'FileName': SaveFile['FileName'] })
            if len(SaveTimestampsList) > MaxSaves:
                print('Maximum number of saves reached...')
                OldestTimestamp = SQLGetMinMax('ROMSaveTimestamps','Timestamp', { 'FileName': SaveFile['FileName'] }, True)[0]['MinVal']
                print('Deleting Oldest ROM Save Directory with timestamp: ' + datetime.datetime.fromtimestamp(OldestTimestamp).strftime('%Y-%m-%d_%H%M%S'))
                SQLDeleteEntry('ROMSaveTimestamps',{'Timestamp': OldestTimestamp, 'FileName': SaveFile['FileName'] })
                if os.path.isdir('./ROMSaves/' + SaveFile['SubFolder'] + '/' + NoExt + '/' + datetime.datetime.fromtimestamp(OldestTimestamp).strftime('%Y-%m-%d_%H%M%S')):
                    shutil.rmtree('./ROMSaves/' + SaveFile['SubFolder'] + '/' + NoExt + '/' + datetime.datetime.fromtimestamp(OldestTimestamp).strftime('%Y-%m-%d_%H%M%S'))
                print('ROM Save successfully deleted!')
    return 0                                       
        


#Function to convert PCGW data into a usable filepath
def GetFilepaths(ApplicationDict, UnprocessedPath):
    Exclusions = []
    ExclusionSQLData = SQLGetEntry('FileExclusions',{'AppID':ApplicationDict['AppID']},[])
    if len(ExclusionSQLData) > 0:
        for entry in ExclusionSQLData:
            Exclusions.append(entry['Filename'])
    #Variable initialization
    SubstitutionDict = {}
    ReturnPaths = []
    #Initialize our UID substitution since we know we'll need to check for existing files or folders for our UIDFinder function instead of a determined value, regardless of system or game platform
    SubstitutionDict['\{\{p\|uid\}\}'] = '{ UID }'
    #Generate our substitution dictionary if we're looking for a linux save
    if ApplicationDict['SystemPlatform'] == 'Linux':
        SubstitutionDict['\{\{p\|linuxhome\}\}'] = ApplicationDict['Home']
        SubstitutionDict['\{\{p\|xdgdatahome\}\}'] = ApplicationDict['Home'] + '/.local/share/'
        SubstitutionDict['\{\{p\|xdgconfighome\}\}'] = ApplicationDict['Home'] + '/.config/'
        SubstitutionDict['\{\{p\|steam\}\}'] = ApplicationDict['SteamPath']
        SubstitutionDict['~'] = ApplicationDict['Home']
    #Generate our substitution dictionary if we're looking for a windows game save on a linux system
    #For some reason steam doesn't always correctly write SystemPlatform and GamePlatform values to the app_manifest
    if ApplicationDict['SystemPlatform'] != ApplicationDict['GamePlatform'] or os.path.isdir(ApplicationDict['SteamPath'] + '/steamapps/compatdata/' + ApplicationDict['AppID']):
        SubstitutionDict['\{\{p\|localappdata\}\}'] = ApplicationDict['ProtonPath'] + 'pfx/drive_c/users/steamuser/AppData/Local/'
        SubstitutionDict['\{\{p\|appdata\}\}'] = ApplicationDict['ProtonPath'] + 'pfx/drive_c/users/steamuser/AppData/Roaming/'
        SubstitutionDict['\{\{p\|userprofile\\Documents\}\}'] = ApplicationDict['ProtonPath'] + 'pfx/drive_c/users/steamuser/My Documents/'
        SubstitutionDict['\{\{Path\|localappdata\}\}'] = ApplicationDict['ProtonPath'] + 'pfx/drive_c/users/steamuser/AppData/Local/'
        SubstitutionDict['\{\{p\|userprofile\}\}'] = ApplicationDict['ProtonPath'] + 'pfx/drive_c/users/steamuser/'
        SubstitutionDict['\{\{p\|programdata\}\}'] = ApplicationDict['ProtonPath'] + 'pfx/drive_c/programdata/'
        SubstitutionDict['\{\{p\|userprofile'] = ApplicationDict['ProtonPath'] + 'pfx/drive_c/users/steamuser/'
        SubstitutionDict['\{\{p\|username\}\}'] = ApplicationDict['ProtonPath'] + 'pfx/drive_c/users/steamuser/'
    #NOTE This is currently unused
    #Placeholder for potential usage on Windows
    else:
        SubstitutionDict['\{\{p\|localappdata\}\}'] = ''
        SubstitutionDict['\{\{p\|appdata\}\}'] = ''
        SubstitutionDict['\{\{p\|userprofile\\Documents\}\}'] = ''
        SubstitutionDict['\{\{Path\|localappdata\}\}'] = ''
        SubstitutionDict['\{\{p\|userprofile\}\}'] = ''
        SubstitutionDict['\{\{p\|userprofile'] = ''
    #NOTE this is a rare situation where the game save is stored in the windows registry
    #Currently unsure of how to get the registry value in proton or windows
    #We substitute in a generic value, but will not use it for anything currently
    SubstitutionDict['\{\{p\|hkcu\}\}'] = '{ HKEY CURRENT USER }'
    #substitute in the installation directory, regardless of host system
    SubstitutionDict['\{\{p\|game\}\}'] = ApplicationDict['InstallDir']
    #Process all of our substitutions
    for substitution in SubstitutionDict:
        SubVar = re.compile(substitution,re.IGNORECASE)
        UnprocessedPath = SubVar.sub(SubstitutionDict[substitution],UnprocessedPath)
    #If there is a | character in our path, we need to split it to get the multiple different paths we're checking
    ProcessedPaths = UnprocessedPath.split('|')
    #For each path we got from our previous split
    for path in ProcessedPaths:
        #We need to remove our double } characters, swap our \ characters with /s for linux systems, and replace any double /s with single /s
        path = path.replace('\\','/').replace('//','/').replace('}}','')
        #Call our UID finder on our current path if we have any UIDs we need to find before we add it to our return list
        if '{ UID }' in path:
            FullPaths = UIDFinder(path,Exclusions)
            if len(FullPaths) == 1:
                ReplacementPath = ''
                TempSplit = path.split('{ UID }')
                for temppath in TempSplit:
                    if temppath != TempSplit[-1]:
                        ReplacementPath = ReplacementPath + '/' + temppath
                ReplacementPath = ReplacementPath.replace('////','/').replace('///','/').replace('//','/')
                FullPaths[0] = FullPaths[0].replace('////','/').replace('///','/').replace('//','/')
                Suffix = '{ UID }' + FullPaths[0].replace(ReplacementPath,'')
                ReturnPaths.extend(FullPaths)
                ReturnPaths.append(Suffix)
            else:
                ReturnPaths.extend(FullPaths)
            
        #Otherwise we just append our current path to our return list
        else:
            ReturnPaths.append(path)
    return ReturnPaths

#Helper function to get our filepaths for each system's save types we find
def ParseSaveData(ApplicationDict, SaveDataDict):
    ReturnList = []
    for SaveType in SaveDataDict:
        ReturnList.extend(GetFilepaths(ApplicationDict,SaveDataDict[SaveType]))
    return ReturnList

#Helper function to replace our relative path readable by any client with the current client's absolute path
def GetAbsolutePath(PathDict, Path):
    ReturnPath = ''
    AbsolutePath = Path
    if '{ PROTON PREFIX }' in AbsolutePath:
        AbsolutePath = AbsolutePath.replace('{ PROTON PREFIX }',PathDict['ProtonPath'])
    if '{ PATH TO GAME }' in AbsolutePath:
        AbsolutePath = AbsolutePath.replace('{ PATH TO GAME }',PathDict['InstallDir'])
    if '{ PATH TO STEAM }' in AbsolutePath:
        AbsolutePath = AbsolutePath.replace('{ PATH TO STEAM }',PathDict['SteamPath'])
    if '{ HOME }' in AbsolutePath:
        AbsolutePath = AbsolutePath.replace('{ HOME }',PathDict['Home'])
    ReturnPath = AbsolutePath
    return ReturnPath

#Helper function to replace our absolute paths on the current client with a relative path readable by any client
def GetRelativePath(PathDict, Path):
    ReturnPath = ''
    RelativePath = Path
    if PathDict['ProtonPath'] in RelativePath and PathDict['ProtonPath'] != '':
        RelativePath = RelativePath.replace(PathDict['ProtonPath'],'{ PROTON PREFIX }' + '/')
    if PathDict['InstallDir'] in RelativePath:
        RelativePath = RelativePath.replace(PathDict['InstallDir'],'{ PATH TO GAME }')
    if PathDict['SteamPath'] in RelativePath:
        RelativePath = RelativePath.replace(PathDict['SteamPath'],'{ PATH TO STEAM }')
    if PathDict['Home'] in RelativePath:
        RelativePath = RelativePath.replace(PathDict['Home'],'{ HOME }')
    ReturnPath = RelativePath
    return ReturnPath

#Function to get PCGW Data from PC Gaming Wiki
def GetPCGWData(ApplicationDict):
    #Variable initialization
    ReturnPaths = []
    ReturnDict = {}
    ReturnDict['SteamCloud'] = False
    ReturnDict['Found'] = False
    #Hardcoded WikiURL to pull json data from PC Gaming Wiki
    WikiURL = "https://www.pcgamingwiki.com/w/api.php?action=cargoquery&tables=Infobox_game,Cloud&fields=Cloud.Steam,Cloud.GOG_Galaxy,Cloud.Discord,Cloud.Epic_Games_Launcher,Cloud.EA_Desktop,Cloud.OneDrive,Cloud.Ubisoft_Connect,Cloud.Xbox,Infobox_game._pageID=PageID,Infobox_game._pageName=Page,Infobox_game.Developers,Infobox_game.Released,Infobox_game.Cover_URL&join_on=Infobox_game._pageID=Cloud._pageID&where=Infobox_game.Steam_AppID%20HOLDS%20%22" + ApplicationDict['AppID'] + "%22&format=json"
    #Calling requests to get the page content
    JSONData = requests.get(WikiURL)
    RawSaveDataDict = {}
    Cargo = {}
    LinuxSave = False
    WindowsSave = False
    SteamSave = False
    #Make sure our request returned something for us to unpack
    if 'cargoquery' in JSONData.json():
        #Parse the json dotatype for our data
        Cargo = JSONData.json()['cargoquery']
        #Make sure that the page we requestsed exists
        if len(Cargo) > 0:
            #Check for steam cloud integration
            if Cargo[0]['title']['Steam'] == 'true':
                ReturnDict['SteamCloud'] = True
            else:
                ReturnDict['SteamCloud'] = False
            #Get our PC Gaming Wiki Page ID from our cargo query earlier
            PageID = Cargo[0]['title']['PageID']
            #Make a new request to get the full page contents
            RawWikiData = requests.get("https://www.pcgamingwiki.com/w/api.php?action=parse&format=json&pageid=" + PageID + "&prop=wikitext")
            #If our new request returned some type of content
            if RawWikiData != '':
                #We want the entirety of the text data from the page
                ParsedWikiData = RawWikiData.json()['parse']['wikitext']['*']
                #use a regular expression to find our Save Game Data Location section of the wiki text
                RawSaveLocations = re.search('===Save game data location===[\S\n ]+?===.+===',ParsedWikiData)
                #If we found a save game data location in our text
                if RawSaveLocations:
                    #We want to get the raw data for any of the individual platforms we can find
                    #NOTE macOS is ignored since we currently don't care about macOS compatibility and only need the Windows, Steam and Linux save sections as a result
                    RawWindowsSave = re.search("Windows\|.+\}\}",RawSaveLocations.group())
                    RawSteamSave = re.search("Steam\|.+\n",RawSaveLocations.group())
                    RawLinuxSave = re.search("Linux\|.+\n",RawSaveLocations.group())
                    #Parse the remaining text to get the actual usable paths from our regular expression search
                    if RawWindowsSave:
                        WindowsSave = re.search("\{\{.+\}\}", RawWindowsSave.group())
                        if WindowsSave:
                            RawSaveDataDict['WindowsSave'] = WindowsSave.group()
                    if RawSteamSave:
                        SteamSave = re.search("\{\{.+\}\}", RawSteamSave.group())
                        if SteamSave:
                            RawSaveDataDict['SteamSave'] = SteamSave.group()
                    if RawLinuxSave:
                        if RawLinuxSave.group()[6] == '~':
                            LinuxSave = re.search('\~.+\}\}',RawLinuxSave.group())
                        else:
                            LinuxSave = re.search('\{\{.+\}\}',RawLinuxSave.group())
                        if LinuxSave:
                            RawSaveDataDict['LinuxSave'] = LinuxSave.group()
    #We make sure we found at least one usable save from any of the platforms before continuing
    if (LinuxSave or SteamSave or WindowsSave): 
        #We call our parse save data function to take the raw text from PCGW and turn it into a usable file path
        SaveDataList = ParseSaveData(ApplicationDict, RawSaveDataDict)
        #We call our verifylocaldata function with our new save paths, so we can find which files exist that we potentially want to backup
        VerifiedSaveDataDict = VerifyLocalData(SaveDataList)
        #Initialize our return values
        ReturnDict['AbsoluteSavePaths'] = []
        ReturnDict['RelativeSavePaths'] = []
        ReturnDict['TimeModified'] = 0
        #For each 
        for entry in VerifiedSaveDataDict:
            #We only care about the entries that we found a matching local file or folder for
            if entry['Found']:
                #We flag that there is at least one found save
                if '{ UID }' not in entry['AbsolutePath']:
                    ReturnDict['Found'] = True
                #We want to treat the overall time modified of the save as the most recent time modified of any of our found saves
                if entry['TimeModified'] > ReturnDict['TimeModified']:
                    ReturnDict['TimeModified'] = entry['TimeModified']
                #We want to make sure we return all found absoltue paths and relative paths
                #NOTE This ignores unfound relative paths, meaning that if a save is located in a different location than was registered before it will be ignored
                if entry['AbsolutePath'] not in ReturnDict['AbsoluteSavePaths']:
                    ReturnDict['AbsoluteSavePaths'].append(entry['AbsolutePath'])
                RelativePath = GetRelativePath(ApplicationDict,entry['AbsolutePath'])
                if RelativePath not in ReturnDict['RelativeSavePaths']:
                    ReturnDict['RelativeSavePaths'].append(RelativePath)
        #If we didn't find any paths that exist, we return all the paths since we know we don't need to sync/backup anything
        if not ReturnDict['Found']:
            for entry in SaveDataList:
                if entry not in ReturnDict['AbsoluteSavePaths']:
                    ReturnDict['AbsoluteSavePaths'].append(entry)
                RelativePath = GetRelativePath(ApplicationDict, entry)
                if RelativePath not in ReturnDict['RelativeSavePaths']:
                    ReturnDict['RelativeSavePaths'].append(RelativePath)
        #MAke sure to bring over our needed values for later from our input value
        if 'AppID' in ApplicationDict:
            ReturnDict['AppID'] = ApplicationDict['AppID']
        if 'ProtonPath' in ApplicationDict:
            ReturnDict['ProtonPath'] = ApplicationDict['ProtonPath']
        if 'InstallDir' in ApplicationDict:
            ReturnDict['InstallDir'] = ApplicationDict['InstallDir']
    return ReturnDict


#Function to help decide how to proceed when syncing a game save
def SyncGame(AppID, PathToSteam, LibraryPath, ClientID, IncludeSteamCloud, MaxSaves, HomeDir):
    #We need to make sure our app manifest file exists before attempting to open it
    if os.path.isfile(LibraryPath + '/steamapps/appmanifest_' + AppID + '.acf'):
        #Check for the application's existince in our database
        AppSQLData = SQLGetEntry('SteamApps', {'AppID': AppID}, [])
        #Load the vdf data file from our application's library
        AppVDFData = vdf.load(open(LibraryPath + '/steamapps/appmanifest_' + AppID + '.acf'))
        #We get the install directory of the application knowing it's located in steamapps/common/
        InstallDir = LibraryPath + '/steamapps/common/' + AppVDFData['AppState']['installdir']
        #NOTE these are variables eing initialized instead of using actual detection for OS, we always assume we're running on a linux client.
        ProtonPath = ''
        SystemPlatform = 'Linux'
        GamePlatform = 'Linux'
        ProtonGame = False
        RelativePath = ''
        RelativeSQLData = SQLGetEntry('RelativeSavePaths', {'AppID': AppID})
        if len(RelativeSQLData) > 0:
            RelativePath = RelativeSQLData[0]['RelativePath']
        if '{ PROTON PREFIX }' in RelativePath:
            ProtonGame = True
        #We detect whether the game is running through proton via the platform_override_dest value
        if 'platform_override_dest' in AppVDFData['AppState']['UserConfig']:
            if AppVDFData['AppState']['UserConfig']['platform_override_dest'] == 'linux' and AppVDFData['AppState']['UserConfig']['platform_override_source'] == 'windows':
                GamePlatform = 'Windows'
            else:
                GamePlatform = 'Linux'
        #If we can detect the game is running through proton, we need to keep track of the path to the proton prefix
        if GamePlatform != SystemPlatform or os.path.isdir(LibraryPath + '/steamapps/compatdata/' + AppID + '/') or ProtonGame:
            ProtonPath = LibraryPath + '/steamapps/compatdata/' + AppID +'/'
        #Data dictionary initialization and grabbing the data we can fill in currently
        GameDataDict = {}
        GameDataDict['AppID'] = AppID
        GameDataDict['ProtonPath'] = ProtonPath
        GameDataDict['InstallDir'] = InstallDir
        GameDataDict['Home'] = HomeDir
        GameDataDict['Title'] = AppVDFData['AppState']['name']
        GameDataDict['SystemPlatform'] = SystemPlatform
        GameDataDict['GamePlatform'] = GamePlatform
        GameDataDict['SteamPath'] = PathToSteam
        #These flags are for games that have been initialized in our database, but are still missing information.
        NeedPCGWFlag = False
        NeedNewPathFlag = False
        #We attempt to get our relative path, our local save information, and our prefixes from the database from the sql database
        RelativePaths = SQLGetEntry('RelativeSavePaths',{ 'AppID': AppID },[])
        ClientSaveSQLData = SQLGetEntry('ClientSaveInfo', { 'AppID': AppID, 'ClientID': ClientID }, [])
        SavePrefixes = SQLGetEntry('ClientPrefixes', { 'AppID': AppID, 'ClientID': ClientID }, [])
        #We check if our app exists in the SQL Data or not
        if len(AppSQLData) > 0:
            #We make sure that the application isn't set to always skipped
            if not AppSQLData[0]['AlwaysSkipped']:
                #We check if we have a relative save path to reference in the database, if not we know we need to get our save path information from PCGW
                if len(RelativePaths) == 0:
                    NeedPCGWFlag = True
                #Extra data sanitation check, if for some reason a relative save path entry was created but was never actually initialized
                elif not RelativePaths[0]['RelativePath']:
                    NeedPCGWFlag = True
            #We check if there is save data information tied to this client
            elif len(ClientSaveSQLData) > 0:
                #We check if we flagged this game to be skipped on this client
                if not ClientSaveSQLData[0]['Skipped']:
                    #We know we need to get a new path if we don't have a prefix for this client
                    if len(SavePrefixes) == 0:
                        NeedNewPathFlag = True
                    #Extra data sanity check in case sql values get initialized without actual data
                    elif not ClientSaveSQLData[0]['InstallPath']:
                        NeedNewPathFlag = True
                    elif len(SavePrefixes > 0):
                        if not SavePrefixes[0]['Prefix']:
                            NeedNewPathFlag = True 
        #We found the application present in our database and we haven't flagged it to always be skipped
        if len(AppSQLData) != 0 and AppSQLData[0]['AlwaysSkipped'] == 0 and not NeedPCGWFlag:
            #We pull the timestamp our most recently synced save from the database
            MostRecentSaveTime = AppSQLData[0]['MostRecentSaveTime']
            #Attempt to pull information on the client's most recent save information
            #Get the game's title from our SQL Database
            GameTitle = SQLGetEntry('SteamApps',{'AppID': AppID }, ['Title'])[0]['Title']
            #Variable initialization for use later
            Suffixes = []
            SaveDict = {}
            #If our client is in the database and isn't skipped
            if len(ClientSaveSQLData) > 0 and ClientSaveSQLData[0]['Skipped'] == 0 and not NeedNewPathFlag:
                #Pull the SQL on the client into our more easily interprateable prefix and suffixes
                PathPrefix = SQLGetEntry('ClientPrefixes',{'ClientID':ClientID, 'AppID':AppID}, [])[0]['Prefix']
                SuffixSQLData = SQLGetEntry('ClientSuffixes',{'ClientID':ClientID, 'AppID':AppID}, [])
                ServerSuffixes = SQLGetEntry('ClientSuffixes',{'AppID': AppID })
                KnownSuffixRoots = []
                if len(SuffixSQLData) > 0:
                    for row in SuffixSQLData:
                        Suffixes.append(row['Suffix'])
                for TempSuffix in ServerSuffixes:
                    if TempSuffix['Suffix'] not in Suffixes:
                        Suffixes.append(TempSuffix['Suffix'])
                        SQLCreateEntry('ClientSuffixes', {'ClientID': ClientID, 'AppID': AppID, 'Suffix': TempSuffix['Suffix'] })
                KnownSuffixIDs = []
                PostSuffixFolders = []
                for suffix in Suffixes:
                    TempSplit = suffix.split('/')
                    SuffixID = ''
                    if len(TempSplit) > 1:
                        if TempSplit[0] != '':
                            SuffixID = TempSplit[0]
                        else:
                            SuffixID = TempSplit[1]
                    KnownSuffixIDs.append(SuffixID)
                    postsuffixid = suffix.replace(SuffixID,'')
                    if postsuffixid not in PostSuffixFolders:
                        PostSuffixFolders.append(suffix.replace(SuffixID,''))
                if os.path.isdir(PathPrefix):
                    PotentialSuffixes = os.listdir(PathPrefix)
                    for newsuffixid in PotentialSuffixes:
                        if newsuffixid not in KnownSuffixIDs:
                            for subfolders in PostSuffixFolders:
                                newsuffix = newsuffixid + '/' + subfolders
                                if os.path.isfile(PathPrefix + '/' + newsuffix) or os.path.isdir(PathPrefix + '/' + newsuffix):
                                    SQLCreateEntry('ClientSuffixes',{'ClientID':ClientID, 'AppID': AppID, 'Suffix': newsuffix})
                                    Suffixes.append(newsuffix)
                #We need to get our local save timestamp to determine what to do with this client
                LocalSaveTime = 0
                #If we have more than one path we need to check
                if len(Suffixes) > 0:
                    #For every path we need to check
                    for suffix in Suffixes:
                        #Pull the timestamp from the path we're currently looking at
                        LocalTimestamp = GetTimeModified(PathPrefix + suffix)
                        #Compare the timestamp to our current most recent time modified
                        if LocalTimestamp > LocalSaveTime:
                            #Set the local timestamp to our new most recent timestamp
                            LocalSaveTime = LocalTimestamp
                #Otherwise we know we only need the timestamp from one path
                else:                
                    LocalSaveTime = GetTimeModified(PathPrefix)
                #If this client has a more recent save than what's backed up
                if LocalSaveTime > MostRecentSaveTime:
                    #Terminal output for debugging
                    print('==========================================================')
                    print("More recent save than registered to server located!")
                    print("Title: " + GameDataDict['Title'])
                    print("AppID: " + AppID)
                    #Compile our SaveDict dictionary which has everything we should need to copy the save to the server.
                    SaveDict['Timestamp'] = LocalSaveTime
                    SaveDict['Prefix'] = PathPrefix
                    SaveDict['Suffixes'] = Suffixes
                    SaveDict['AppID'] = AppID
                    SaveDict['ProtonPath'] = ProtonPath
                    SaveDict['SteamPath'] = PathToSteam
                    SaveDict['Home'] = HomeDir
                    SaveDict['InstallDir'] = InstallDir
                    #Copy the save to the database server using the information from the dictionary we just created
                    CopySaveToServer(SaveDict, MaxSaves)
                    #Update our SQL database with information on the new newest save
                    SQLUpdateEntry('ClientSaveInfo',{'MostRecentSaveTime':LocalSaveTime},{'AppID':AppID,'ClientID':ClientID})
                    SQLUpdateEntry('SteamApps',{'MostRecentSaveTime':LocalSaveTime},{'AppID':AppID})
                    #Create a SQL entry for our new save timestamp
                    SQLCreateEntry('SaveTimestamps',{'AppID':AppID,'Timestamp':LocalSaveTime})
                #If the time modified on the server is more recent than the local file's time modified timestamp
                elif MostRecentSaveTime > LocalSaveTime:
                    #Terminal output for debugging
                    print('==========================================================')
                    print("More recent save on server than locally stored located!")
                    print("Title: " + GameDataDict['Title'])
                    print("AppID: " + AppID)
                    #Compile our SaveDict dictionary which has everything we should need to copy from the server to the current client
                    SaveDict['Timestamp'] = MostRecentSaveTime
                    SaveDict['Prefix'] = PathPrefix
                    SaveDict['Suffixes'] = Suffixes
                    SaveDict['AppID'] = AppID
                    SaveDict['ProtonPath'] = ProtonPath
                    SaveDict['SteamPath'] = PathToSteam
                    SaveDict['Home'] = HomeDir
                    SaveDict['InstallDir'] = InstallDir
                    #Copy the save from the server to the client using our dictionary we just created
                    CopySaveFromServer(SaveDict)
                    #Update our SQL entry for the client with the new most recent save time
                    SQLUpdateEntry('ClientSaveInfo',{'MostRecentSaveTime':MostRecentSaveTime},{'AppID':AppID,'ClientID':ClientID})
            #This means that the client hasn't been synced for this game, but it exists in the database already
            elif len(ClientSaveSQLData) == 0 or NeedNewPathFlag:
                #Get our relative save path from our SQL Database 
                RelativePathsSQLData = SQLGetEntry('RelativeSavePaths',{'AppID':AppID},['RelativePath'])
                #Initialize values for use later
                RelativePaths = []
                FoundPaths = []
                AbsoluteSavePaths = []
                LocalSaveTime = 0
                #Get a list of our relative paths from our dictionary objects
                for row in RelativePathsSQLData:
                    RelativePaths.append(row['RelativePath'])
                #We translate our relative paths into an absolute path using our dictionary we created earlier
                for path in RelativePaths:
                    AbsoluteSavePaths.append(GetAbsolutePath(GameDataDict, path))
                #We then verify our expected absolute paths to determine which data exists locally for us to check against the server's savedata
                VerifiedDataDict = VerifyLocalData(AbsoluteSavePaths)
                #Further verification, to cut down on which paths exist and which ones don't locally
                for entry in VerifiedDataDict:
                    if entry['Found']:
                        FoundPaths.append(entry['AbsolutePath'])
                #We need to check whether there are multiple filepaths we're checking the timestamp of or just one
                if len(FoundPaths) > 1:
                    #Get our filepath prefixes and suffixes from our FoundPaths value
                    (Prefix, Suffixes) = GetPrefixAndSuffixes(FoundPaths)
                    #For each suffix we have
                    for suffix in Suffixes:
                        #Load the timestamp of that filepath into a temporary value
                        TempTimestamp = GetTimeModified(Prefix + suffix)
                        #if it's greater than our baseline value
                        if TempTimestamp > LocalSaveTime:
                            #We set our baseline value equal to our temporary value
                            LocalSaveTime = TempTimestamp
                #if we only have one path that we're checking against
                elif len(FoundPaths) == 1:
                    #We then map our FoundPath to our prefix
                    Prefix = FoundPaths[0]
                    #And initialize an empty suffix if needed
                    Suffixes = ['']
                    #We only have one value to check, so we can assume that the baseline value is always the timestamp of our prefix
                    LocalSaveTime = GetTimeModified(Prefix)
                i = 0
                #if the client has a save that is more recent than the server
                #the and statement is a safety check needed for an edge case where a user has installed a game that does use proton but 
                if LocalSaveTime > MostRecentSaveTime:
                    response = ''
                    #We now know that the client's save game is newer than the servers
                    #We prompt the user for how to proceed
                    while(response not in ['1','2','3']):
                        print('==========================================================')
                        print('Unsynced Client has more recent save than server')
                        print('Game Title: ' + GameDataDict['Title'])
                        print('Please Select an option:')
                        print('1. Overwrite server save with local save')
                        print('2. Overwrite local save with server save')
                        print('3. Do not sync this game save with this client')
                        response = input('Type the corresponding number (1,2,3): ')
                    #We treat this as an update to the game save on the server
                    if response == '1':
                        #Terminal output for debugging
                        print("More recent save than registered to server located!")
                        print("Title: " + GameDataDict['Title'])
                        print("AppID: " + AppID)
                        #Compile our SaveDict Dictionary which has everything we should need to copy the save to our server
                        SaveDict['Timestamp'] = LocalSaveTime
                        SaveDict['Prefix'] = Prefix
                        SaveDict['Suffixes'] = Suffixes
                        SaveDict['AppID'] = AppID
                        SaveDict['ProtonPath'] = ProtonPath
                        SaveDict['SteamPath'] = PathToSteam
                        SaveDict['Home'] = HomeDir
                        SaveDict['InstallDir'] = InstallDir
                        #Copy the save to the server with the dictionary we just created
                        CopySaveToServer(SaveDict, MaxSaves)
                        #Create SQL Entries for the newly synced save file, setting it as the new most recent save in our database 
                        if len(ClientSaveSQLData) > 0:
                            SQLUpdateEntry('ClientSaveInfo',{'Skipped': 0, 'InstallPath': InstallDir, 'MostRecentSaveTime': LocalSaveTime, 'ProtonPrefix': ProtonPath.replace('\'','\'\'')}, {'AppID': AppID, 'ClientID': ClientID })
                        else:
                            SQLCreateEntry('ClientSaveInfo',{'AppID': AppID, 'ClientID': ClientID, 'Skipped': 0, 'InstallPath': InstallDir, 'MostRecentSaveTime': LocalSaveTime, 'ProtonPrefix': ProtonPath.replace('\'','\'\'')})
                        if len(SavePrefixes) > 0: 
                            SQLUpdateEntry('ClientPrefixes',{'Prefix': Prefix.replace('\'','\'\'')}, { 'AppID': AppID, 'ClientID': ClientID })
                        else:
                            SQLCreateEntry('ClientPrefixes',{'AppID': AppID, 'ClientID': ClientID, 'Prefix': Prefix.replace('\'','\'\'')})
                        SQLCreateEntry('SaveTimestamps',{'AppID': AppID, 'Timestamp': LocalSaveTime})
                        SQLUpdateEntry('SteamApps',{'MostRecentSaveTime': LocalSaveTime}, {'AppID': AppID })
                        if len(Suffixes) > 0:
                            for suffix in Suffixes:
                                SQLCreateEntry('ClientSuffixes',{'AppID': AppID, 'ClientID': ClientID, 'Suffix': suffix})
                    #we treat this as an update to the game save on the client
                    elif response == '2':
                        #Terminal output for debugging
                        print("More recent save on server than locally stored located!")
                        print("Title: " + GameDataDict['Title'])
                        print("AppID: " + AppID)
                        #Compile our SaveDict Dictionary which has everything we should need to copy the save to the client
                        SaveDict['Timestamp'] = MostRecentSaveTime
                        SaveDict['Prefix'] = Prefix
                        SaveDict['Suffixes'] = Suffixes
                        SaveDict['AppID'] = AppID
                        SaveDict['ProtonPath'] = ProtonPath
                        SaveDict['SteamPath'] = PathToSteam
                        SaveDict['Home'] = HomeDir
                        SaveDict['InstallDir'] = InstallDir
                        #Copy the save from our save using the dictionary we just created
                        CopySaveFromServer(SaveDict)
                        #Create SQL Entries for the client now that it's been synced
                        if len(ClientSaveSQLData) > 0:
                            SQLUpdateEntry('ClientSaveInfo',{'Skipped': 0, 'InstallPath': InstallDir.replace('\'','\'\''), 'MostRecentSaveTime': MostRecentSaveTime, 'ProtonPrefix': ProtonPath.replace('\'','\'\'')}, {'AppID': AppID, 'ClientID': ClientID})
                        else:
                            SQLCreateEntry('ClientSaveInfo',{'AppID': AppID, 'ClientID': ClientID, 'Skipped': 0, 'InstallPath': InstallDir.replace('\'','\'\''), 'MostRecentSaveTime': MostRecentSaveTime, 'ProtonPrefix': ProtonPath.replace('\'','\'\'')})
                        if len(SavePrefixes) > 0:
                            SQLUpdateEntry('ClientPrefixes',{'Prefix':Prefix.replace('\'','\'\'')}, {'AppID': AppID, 'ClientID': ClientID })
                        else:
                            SQLCreateEntry('ClientPrefixes',{'AppID': AppID, 'ClientID': ClientID, 'Prefix':Prefix.replace('\'','\'\'')})
                        #create suffixes entries if we have suffixes that exist in our list
                        #NOTE there should be multiple checks to make it possible to proceed without suffixes if for some reason it was never initialized
                        if len(Suffixes) > 0:
                            for suffix in Suffixes:
                                SQLCreateEntry('ClientSuffixes',{'AppID': AppID, 'ClientID': ClientID, 'Suffix':suffix.replace('\'','\'\'')})
                    #We add the client's save to the SQL server and mark it as skipped
                    elif response == '3':
                        SQLCreateEntry('ClientSaveInfo',{'AppID': AppID, 'ClientID': ClientID, 'Skipped': 1})
                #If the local save time is less up to date than the save on the server
                else:
                    #We initialize new variables for our absolute paths
                    #NOTE We cannot reference found paths since we may not necessarily have found any local data to compare the timestamp too
                    AbsolutePaths = []
                    #Convert our expected relative paths into local absolute paths
                    for path in RelativePaths:
                        AbsolutePaths.append(GetAbsolutePath(GameDataDict,path))
                    #Split our paths into prefixes and suffixes if we have more than one path to reference from
                    if len(AbsolutePaths) > 1:
                        (Prefix, Suffixes) = GetPrefixAndSuffixes(AbsolutePaths)
                    #If we only have one file/directory path we're syncing, we can set the prefix as the value and create an empty suffixes value for our copy function
                    else:
                        Prefix = AbsolutePaths[0]
                        Suffixes = ['']
                    #Terminal output for debugging
                    print('==========================================================')
                    print("More recent save on server than locally stored located!")
                    print("Title: " + GameDataDict['Title'])
                    print("AppID: " + AppID)
                    #Compile a new dictionary that should have everything we need to copy a save from the server 
                    SaveDict['Timestamp'] = MostRecentSaveTime
                    SaveDict['Prefix'] = Prefix
                    SaveDict['Suffixes'] = Suffixes
                    SaveDict['AppID'] = AppID
                    SaveDict['ProtonPath'] = ProtonPath
                    SaveDict['SteamPath'] = PathToSteam
                    SaveDict['Home'] = HomeDir
                    SaveDict['InstallDir'] = InstallDir
                    #Copy the save from the server using our newly created dictionary
                    CopySaveFromServer(SaveDict)
                    #initialize SQL data for our newly synced client
                    if len(ClientSaveSQLData) > 0:
                        SQLUpdateEntry('ClientSaveInfo',{'Skipped':0, 'InstallPath':InstallDir.replace('\'','\'\''), 'MostRecentSaveTime':MostRecentSaveTime, 'ProtonPrefix':ProtonPath.replace('\'','\'\'')}, { 'AppID': AppID, 'ClientID': ClientID })
                    else:
                        SQLCreateEntry('ClientSaveInfo',{'AppID':AppID, 'ClientID':ClientID, 'Skipped':0, 'InstallPath':InstallDir.replace('\'','\'\''), 'MostRecentSaveTime':MostRecentSaveTime, 'ProtonPrefix':ProtonPath.replace('\'','\'\'')})
                    if len(SavePrefixes) > 0:
                        SQLUpdateEntry('ClientPrefixes',{'Prefix':Prefix.replace('\'','\'\'')}, { 'AppID': AppID, 'ClientID': ClientID })
                    else:
                        SQLCreateEntry('ClientPrefixes',{'AppID':AppID, 'ClientID':ClientID, 'Prefix':Prefix.replace('\'','\'\'')})
                    for suffix in Suffixes:
                        SQLCreateEntry('ClientSuffixes',{'AppID':AppID, 'ClientID':ClientID, 'Suffix':suffix.replace('\'','\'\'')})
        #If we have no record of this application in the database
        elif len(AppSQLData) == 0 or NeedPCGWFlag:
            #We need to pull information from PC Gaming Wiki since we have no information to reference from the SQL database
            PCGWDict = GetPCGWData(GameDataDict)
            ContinueFlag = False
            #Pull the title from our vdf data since it's less intensive than parsing the PCGW Text or making a new request
            PCGWDict['Title'] = AppVDFData['AppState']['name']
            #We only proceed if the PCGW entry exists and we either are including steam cloud or it's not a steam cloud game
            if PCGWDict['Found'] and (PCGWDict['SteamCloud'] == False or (PCGWDict['SteamCloud'] == True and IncludeSteamCloud)):
                #Terminal output for debugging
                print('==========================================================')
                print('Unregistered Game\'s Local Save Data Found!')
                print('Title: ' + PCGWDict['Title'])
                print('AppID: ' + AppID)
                Suffixes = []
                #SQL Entry creation of our newly found application data
                if len(AppSQLData) > 0:
                    SQLUpdateEntry('SteamApps',{'AlwaysSkipped':0, 'Title': PCGWDict['Title'].replace('\'','\'\''), 'MostRecentSaveTime': PCGWDict['TimeModified']}, {'AppID': AppID})
                else:
                    SQLCreateEntry('SteamApps',{'AppID':AppID, 'AlwaysSkipped':0, 'Title': PCGWDict['Title'].replace('\'','\'\''), 'MostRecentSaveTime': PCGWDict['TimeModified']})
                if len(ClientSaveSQLData) > 0:
                    SQLUpdateEntry('ClientSaveInfo',{'Skipped':0, 'InstallPath':GameDataDict['InstallDir'].replace('\'','\'\''), 'MostRecentSaveTime':PCGWDict['TimeModified'], 'ProtonPrefix':GameDataDict['ProtonPath'].replace('\'','\'\'')}, {'AppID':AppID, 'ClientID': ClientID })
                    SQLCreateEntry('SaveTimestamps',{'AppID':AppID, 'Timestamp': PCGWDict['TimeModified']})
                else: 
                    SQLCreateEntry('ClientSaveInfo',{'AppID':AppID, 'ClientID':ClientID, 'Skipped':0, 'InstallPath':GameDataDict['InstallDir'].replace('\'','\'\''), 'MostRecentSaveTime':PCGWDict['TimeModified'], 'ProtonPrefix':GameDataDict['ProtonPath'].replace('\'','\'\'')})
                    SQLCreateEntry('SaveTimestamps',{'AppID':AppID, 'Timestamp': PCGWDict['TimeModified']})
                for relativepath in PCGWDict['RelativeSavePaths']:
                    SQLCreateEntry('RelativeSavePaths',{'AppID':AppID, 'RelativePath':relativepath.replace('\'','\'\'')})
                #if we have more than one absolute save path found
                if len(PCGWDict['AbsoluteSavePaths']) > 1:
                    #We split our prefix and suffixes from our absolute paths
                    (Prefix, Suffixes) = GetPrefixAndSuffixes(PCGWDict['AbsoluteSavePaths'])
                    Prefix = Prefix.replace('{ UID }','')
                    for i in range(0,len(Suffixes)):
                        Suffixes[i] = Suffixes[i].replace('{ UID }','')
                    #Create our prefix and suffix entries for our newly found data
                    if os.path.isdir(Prefix):
                        SQLCreateEntry('ClientPrefixes',{'AppID':AppID, 'ClientID':ClientID, 'Prefix':Prefix})
                        for suffix in Suffixes:
                            if os.path.isfile(Prefix + '/' + suffix) or os.path.isdir(Prefix + '/' + suffix):
                                ContinueFlag = True
                                SQLCreateEntry('ClientSuffixes',{'AppID':AppID, 'ClientID':ClientID, 'Suffix':suffix})
                            else:
                                Suffixes.remove(suffix)
                #if we are only syncing a single file or directory path, we don't have to iterate through our suffix list, just create an empty suffixes variable
                elif len(PCGWDict['AbsoluteSavePaths']) == 1 and '{ UID }' not in PCGWDict['AbsoluteSavePaths'][0]:
                    SQLCreateEntry('ClientPrefixes',{'AppID':AppID,'ClientID':ClientID,'Prefix':PCGWDict['AbsoluteSavePaths'][0].replace('\'','\'\'')})
                    Prefix = PCGWDict['AbsoluteSavePaths'][0]
                    ContinueFlag = True
                    Suffixes = []
                    SQLCreateEntry('ClientSuffixes',{'AppID':AppID,'ClientID':ClientID,'Suffix':''})
                #Compile our data dictionary that should have everything we need to copy our save
                SaveDict = {}
                SaveDict['Timestamp'] = PCGWDict['TimeModified']
                SaveDict['Prefix'] = Prefix.replace('{ UID }','')
                SaveDict['Suffixes'] = Suffixes
                SaveDict['AppID'] = AppID
                SaveDict['ProtonPath'] = PCGWDict['ProtonPath']
                SaveDict['SteamPath'] = PathToSteam
                SaveDict['Home'] = HomeDir
                SaveDict['InstallDir'] = InstallDir
                #Copy our save to the server now that we've created our SQL entries and compiled our data dictionary
                if ContinueFlag:
                    CopySaveToServer(SaveDict, MaxSaves)
            #If this is a steam cloud game and we aren't including steam cloud games to sync
            elif PCGWDict['SteamCloud'] and not IncludeSteamCloud and not NeedPCGWFlag:
                #Create a SQL entry to reference that this game is always skipped by any syncing clients
                SQLCreateEntry('SteamApps',{'AppID':AppID, 'AlwaysSkipped':1, 'Title':PCGWDict['Title'].replace('\'','\'\'')})    
        return 0

#This function performs a full sync, syncing the steam library, rom library, and non-steam library if they exist
#TODO add in silent option to run the sync without any terminal output
def FullSync(PathToSteam, ClientID, IncludeSteamCloud, ROMPaths, MaxSaves, Silent, HomeDir):
    print("Syncing Game Saves, please do not exit until this program has completed running...")
    #Load our vdf file from our path to steam
    PathToVDF = PathToSteam + "steamapps/libraryfolders.vdf"
    LibraryVDFDict = vdf.load(open(PathToVDF))
    #NOTE for now we always assume we're running on linux, as no windows functionality is present
    SystemPlatform = 'Linux'
    if os.path.isdir('./ROMSaves'):
        CheckForUpdatedROMSaves(MaxSaves)
    #for each library that we have mapped in our steam library file
    for Library in LibraryVDFDict['libraryfolders']:
        #We load the path from the library we're currently looking at
        LibraryPath = LibraryVDFDict['libraryfolders'][Library]['path']
        print("Syncing Games From Steam Library Located at: " + LibraryPath)
        #For every application that's installed to this library
        for AppID in LibraryVDFDict['libraryfolders'][Library]['apps']:
            #We sync the individually installed game using our sync game function
            #NOTE this is a portion of the code that I considered multithreading, but generally it seemed like the performance uplift wouldn't be worthwhile compared to the potential issues with multiple PCGW requests and file locks
            SyncGame(AppID, PathToSteam, LibraryPath, ClientID, IncludeSteamCloud, MaxSaves, HomeDir)
        print("Finished Syncing Library!")
    #We check if we are syncing more than one ROM folder
    if len(ROMPaths) > 1:
        #Variable initialization
        SubFolders = []
        RomRootFolder = ''
        NonRootFolders = []
        #We iterate through our ROM Paths
        for RomFolder in ROMPaths:
            #We make sure we pick up on which folders are being synced to different locations
            #That's what the Subfolder tag is for
            if RomFolder["Subfolder"]:
                #We add our ROM Folder to our list of subfolders and non-root folders for later 
                SubFolders.append(RomFolder["Tag"])
                NonRootFolders.append(RomFolder)
            else:
                #We save the root path to it's own value so that we know where the rest of our unspecified ROM folders go
                RomRootFolder = RomFolder["Path"]
        #Once we've iterated through all of our ROM Folders
        #We call our SyncRomFolder function on our root folder, along with passing it a list of folders to exclude from the root folder's sync location
        if RomRootFolder != '':
            SyncRomFolder(RomRootFolder,"./ROMs/",SubFolders, MaxSaves)
        #We iterate through all the rest of our folders, and sync them individually
        for folder in NonRootFolders:
            if folder['Path'] != '':
                SyncRomFolder(folder["Path"],"./ROMs/" + folder["Tag"],[], MaxSaves)
    #If we only specified one ROM Folder location, we don't need to exclude any subfolders from the sync and we know we only have one folder to sync to
    elif len(ROMPaths) == 1 and ROMPaths[0]['Path'] != '':
        SyncRomFolder(ROMPaths[0]["Path"], "./ROMs/", [], MaxSaves)
    #We check for any non-steam games in our database
    NonSteamGameEntries = SQLGetEntry('NonSteamApps', {}, [])
    #If we have at least one non-steam game in our database, we know we need to sync our entire non-steam library
    if len(NonSteamGameEntries) > 0:
        SyncNonSteamLibrary(ClientID, PathToSteam, HomeDir, MaxSaves) 
    print("Full Client Sync Complete!")     
    return 0

#A helper function to try to sync all of our non-Steam games
def SyncNonSteamLibrary(ClientID, PathToSteam, HomeDir, MaxSaves):
    #Variable initialization
    Home = HomeDir
    SearchDirs = []
    FoundGames = []
    SteamDirs = []
    #We get our SQL Data of known games on the current Client
    LocalNonSteamSQLData = SQLGetEntry('NonSteamClientSaves',{'ClientID':ClientID},[])
    #We check to make sure that the compatdata folder we're going to be checking for the existence of non-steam games in exists
    #NOTE this only checks games installed into our local steam folder, this does not check folder outside of the steam install's compatdata folder
    #This is because we expect the user to install onto the C: drive or for the save data to be located on the C: drive
    #AFAIK there is no way to specify a non-Steam Game to have it's compatdata in a different library location, but I could be wrong about that.
    if os.path.isdir(PathToSteam + 'steamapps/compatdata/'):
        SteamDirs = os.listdir(PathToSteam + 'steamapps/compatdata/')
    #We get a list of all of our non-Steam games
    KnownNonSteamSQLData = SQLGetEntry('NonSteamApps',{},[])
    #We check all the directories in our compatdata folder, adding any that are higher than 1,000,000,000 to our search directories since we know that there are no true AppID's that are that high of a number
    for directory in SteamDirs:
        if directory.isnumeric():
            if int(directory) > 1000000000:
                SearchDirs.append(PathToSteam + 'steamapps/compatdata/' + directory + '/pfx/')
    #We also search the $HOME/Games folder if it exists and there are subfolders there as well
    if os.path.isdir(Home + 'Games'):
        TempDirs = os.listdir(Home + 'Games/')
        for tempdir in TempDirs:
            SearchDirs.append(Home + 'Games/' + tempdir + '/')
    #We get our SQL data for all the locally known non-Steam games
    if len(LocalNonSteamSQLData) > 0:
        for LocalGame in LocalNonSteamSQLData:
            UIDFolderFlag = False
            #Sync each game, and add it to our found games list so we know we don't have to search for it later
            RelativePath = SQLGetEntry('NonSteamApps', { 'GameID':LocalGame['GameID'] })[0]['RelativeSavePath']
            if '{ UID }' in RelativePath:
                if '{ HOME }' in RelativePath:
                    RelativePath = RelativePath.replace('{ HOME }', HomeDir)
                if '{ WINE PREFIX }' in RelativePath:
                    Middleath = RelativePath.replace('{ WINE PREFIX }','').replace('{ UID }','')
                    TempSplit = LocalGame['LocalSavePath'].split(MiddlePath)
                    WinePrefix = LocalGame['LocalSavePath'][0]
                    RelativePath = RelativePath.replace('{ WINE PREFIX }',WinePrefix)
                if '{ UID }' == RelativePath.split('/')[-1] and RelativePath.replace('{ UID }','').replace('//','/') in LocalGame['LocalSavePath']:
                    UIDFolderFlag = True
            SyncNonSteamGame(LocalGame['GameID'], LocalGame['LocalSavePath'], LocalGame['MostRecentSaveTime'], ClientID, MaxSaves, UIDFolderFlag)
            FoundGames.append(LocalGame['GameID'])
    #variable initialization to create a list of games we need to search for
    SearchableGames = []
    #We only care about non-steam games we already know about
    if len(KnownNonSteamSQLData) > 0:
        #iterate through our list of non steam games
        for KnownGame in KnownNonSteamSQLData:
            #We add any games that haven't already been found to our list of games we need to search for
            if int(KnownGame['GameID']) not in FoundGames:
                SearchableGames.append(KnownGame)
    #If we have at least one non-Steam game that we haven't located
    if len(SearchableGames) > 0:
        #We iterate through our list of unfound non-Steam games
        for game in SearchableGames:
            FullPath = game['RelativeSavePath']
            print('Searching for game: ' + game['Title'] + ' on new client...')
            #We use the { WINE PREFIX } string in the relative save path to indicate it was installed into a wine prefix
            if '{ WINE PREFIX }' in game['RelativeSavePath']:
                #We pull our path after the drive_c folder from the relative save path
                WinPath = game['RelativeSavePath'].replace('{ WINE PREFIX }','')
                #variable initialization
                i = 0
                found = False
                #We iterate through all the directories that could potentially have the save path we're looking for
                while i < len(SearchDirs) and not found: 
                    #If we find a match to our expected save path
                    if os.path.isdir(SearchDirs[i] + WinPath) or os.path.isfile(SearchDirs[i] + WinPath):
                        #We flag that we found the save path we were looking for
                        found = True
                        #We call the SyncNonSteamGame function for any saves that predate our server save time as well
                        SyncNonSteamGame(game['GameID'], SearchDirs[i] + WinPath, game['MostRecentSaveTime'], ClientID, MaxSaves)
                    #Iteration through our list of directories when we haven't found the expected save path yet
                    else:
                        i += 1
            #We also handle the home folder differently, since it may be in a different location on different machines
            elif '{ HOME }' in game['RelativeSavePath']:
                #We get the expected full path of the game we're currently checking
                FullPath = FullPath.replace('{ HOME }',Home)
                #We make sure that the file or folder exists, then sync if it does
                if (os.path.isdir(FullPath) or os.path.isfile(FullPath)):
                    if '{ UID }' not in game['RelativeSavePath']:
                        SyncNonSteamGame(game['GameID'], FullPath, game['MostRecentSaveTime'], ClientID, MaxSaves)
            if '{ UID }' in game['RelativeSavePath']:
                MatchingPaths = UIDFinder(FullPath)
                if len(MatchingPaths) > 1:
                    print('ERROR: Non-Steam games do not currently support multiple profiles on the same machine. The { UID } tag is meant to distinguish PC specific generated filepaths.')
                elif len(MatchingPaths) == 1:
                    InsideFolderFlag = False
                    FullPath = MatchingPaths[0]
                    TempSplit = game['RelativeSavePath'].split('/')
                    if len(TempSplit) > 1:
                        if TempSplit[-1] != '':
                            if '{ UID }' == TempSplit[-1]:
                                InsideFolderFlag = True
                        elif '{ UID }' == TempSplit[-2]:
                            InsideFolderFlag = True
                    if '{ UID }' not in FullPath:
                        SyncNonSteamGame(game['GameID'], FullPath, game['MostRecentSaveTime'], ClientID, MaxSaves, InsideFolderFlag)
    return 0 
#This function is for 
#TODO integrate the number of saves cap that the user specified at the first run
def SyncNonSteamGame(GameID, LocalSavePath, ServerSaveTime, ClientID, MaxSaves, UIDFolderFlag=False, OverwriteFlag=False):
    LocalSaveEntry = SQLGetEntry('NonSteamClientSaves',{'ClientID':ClientID, 'GameID':GameID})
    ContinueFlag = False
    #We get the time modified of our local save
    LocalTimeModified = GetTimeModified(LocalSavePath)
    #We pull the last file/foldername and specify that that's our filename value
    Filename = LocalSavePath.split('/')[-1]
    #data sanitation check, some file path splits may end up resulting in an empty value as the last value, so we pull the value before if this happens
    if Filename == '':
        Filename = LocalSavePath.split('/')[-2]
    #If the local save time is greater than the server's save time, and we haven't flagged this save to overwrite the save on this client
    if LocalTimeModified > ServerSaveTime and not OverwriteFlag:
        if len(LocalSaveEntry) == 0 and ServerSaveTime != 0:
            print('Unsynced Client has more recent save than server!')
            print('1. Set new client\'s save as the most recent on the server')
            print('2. Overwrite this client\'s save with the most recent save on the server')
            Selection = ''
            while Selection.lower() not in ['1','2','q','quit','exit']:
                if Selection != '':
                    print('ERROR: ' + Selection +' is not a recognized option. Please select an option from the list above or type quit to exit')
                Selection = input("Please select an entry by typing the corresponding number: ")
                if Selection == '1':
                    ContinueFlag = True
                elif Selection == '2':
                    SyncNonSteamGame(GameID, LocalSavePath, ServerSaveTime, ClientID, MaxSaves, UIDFolderFlag, True)
        elif len(LocalSaveEntry) > 0 or ServerSaveTime == 0:
            ContinueFlag = True
        if ContinueFlag:
            #We get the expected backup directory, and output some information to the end user
            BackupDirectory = "./NonSteamSaves" + "/" + str(GameID) + "/" + datetime.datetime.fromtimestamp(LocalTimeModified).strftime('%Y-%m-%d_%H%M%S')
            BackupDirNoTimestamp = "./NonSteamSaves" + "/" + str(GameID) + "/"
            if not os.path.isdir(BackupDirectory):
                os.makedirs(BackupDirectory,exist_ok=True)
            print('More recent save on client than on server!')
            print('Copying Save to server...')
            print('Source: ' + LocalSavePath)
            print('Destination: ' + BackupDirectory)
            #We check whether we're copying a folder or a file, and copy into the backup directory accordingly
            if os.path.isdir(LocalSavePath) and not UIDFolderFlag:
                shutil.copytree(LocalSavePath, BackupDirectory + '/' + Filename, dirs_exist_ok=True)
            elif os.path.isfile(LocalSavePath):
                shutil.copy(LocalSavePath, BackupDirectory)
            elif UIDFolderFlag:
                shutil.copytree(LocalSavePath,BackupDirectory, dirs_exist_ok=True)
            SortedSaves = sorted(os.listdir(BackupDirNoTimestamp))
            if len(SortedSaves) > MaxSaves:
                print("Reached Maximum number of saves...")
                print("Removing oldest save from backups folder...")
                print("Deleting Directory: " + BackupDirNoTimestamp + SortedSaves[0])
                OldestTimestamp = SQLGetMinMax('NonSteamSaveTimestamps', 'Timestamp', { 'GameID': GameID, }, True)[0]['MinVal']
                SQLDeleteEntry('NonSteamSaveTimestamps', {'GameID': GameID, 'Timestamp': OldestTimestamp })
                if os.path.isdir(BackupDirNoTimestamp + SortedSaves[0]):
                    shutil.rmtree(BackupDirNoTimestamp + SortedSaves[0])
                print("Directory Successfully Deleted!")
            #SQL database entry creation and updates for our new save save timestamp
            SQLCreateEntry('NonSteamSaveTimestamps', {'GameID':GameID, 'Timestamp':LocalTimeModified })
            SQLUpdateEntry('NonSteamApps',{'MostRecentSaveTime':LocalTimeModified}, {'GameID':GameID})
            #We need to update our SQL entry for this client with the new timestamp, or create a new entry if one doesn't exist
            if len(LocalSaveEntry) > 0:
                SQLUpdateEntry('NonSteamClientSaves',{ 'MostRecentSaveTime':LocalTimeModified }, { 'GameID': GameID, 'ClientID': ClientID })
            else:
                SQLCreateEntry('NonSteamClientSaves',{ 'GameID': GameID, 'ClientID':ClientID, 'MostRecentSaveTime':LocalTimeModified, 'LocalSavePath':LocalSavePath })
            print('Save successfully copied!')
        #If the server has a more recent save than the current client, or we have a flag to indicate we're overwriting a more recent local save with an earlier server save
    elif ServerSaveTime > LocalTimeModified or OverwriteFlag:
        #We get the expected backup directory and output some information to the end user
        BackupDirectory = "./NonSteamSaves" + "/" + str(GameID) + "/" + datetime.datetime.fromtimestamp(ServerSaveTime).strftime('%Y-%m-%d_%H%M%S')
        print('More recent save on server than on client!')
        print('Copying Save to client...')
        if not UIDFolderFlag:
            print('Source: ' + BackupDirectory + '/' + Filename)
        else:
            print('Source: ' + BackupDirectory)
        print('Destination: ' + LocalSavePath)
        #We need to update our SQL entry for this client with the new timestamp, or create a new entry if there isn't one.
        if len(LocalSaveEntry) > 0:
            SQLUpdateEntry('NonSteamClientSaves',{ 'MostRecentSaveTime':LocalTimeModified }, { 'GameID': GameID, 'ClientID': ClientID })
        else:
            SQLCreateEntry('NonSteamClientSaves',{ 'GameID': GameID, 'ClientID':ClientID, 'MostRecentSaveTime':LocalTimeModified, 'LocalSavePath':LocalSavePath })       
        #We check whether we're copying a folder or a file and copy accordingly
        #NOTE this should overwrite the local data in both cases
        if os.path.isdir(BackupDirectory + '/' + Filename) and not UIDFolderFlag:
            shutil.copytree(BackupDirectory + '/' + Filename, LocalSavePath, dirs_exist_ok=True)
        elif os.path.isfile(BackupDirectory + '/' + Filename) and not UIDFolderFlag:
            if os.path.isfile(LocalSavePath):
                os.remove(LocalSavePath)
            shutil.copy(BackupDirectory + '/' + Filename, LocalSavePath)
        elif UIDFolderFlag:
            shutil.copytree(BackupDirectory,LocalSavePath, dirs_exist_ok=True)
        print('Save successfully copied!')
    return 0
