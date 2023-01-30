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

def PushGameSaveToServer(AppID, ClientID, ApplicationDict):
    ApplicationDict['Title'] = ApplicationDict['Title'].replace("\'","\'\'")
    Restrictions = {}
    Restrictions['AppID'] = AppID
    AppSQLData = SQLGetEntry('SteamApps',Restrictions,[])
    Restrictions['ClientID'] = ClientID
    print(ApplicationDict)
    if len(AppSQLData) > 0:
        SaveSQLData = SQLGetEntry('ClientSaves',Restrictions,[])
        if len(SaveSQLData) > 0:
            ServerSaveTime = AppSQLData[0]['MostRecentSaveTime']
            LocalSaveTime = ApplicationDict['TimeModified']
            if LocalSaveTime > ServerSaveTime:
                #TODO Add in functionality for capping the number of saves that get stored in backups folder
                SQLDict = {'MostRecentSaveTime': LocalTimeModified }
                Restrictions = {'AppID':AppID }
                SQLUpdateEntry('SteamApps', SQLDict, Restrictions)
                SQLDict = {'AppID':AppID, 'Timestamp':LocalSaveTime}
                SQLCreateEntry('SaveTimestamps',SQLDict)
                BackupDirectory = "Backups" + "/" + AppID + "/" + str(LocalSaveTime)
                pathlist = []
                MultiPath = False
                if not os.path.isdir(BackupDirectory):
                    os.makedirs(BackupDirectory, exist_ok = True)
                if len(ApplicationDict['AbsoluteSavePaths']) > 1:
                    MinLength = 100
                    MultiPath = True
                    for path in ApplicationDict['AbsoluteSavePaths']:
                        TempSplit = path.split('/')
                        if len(TempSplit) < MinLength:
                            MinLength = len(TempSplit)
                i = 0
                index = 0
                found = False
                Prefix = ''
                Suffixes = []
                while (i < MinLength) and (not found) and MultiPath:
                    ComparisonPath = ApplicationDict['AbsoluteSavePaths'][0].split('/')
                    NumPaths = len(ApplicationDict['AbsoluteSavePaths'])
                    for j in range(1,NumPaths+1):
                        TempSplit = ApplicationDict['AbsoluteSavePaths'][j].split('/')
                        if TempSplit[i] == ComparisonPath[i] and not found:
                            if j == NumPaths and not found:
                                Prefix += TempSplit[i] + '/'
                        elif j != 1 and not found:
                            index = len(Prefix)
                            Suffixes.append(ApplicationDict['AbsoluteSavePaths'][j][index:])            
                            found = True
                            for k in range(1,j+1):
                                Suffixes.append(ApplicationDict['AbsoluteSavePaths'][k][index:])
                        elif not found:
                            index = len(Prefix)
                            Suffixes.append(ApplicationDict['AbsoluteSavePaths'][j][index:])
                            found = True
                        else:
                            Suffixes.append(ApplicationDict['AbsoluteSavePaths'][j][index:])
                    if found:
                        Suffixes.append(ApplicationDict['AbsoluteSavePaths'][0][index:])
                    else:
                        i += 1
                print(Prefix)
                print(Suffixes)
                for path in ApplicationDict['AbsoluteSavePaths']:
                    splitpath = path.split('/')
                    if splitpath[-1] != '':
                        FileName = splitpath[-1]
                    else:
                        FileName = splitpath[-2]
                    if os.path.isdir(path):
                        shutil.copytree(path,BackupDirectory+'/'+FileName,dirs_exist_ok=True)
                    else:
                        shutil.copy(path,BackupDirectory+'/'+FileName)
        else:
            Restrictions = {'AppID': AppID}
            RelativePaths = SQLGetEntry('RelativeSavePaths',Restrictions,[])
            Savetimestamp = 0
            RelativePathList = []
            for row in RelativePaths:
                RelativePathList.append(row['RelativeSavePath'])
                LocalTimestamp = GetTimeModified(LocalSavePath)
                if LocalTimestamp > SaveTimestamp:
                    SaveTimestamp = LocalTimestamp
            BackupDirectory = "Backups" + "/" + AppID + "/" + str(SaveTimestamp)
            AbsolutePathList = GetExpectedLocalSavePaths(RelativePathList)
            if not os.path.isdir(BackupDirectory):
                os.makedirs(BackupDirectory, exist_ok=True)
            if len(ApplicationDict['AbsoluteSavePaths']) > 1:
                MinLength = 100
                MultiPath = True
                for path in ApplicationDict['AbsoluteSavePaths']:
                    TempSplit = path.split('/')
                    if len(TempSplit) < MinLength:
                        MinLength = len(TempSplit)
            i = 0
            index = 0
            found = False
            Prefix = ''
            Suffixes = []
            while (i < MinLength) and (not found) and MultiPath:
                ComparisonPath = ApplicationDict['AbsoluteSavePaths'][0].split('/')
                NumPaths = len(ApplicationDict['AbsoluteSavePaths'])
                for j in range(1,NumPaths+1):
                    TempSplit = ApplicationDict['AbsoluteSavePaths'][j].split('/')
                    if TempSplit[i] == ComparisonPath[i] and not found:
                        if j == NumPaths and not found:
                            Prefix += TempSplit[i] + '/'
                    elif j != 1 and not found:
                        index = len(Prefix)
                        Suffixes.append(ApplicationDict['AbsoluteSavePaths'][j][index:])
                        found = True
                        for k in range(1,j+1):
                            Suffixes.append(ApplicationDict['AbsoluteSavePaths'][k][index:])
                    elif not found:
                        index = len(Prefix)
                        Suffixes.append(ApplicationDict['AbsoluteSavePaths'][j][index:])
                        found = True
                    else:
                        Suffixes.append(ApplicationDict['AbsoluteSavePaths'][j][index:])
                if found:
                    Suffixes.append(ApplicationDict['AbsoluteSavePaths'][0][index:])
                else:
                    i += 1
            print(Prefix)
            print(Suffixes)
            for path in AbsolutePathList:
                SQLDict = {'AppID':AppID, 'Skipped':0, 'AbsoluteSavePath':path.replace("\'","\'\'"), 'ClientID':ClientID, 'InstallPath':ApplicationDict['InstallDir'].replace("\'","\'\'"), 'ProtonPrefix':ApplicationDict['ProtonPath']}
                SQLCreateEntry('ClientSaves',SQLDict)
                splitpath = path.split('/')
                if splitpath[-1] != '':
                    FileName = splitpath[-1]
                else:
                    FileName = splitpath[-2]
                if os.path.isdir(LocalSavePath):
                    shutil.copytree(path,BackupDirectory+'/'+FileName,dirs_exist_ok=True)
                else:
                    shutil.copy(path,BackupDirectory+'/'+FileName)
    else:
        SQLDict = {'AppID':AppID, 'AlwaysSkipped':0, 'Title':ApplicationDict['Title'], 'MostRecentSaveTime':ApplicationDict['TimeModified']}
        SQLCreateEntry('SteamApps',SQLDict)
        SQLDict = {'AppID':AppID,'Timestamp':ApplicationDict['TimeModified']}
        SQLCreateEntry('SaveTimestamps',SQLDict)
        BackupDirectory = "Backups" + "/" + AppID + "/" + str(ApplicationDict['TimeModified'])
        if not os.path.isdir(BackupDirectory):
            os.makedirs(BackupDirectory, exist_ok = True)
        if len(ApplicationDict['AbsoluteSavePaths']) > 1:
            MinLength = 100
            MultiPath = True
            for path in ApplicationDict['AbsoluteSavePaths']:
                TempSplit = path.split('/')
                if len(TempSplit) < MinLength:
                    MinLength = len(TempSplit)
            i = 0
            index = 0
            found = False
            Prefix = ''
            Suffixes = []
            while (i < MinLength) and (not found) and MultiPath:
                ComparisonPath = ApplicationDict['AbsoluteSavePaths'][0].split('/')
                NumPaths = len(ApplicationDict['AbsoluteSavePaths'])
                for j in range(1,NumPaths):
                    TempSplit = ApplicationDict['AbsoluteSavePaths'][j].split('/')
                    if TempSplit[i] == ComparisonPath[i] and not found:
                        if j == NumPaths-1 and not found:
                            Prefix +=  TempSplit[i] + '/'
                    elif j != 1 and not found:
                        index = len(Prefix)
                        Suffixes.append(ApplicationDict['AbsoluteSavePaths'][j][index:])
                        found = True
                        for k in range(1,j+1):
                            Suffixes.append(ApplicationDict['AbsoluteSavePaths'][k][index:])
                    elif not found:
                        index = len(Prefix)
                        Suffixes.append(ApplicationDict['AbsoluteSavePaths'][j][index:])
                        found = True
                    else:
                        Suffixes.append(ApplicationDict['AbsoluteSavePaths'][j][index:])
                if found:
                    Suffixes.append(ApplicationDict['AbsoluteSavePaths'][0][index:])
                else:
                    i += 1
            print(Prefix)
            print(Suffixes)
        '''
        for path in ApplicationDict['AbsoluteSavePaths']:
            SQLDict = {'AppID':AppID, 'Skipped':0, 'AbsoluteSavePath':path.replace("\'","\'\'"), 'ClientID':ClientID, 'InstallPath':ApplicationDict['InstallDir'].replace("\'","\'\'"), 'ProtonPrefix':ApplicationDict['ProtonPath']}
            SQLCreateEntry('ClientSaves', SQLDict)
            splitpath = path.split('/')
            if splitpath[-1] != '':
                FileName = splitpath[-1]
            else:
                FileName = splitpath[-2]
            if os.path.isdir(path):
                shutil.copytree(path,BackupDirectory+'/'+FileName,dirs_exist_ok=True)
            else:
                shutil.copy(path,BackupDirectory+'/'+FileName)
        for path in ApplicationDict['RelativeSavePaths']:
            SQLDict = {'AppID':AppID, 'RelativeSavePath':path.replace("\'","\'\'")}
            SQLCreateEntry('RelativeSavePaths',SQLDict)'''
    return 0

def CopySaveFromServer(SaveDict):
    print("==========================================================================")
    print("Copying Save From Server...")
    FileName = ''
    BackupDirectory = "Backups" + "/" + SaveDict['AppID'] + "/" + str(SaveDict['Timestamp'])
    DestinationDirectory = SaveDict['Prefix']
    for suffix in SaveDict['Suffixes']:
        if suffix != '':
            RelativeSuffix = GetRelativePath(SaveDict,'/' + suffix)
            TempSplit = suffix.split('/')
            if TempSplit[-1] != '':
                FileName = TempSplit[-1]
            else:
                FileName = TempSplit[-2]
            PrecedingFolders = RelativeSuffix.split(FileName)[0]
            Source = BackupDirectory + '/' + PrecedingFolders + FileName
            Destination = SaveDict['Prefix'] + '/' + suffix
            if os.path.isdir(Source):
                print("Source: " + Source)
                print("Destination: " + Destination)
                os.makedirs(Destination.replace(FileName,''),exist_ok=True)
                if os.path.isdir(Destination):
                    shutil.rmtree(Destination) 
                shutil.copytree(Source,Destination)
                print("Save Successfully Copied!")
            elif os.path.sifile(Source):
                print("Source: " + Source)
                print("Destination: " + Destination)
                os.makedirs(Destination.replace(FileName,''),exist_ok=True)
                if os.path.isfile(Destination):
                    os.remove(Destination)
                shutil.copy(Source,Destination)
                print("Save Successfully Copied!")
        else:
            TempSplit = SaveDict['Prefix'].split('/')
            if TempSplit[-1] != '':
                FileName = TempSplit[-1]
            else:
                FileName = TempSplit[-2]
        Source = BackupDirectory + '/'  + FileName
        Destination = SaveDict['Prefix']
        if os.path.isdir(Source):
            print("Source: " + Source)
            print("Destination: " + Destination)
            os.makedirs(Destination.replace(FileName,''),exist_ok=True)
            if os.path.isdir(Destination):
                shutil.rmtree(Destination)
            shutil.copytree(Source,Destination)
            print("Save Successfully Copied!")
        elif os.path.isfile(Source):
            print("Source: " + Source)
            print("Destination: " + Destination)
            os.makedirs(Destination.replace(FileName,''),exist_ok=True)
            if os.path.isfile(Destination):
                os.remove(Destination)
            shutil.copy(Source,Destination)
            print("Save Successfully Copied!")
    return 0

def CopySaveToServer(SaveDict):
    print("Copying Save To Server...")
    FileName = ''
    BackupDirectory = "Backups" + "/" + SaveDict['AppID'] + "/" + str(SaveDict['Timestamp'])
    if not os.path.isdir(BackupDirectory):
        os.makedirs(BackupDirectory,exist_ok=True)
    if len(SaveDict['Suffixes']) == 0 or len(SaveDict['Suffixes']) == 1:
        SplitPath = SaveDict['Prefix'].split('/')
        if SplitPath[-1] != '':
            FileName = SplitPath[-1]
        else:
            FileName = SplitPath[-2]
        if os.path.isdir(SaveDict['Prefix']):
            print("Source: " + SaveDict['Prefix'])
            print("Destination: " + BackupDirectory + '/' + FileName)
            shutil.copytree(SaveDict['Prefix'],BackupDirectory + '/' + FileName,dirs_exist_ok=True)
            print("Save Successfully Copied!")
        else:
            print("Source: " + SaveDict['Prefix'])
            print("Destination: " + BackupDirectory + '/' + FileName)
            shutil.copy(SaveDict['Prefix'],BackupDirectory + '/' + FileName)
            print("Save Successfully Copied!")
    else:
        for suffix in SaveDict['Suffixes']:
            RelativeSuffix= GetRelativePath(SaveDict,'/' + suffix)
            TempSplit = suffix.split('/')
            if TempSplit[-1] != '':
                FileName = TempSplit[-1]
            else:
                FileName = TempSplit[-2]
            PrecedingFolders = RelativeSuffix.split(FileName)[0]
            os.makedirs(BackupDirectory+'/'+PrecedingFolders,exist_ok=True)
            if os.path.isdir(SaveDict['Prefix'] + '/' + suffix):
                print("Source: " + SaveDict['Prefix'] + '/' + suffix)
                print("Destination: " + BackupDirectory + '/' + PrecedingFolders + '/' + FileName)
                shutil.copytree(SaveDict['Prefix'] + '/' + suffix, BackupDirectory + '/' + PrecedingFolders + '/' + FileName)
                print("Save Successfully Copied!")
            elif PrecedingFolders == '':
                print("Source: " + SaveDict['Prefix'] + '/' + suffix)
                print("Destination: " + BackupDirectory + '/' + FileName)
                shutil.copy(SaveDict['Prefix'] + '/' + suffix, BackupDirectory + '/' + FileName)
                print("Save Successfully Copied!")
            else:
                print("Souce: " + SaveDict['Prefix'] + '/' + suffix)
                print("Destination: " + BackupDirectory + '/' + PrecedingFolders + '/' + FileName)
                shutil.copy(SaveDict['Prefix'] + '/' + suffix, BackupDirectory + '/' + PrecedingFolders + '/' + FileName)
                print("Save Successfully Copied!")
    return 0

def GetPrefixAndSuffixes(PathList):
    MinLength = 100
    for path in PathList:
        TempSplit = path.split('/')
        if len(TempSplit) < MinLength:
            MinLength = len(TempSplit)
    i = 0
    index = 0
    found = False
    Prefix = ''
    Suffixes = []
    while (i < MinLength) and (not found):
        ComparisonPath = PathList[0].split('/')
        NumPaths = len(PathList)
        for j in range(1,NumPaths):
            TempSplit = PathList[j].split('/')
            if TempSplit[i] == ComparisonPath[i] and not found:
                if j == NumPaths-1 and not found:
                    Prefix += TempSplit[i] + '/'
            elif j != 1 and not found:
                index = len(Prefix)
                Suffixes.append(PathList[j][index:])
                found = True
                for k in range(1,j+1):
                    Suffixes.append(PathList[k][index:])
            elif not found:
                index = len(Prefix)
                Suffixes.append(PathList[j][index:])
                found = True
            else:
                Suffixes.append(PathList[j][index:])
        if found:
            Suffixes.append(PathList[0][index:])
        else:
            i += 1
    return (Prefix,Suffixes)

def GetTimeModified(FilePath):
    LastTimeModified = 0
    if os.path.isdir(FilePath):
        LastTimeModified = os.path.getmtime(FilePath)
        for file in os.listdir(FilePath):
            if os.path.isfile(file):
                if os.path.getmtime(file) > LastTimeModified:
                    LastTimeModified = os.path.getmtime(file)
    elif os.path.isfile(FilePath):
        LastTimeModified = os.path.getmtime(FilePath)
    return LastTimeModified

def GetFilepathFixes(ApplicationDict):
    return 0

def VerifyLocalData(ReferencePaths):
    ReturnList = []
    SaveType = 'Unfound'
    for path in ReferencePaths:
        Directories = path.split('/')
        TempList = []
        for directory in Directories:
            if directory != '':
                TempList.append(directory)
        Directories = TempList
        if (SaveType in ['Unfound', 'Filename'] and (Directories[-1][-1] == '*' or ('.' in Directories[-1]))):
            TempPath = ''
            for i in range(0,len(Directories)-1):
                TempPath += '/' + Directories[i]
            filename = Directories[-1].replace('.','\.').replace('*','.*')
            if os.path.isdir(TempPath):
                regexp = re.compile(filename)
                for file in os.listdir(TempPath):
                    if regexp.match(file):
                        SaveType = 'Filename'
                        ReturnPath = TempPath + '/' + file
                        ReturnList.append({'AbsolutePath':ReturnPath, 'SaveType':'Filename', 'Found':True, 'TimeModified':GetTimeModified(ReturnPath)})
        elif SaveType in ['Unfound','Directory'] and os.path.isdir(path):
            ReturnList.append({'AbsolutePath': path, 'SaveType':'Directory', 'Found':True, 'TimeModified': GetTimeModified(path)})
        else:
            ReturnList.append({'AbsolutePath': path, 'SaveType':'Unfound', 'Found':False})
    return ReturnList

def UIDFinder(Path,Exclusions):
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
        #we know that the current substitution is simply a full folder name
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


def GetFilepaths(ApplicationDict, UnprocessedPath):
    SubstitutionDict = {}
    ReturnPaths = []
    SubstitutionDict['\{\{p\|uid\}\}'] = '{ UID }'
    if ApplicationDict['SystemPlatform'] == 'Linux':
        SubstitutionDict['\{\{p\|linuxhome\}\}'] = ApplicationDict['Home']
        SubstitutionDict['\{\{p\|xdgdatahome\}\}'] = ApplicationDict['Home'] + '/.local/share/'
        SubstitutionDict['\{\{p\|xdgconfighome\}\}'] = ApplicationDict['Home'] + '/.config/'
        SubstitutionDict['\{\{p\|steam\}\}'] = ApplicationDict['Home'] + "/.steam/steam/"
        SubstitutionDict['~'] = ApplicationDict['Home']
    if ApplicationDict['SystemPlatform'] != ApplicationDict['GamePlatform']:
        SubstitutionDict['\{\{p\|localappdata\}\}'] = ApplicationDict['ProtonPath'] + 'pfx/drive_c/users/steamuser/AppData/Local/'
        SubstitutionDict['\{\{p\|appdata\}\}'] = ApplicationDict['ProtonPath'] + 'pfx/drive_c/users/steamuser/AppData/Roaming/'
        SubstitutionDict['\{\{p\|userprofile\\Documents\}\}'] = ApplicationDict['ProtonPath'] + 'pfx/drive_c/users/steamuser/My Documents/'
        SubstitutionDict['\{\{Path\|localappdata\}\}'] = ApplicationDict['ProtonPath'] + 'pfx/drive_c/users/steamuser/AppData/Local/'
        SubstitutionDict['\{\{p\|userprofile\}\}'] = ApplicationDict['ProtonPath'] + 'pfx/drive_c/users/steamuser/'
        SubstitutionDict['\{\{p\|programdata\}\}'] = ApplicationDict['ProtonPath'] + 'pfx/drive_c/programdata/'
        SubstitutionDict['\{\{p\|userprofile'] = ApplicationDict['ProtonPath'] + 'pfx/drive_c/users/steamuser/'
        SubstitutionDict['\{\{p\|username\}\}'] = ApplicationDict['ProtonPath'] + 'pfx/drive_c/users/steamuser/'
    else:
        SubstitutionDict['\{\{p\|localappdata\}\}'] = ''
        SubstitutionDict['\{\{p\|appdata\}\}'] = ''
        SubstitutionDict['\{\{p\|userprofile\\Documents\}\}'] = ''
        SubstitutionDict['\{\{Path\|localappdata\}\}'] = ''
        SubstitutionDict['\{\{p\|userprofile\}\}'] = ''
        SubstitutionDict['\{\{p\|userprofile'] = ''
    SubstitutionDict['\{\{p\|hkcu\}\}'] = '{ HKEY CURRENT USER }'

    SubstitutionDict['\{\{p\|game\}\}'] = ApplicationDict['InstallDir']
    for substitution in SubstitutionDict:
        SubVar = re.compile(substitution,re.IGNORECASE)
        UnprocessedPath = SubVar.sub(SubstitutionDict[substitution],UnprocessedPath)
    ProcessedPaths = UnprocessedPath.split('|')
    for path in ProcessedPaths:
        path = path.replace('\\','/').replace('//','/').replace('}}','')
        if '{ UID }' in path:
            ReturnPaths.extend(UIDFinder(path,[]))
        else:
            ReturnPaths.append(path)
    return ReturnPaths

def ParseSaveData(ApplicationDict, SaveDataDict):
    ReturnList = []
    for SaveType in SaveDataDict:
        ReturnList.extend(GetFilepaths(ApplicationDict,SaveDataDict[SaveType]))
    return ReturnList


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

def GetPCGWData(ApplicationDict):
    ReturnPaths = []
    ReturnDict = {}
    ReturnDict['Found'] = False
    WikiURL = "https://www.pcgamingwiki.com/w/api.php?action=cargoquery&tables=Infobox_game,Cloud&fields=Cloud.Steam,Cloud.GOG_Galaxy,Cloud.Discord,Cloud.Epic_Games_Launcher,Cloud.EA_Desktop,Cloud.OneDrive,Cloud.Ubisoft_Connect,Cloud.Xbox,Infobox_game._pageID=PageID,Infobox_game._pageName=Page,Infobox_game.Developers,Infobox_game.Released,Infobox_game.Cover_URL&join_on=Infobox_game._pageID=Cloud._pageID&where=Infobox_game.Steam_AppID%20HOLDS%20%22" + ApplicationDict['AppID'] + "%22&format=json"
    JSONData = requests.get(WikiURL)
    RawSaveDataDict = {}
    Cargo = {}
    LinuxSave = False
    WindowsSave = False
    SteamSave = False
    if 'cargoquery' in JSONData.json():
        Cargo = JSONData.json()['cargoquery']
        if len(Cargo) > 0:
            if Cargo[0]['title']['Steam'] == 'true':
                ReturnDict['SteamCloud'] = True
            else:
                ReturnDict['SteamCloud'] = False
            PageID = Cargo[0]['title']['PageID']
            RawWikiData = requests.get("https://www.pcgamingwiki.com/w/api.php?action=parse&format=json&pageid=" + PageID + "&prop=wikitext")
            if RawWikiData != '':
                ParsedWikiData = RawWikiData.json()['parse']['wikitext']['*']
                RawSaveLocations = re.search('===Save game data location===[\S\n ]+?===.+===',ParsedWikiData)
                if RawSaveLocations:
                    RawWindowsSave = re.search("Windows\|.+\}\}",RawSaveLocations.group())
                    RawSteamSave = re.search("Steam\|.+\n",RawSaveLocations.group())
                    RawLinuxSave = re.search("Linux\|.+\n",RawSaveLocations.group())
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
    if (LinuxSave or SteamSave or WindowsSave):
        SaveDataList = ParseSaveData(ApplicationDict, RawSaveDataDict)
        VerifiedSaveDataDict = VerifyLocalData(SaveDataList)
        ReturnDict['AbsoluteSavePaths'] = []
        ReturnDict['RelativeSavePaths'] = []
        ReturnDict['TimeModified'] = 0
        for entry in VerifiedSaveDataDict:
            if entry['Found']:
                ReturnDict['Found'] = True
                if entry['TimeModified'] > ReturnDict['TimeModified']:
                    ReturnDict['TimeModified'] = entry['TimeModified']
                if entry['AbsolutePath'] not in ReturnDict['AbsoluteSavePaths']:
                    ReturnDict['AbsoluteSavePaths'].append(entry['AbsolutePath'])
                RelativePath = GetRelativePath(ApplicationDict,entry['AbsolutePath'])
                if RelativePath not in ReturnDict['RelativeSavePaths']:
                    ReturnDict['RelativeSavePaths'].append(RelativePath)
        if not ReturnDict['Found']:
            for entry in SaveDataList:
                if entry not in ReturnDict['AbsoluteSavePaths']:
                    ReturnDict['AbsoluteSavePaths'].append(entry)
                RelativePath = GetRelativePath(ApplicationDict, entry)
                if RelativePath not in ReturnDict['RelativeSavePaths']:
                    ReturnDict['RelativeSavePaths'].append(RelativePath)
        if 'AppID' in ApplicationDict:
            ReturnDict['AppID'] = ApplicationDict['AppID']
        if 'ProtonPath' in ApplicationDict:
            ReturnDict['ProtonPath'] = ApplicationDict['ProtonPath']
        if 'InstallDir' in ApplicationDict:
            ReturnDict['InstallDir'] = ApplicationDict['InstallDir']
    if 'SteamCloud' not in ReturnDict:
        ReturnDict['SteamCloud'] = False
    return ReturnDict



def SyncGame(AppID, PathToSteam, LibraryPath, ClientID, IncludeSteamCloud):
    AppSQLData = SQLGetEntry('SteamApps', {'AppID': AppID}, [])
    AppVDFData = vdf.load(open(LibraryPath + '/steamapps/appmanifest_' + AppID + '.acf'))
    InstallDir = LibraryPath + '/steamapps/common/' + AppVDFData['AppState']['installdir']
    ProtonPath = ''
    SystemPlatform = 'Linux'
    GamePlatform = 'Linux'
    if 'platform_override_dest' in AppVDFData['AppState']['UserConfig']:
        if AppVDFData['AppState']['UserConfig']['platform_override_dest'] == 'linux' and AppVDFData['AppState']['UserConfig']['platform_override_source'] == 'windows':
            GamePlatform = 'Windows'
        else:
            GamePlatform = 'Linux'
    if GamePlatform != SystemPlatform:
        ProtonPath = LibraryPath + '/steamapps/compatdata/' + AppID +'/'
    GameDataDict = {}
    GameDataDict['AppID'] = AppID
    GameDataDict['ProtonPath'] = ProtonPath
    GameDataDict['InstallDir'] = InstallDir
    GameDataDict['Home'] = os.path.expanduser('~')
    GameDataDict['Title'] = AppVDFData['AppState']['name']
    GameDataDict['SystemPlatform'] = SystemPlatform
    GameDataDict['GamePlatform'] = GamePlatform
    GameDataDict['SteamPath'] = PathToSteam
    if len(AppSQLData) != 0 and AppSQLData[0]['AlwaysSkipped'] == 0:
        MostRecentSaveTime = AppSQLData[0]['MostRecentSaveTime']
        SaveDict = {}
        ClientSaveSQLData = SQLGetEntry('ClientSaveInfo',{'ClientID':ClientID, 'AppID':AppID}, [])
        GameTitle = SQLGetEntry('SteamApps',{'AppID': AppID }, ['Title'])[0]['Title']
        Suffixes = []
        if len(ClientSaveSQLData) > 0 and ClientSaveSQLData[0]['Skipped'] == 0:
            PathPrefix = SQLGetEntry('ClientPrefixes',{'ClientID':ClientID, 'AppID':AppID}, [])[0]['Prefix']
            SuffixSQLData = SQLGetEntry('ClientSuffixes',{'ClientID':ClientID, 'AppID':AppID}, [])
            if len(SuffixSQLData) > 0:
                for row in SuffixSQLData:
                    Suffixes.append(row['Suffix'])
            LocalSaveTime = 0
            if len(Suffixes) > 0:
                for suffix in Suffixes:
                    LocalTimestamp = GetTimeModified(PathPrefix + suffix)
                    if LocalTimestamp > LocalSaveTime:
                        LocalSaveTime = LocalTimestamp
            else:
                LocalSaveTime = GetTimeModified(PathPrefix)
            if LocalSaveTime > MostRecentSaveTime:
                print('==========================================================')
                print("More recent save than registered to server located!")
                print("Title: " + GameDataDict['Title'])
                print("AppID: " + AppID)
                SaveDict['Timestamp'] = LocalSaveTime
                SaveDict['Prefix'] = PathPrefix
                SaveDict['Suffixes'] = Suffixes
                SaveDict['AppID'] = AppID
                SaveDict['ProtonPath'] = ProtonPath
                SaveDict['SteamPath'] = PathToSteam
                SaveDict['Home'] = os.path.expanduser('~')
                SaveDict['InstallDir'] = InstallDir
                CopySaveToServer(SaveDict)
                SQLUpdateEntry('ClientSaveInfo',{'MostRecentSaveTime':LocalSaveTime},{'AppID':AppID,'ClientID':ClientID})
                SQLUpdateEntry('SteamApps',{'MostRecentSaveTime':LocalSaveTime},{'AppID':AppID})
                SQLCreateEntry('SaveTimestamps',{'AppID':AppID,'Timestamp':LocalSaveTime})
            elif MostRecentSaveTime > LocalSaveTime:
                print('==========================================================')
                print("More recent save on server than locally stored located!")
                print("Title: " + GameDataDict['Title'])
                print("AppID: " + AppID)
                SaveDict['Timestamp'] = MostRecentSaveTime
                SaveDict['Prefix'] = PathPrefix
                SaveDict['Suffixes'] = Suffixes
                SaveDict['AppID'] = AppID
                SaveDict['ProtonPath'] = ProtonPath
                SaveDict['SteamPath'] = PathToSteam
                SaveDict['Home'] = os.path.expanduser('~')
                SaveDict['InstallDir'] = InstallDir
                CopySaveFromServer(SaveDict)
                SQLUpdateEntry('ClientSaveInfo',{'MostRecentSaveTime':MostRecentSaveTime},{'AppID':AppID,'ClientID':ClientID})
        elif len(ClientSaveSQLData) == 0:
            LocalSaveTime = 0
            RelativePathsSQLData = SQLGetEntry('RelativeSavePaths',{'AppID':AppID},['RelativePath'])
            RelativePaths = []
            for row in RelativePathsSQLData:
                RelativePaths.append(row['RelativePath'])
            AbsoluteSavePaths = []
            for path in RelativePaths:
                AbsoluteSavePaths.append(GetAbsolutePath(GameDataDict, path))
            VerifiedDataDict = VerifyLocalData(AbsoluteSavePaths)
            FoundPaths = []
            for entry in VerifiedDataDict:
                if entry['Found']:
                    print(entry)
                    FoundPaths.append(entry['AbsolutePath'])
            if len(FoundPaths) > 1:
                (Prefix, Suffixes) = GetPrefixAndSuffixes(FoundPaths)
                for suffix in Suffixes:
                    TempTimestamp = GetTimeModified(Prefix + suffix)
                    if TempTimestamp > LocalSaveTime:
                        LocalSaveTime = TempTimestamp
            elif len(FoundPaths) == 1:
                Prefix = FoundPaths[0]
                Suffixes = ['']
                LocalSaveTime = GetTimeModified(Prefix)
            if LocalSaveTime > MostRecentSaveTime:
                response = ''
                while(response not in ['1','2','3']):
                    print('==========================================================')
                    print('Unsynced Client has more recent save than server')
                    print('Game Title: ' + GameDataDict['Title'])
                    print('Please Select an option:')
                    print('1. Overwrite server save with local save')
                    print('2. Overwrite local save with server save')
                    print('3. Do not sync this game save with this client')
                    response = input('Type the corresponding number (1,2,3): ')
                if response == '1':
                    print("More recent save than registered to server located!")
                    print("Title: " + GameDataDict['Title'])
                    print("AppID: " + AppID)
                    SaveDict['Timestamp'] = LocalSaveTime
                    SaveDict['Prefix'] = Prefix
                    SaveDict['Suffixes'] = Suffixes
                    SaveDict['AppID'] = AppID
                    SaveDict['ProtonPath'] = ProtonPath
                    SaveDict['SteamPath'] = PathToSteam
                    SaveDict['Home'] = os.path.expanduser('~')
                    SaveDict['InstallDir'] = InstallDir
                    CopySaveToServer(SaveDict)
                    SQLCreateEntry('ClientSaveInfo',{'AppID': AppID, 'ClientID': ClientID, 'Skipped': 0, 'InstallPath': InstallPath, 'MostRecentSaveTime': LocalSaveTime, 'ProtonPrefix': ProtonPath.replace('\'','\'\'')})
                    SQLCreateEntry('ClientPrefixes',{'AppID': AppID, 'ClientID': ClientID, 'Prefix': Prefix.replace('\'','\'\'')})
                    SQLCreateEntry('SaveTimestamps',{'AppID': AppID, 'Timestamp': LocalSaveTime})
                    SQLUpdateEntry('SteamApps',{'MostRecentSaveTime': LocalSaveTime}, {'AppID': AppID })
                    if len(Suffixes) > 0:
                        for suffix in Suffixes:
                            SQLCreateEntry('ClientSuffixes',{'AppID': AppID, 'ClientID': ClientID, 'Suffix': suffix})
                elif response == '2':
                    print("More recent save on server than locally stored located!")
                    print("Title: " + GameDataDict['Title'])
                    print("AppID: " + AppID)
                    SaveDict['Timestamp'] = MostRecentSaveTime
                    SaveDict['Prefix'] = Prefix
                    SaveDict['Suffixes'] = Suffixes
                    SaveDict['AppID'] = AppID
                    SaveDict['ProtonPath'] = ProtonPath
                    SaveDict['SteamPath'] = PathToSteam
                    SaveDict['Home'] = os.path.expanduser('~')
                    SaveDict['InstallDir'] = InstallDir
                    CopySaveFromServer(SaveDict)
                    SQLCreateEntry('ClientSaveInfo',{'AppID': AppID, 'ClientID': ClientID, 'Skipped': 0, 'InstallPath': InstallDir.replace('\'','\'\''), 'MostRecentSaveTime': MostRecentSaveTime, 'ProtonPrefix': ProtonPath.replace('\'','\'\'')})
                    SQLCreateEntry('ClientPrefixes',{'AppID': AppID, 'ClientID': ClientID, 'Prefix':Prefix.replace('\'','\'\'')})
                    if len(Suffixes) > 0:
                        for suffix in Suffixes:
                            SQLCreateEntry('ClientSuffixes',{'AppID': AppID, 'ClientID': ClientID, 'Suffix':suffix.replace('\'','\'\'')})
                elif response == '3':
                    SQLCreateEntry('ClientSaveInfo',{'AppID': AppID, 'ClientID': ClientID, 'Skipped': 1})
            else:
                AbsolutePaths = []
                for path in RelativePaths:
                    AbsolutePaths.append(GetAbsolutePath(GameDataDict,path))
                if len(AbsolutePaths) > 1:
                    (Prefix, Suffixes) = GetPrefixAndSuffixes(AbsolutePaths)
                else:
                    Prefix = AbsolutePaths[0]
                    Suffixes = ['']
                print('==========================================================')
                print("More recent save on server than locally stored located!")
                print("Title: " + GameDataDict['Title'])
                print("AppID: " + AppID)
                SaveDict['Timestamp'] = MostRecentSaveTime
                SaveDict['Prefix'] = Prefix
                SaveDict['Suffixes'] = Suffixes
                SaveDict['AppID'] = AppID
                SaveDict['ProtonPath'] = ProtonPath
                SaveDict['SteamPath'] = PathToSteam
                SaveDict['Home'] = os.path.expanduser('~')
                SaveDict['InstallDir'] = InstallDir
                CopySaveFromServer(SaveDict)
                SQLCreateEntry('ClientSaveInfo',{'AppID':AppID, 'ClientID':ClientID, 'Skipped':0, 'InstallPath':InstallDir.replace('\'','\'\''), 'MostRecentSaveTime':MostRecentSaveTime, 'ProtonPrefix':ProtonPath.replace('\'','\'\'')})
                SQLCreateEntry('ClientPrefixes',{'AppID':AppID, 'ClientID':ClientID, 'Prefix':Prefix.replace('\'','\'\'')})
                for suffix in Suffixes:
                    SQLCreateEntry('ClientSuffixes',{'AppID':AppID, 'ClientID':ClientID, 'Suffix':suffix.replace('\'','\'\'')})
                
    elif len(AppSQLData) == 0:
        PCGWDict = GetPCGWData(GameDataDict)
        PCGWDict['Title'] = AppVDFData['AppState']['name']
        if PCGWDict['Found'] and (PCGWDict['SteamCloud'] == False or (PCGWDict['SteamCloud'] == True and IncludeSteamCloud)):
            print('==========================================================')
            print('Unregistered Game\'s Local Save Data Found!')
            print('Title: ' + PCGWDict['Title'])
            print('AppID: ' + AppID)
            Suffixes = []
            SQLCreateEntry('SteamApps',{'AppID':AppID, 'AlwaysSkipped':0, 'Title': PCGWDict['Title'].replace('\'','\'\''), 'MostRecentSaveTime': PCGWDict['TimeModified']})
            SQLCreateEntry('ClientSaveInfo',{'AppID':AppID, 'ClientID':ClientID, 'Skipped':0, 'InstallPath':GameDataDict['InstallDir'].replace('\'','\'\''), 'MostRecentSaveTime':PCGWDict['TimeModified'], 'ProtonPrefix':GameDataDict['ProtonPath'].replace('\'','\'\'')})
            for relativepath in PCGWDict['RelativeSavePaths']:
                SQLCreateEntry('RelativeSavePaths',{'AppID':AppID, 'RelativePath':relativepath.replace('\'','\'\'')})
            if len(PCGWDict['AbsoluteSavePaths']) > 1:
                (Prefix, Suffixes) = GetPrefixAndSuffixes(PCGWDict['AbsoluteSavePaths'])
                SQLCreateEntry('ClientPrefixes',{'AppID':AppID, 'ClientID':ClientID, 'Prefix':Prefix})
                for suffix in Suffixes:
                    SQLCreateEntry('ClientSuffixes',{'AppID':AppID, 'ClientID':ClientID, 'Suffix':suffix})
                
            else:
                SQLCreateEntry('ClientPrefixes',{'AppID':AppID,'ClientID':ClientID,'Prefix':PCGWDict['AbsoluteSavePaths'][0].replace('\'','\'\'')})
                Prefix = PCGWDict['AbsoluteSavePaths'][0]
                Suffixes = []
                SQLCreateEntry('ClientSuffixes',{'AppID':AppID,'ClientID':ClientID,'Suffix':''})
            SaveDict = {}
            SaveDict['Timestamp'] = PCGWDict['TimeModified']
            SaveDict['Prefix'] = Prefix
            SaveDict['Suffixes'] = Suffixes
            SaveDict['AppID'] = AppID
            SaveDict['ProtonPath'] = PCGWDict['ProtonPath']
            SaveDict['SteamPath'] = PathToSteam
            SaveDict['Home'] = os.path.expanduser('~')
            SaveDict['InstallDir'] = InstallDir
            CopySaveToServer(SaveDict)
        elif PCGWDict['SteamCloud'] and not IncludeSteamCloud:
            SQLCreateEntry('SteamApps',{'AppID':AppID, 'AlwaysSkipped':1, 'Title':PCGWDict['Title'].replace('\'','\'\'')})    
    return 0


def FullSync(PathToSteam, ClientID, IncludeSteamCloud):
    PathToVDF = PathToSteam + "steamapps/libraryfolders.vdf"
    LibraryVDFDict = vdf.load(open(PathToVDF))
    SystemPlatform = 'Linux'
    for Library in LibraryVDFDict['libraryfolders']:
        LibraryPath = LibraryVDFDict['libraryfolders'][Library]['path']
        for AppID in LibraryVDFDict['libraryfolders'][Library]['apps']:
            SyncGame(AppID, PathToSteam, LibraryPath, ClientID, IncludeSteamCloud)
    return 0







#FullSync("/home/tanner/.local/share/Steam/",1,False)
