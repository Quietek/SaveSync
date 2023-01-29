#!/usr/bin/python

#Author: Tanner Tracy
#Date Created: 2022-08-08
#Description: A program used to sync savedata for steam games between computers since not all games on steam support cloud saves

#Modified By:
#Date Modified:
#Description:

#TODO move filepath replacements and file exclusions to separate files or functions
#TODO edit time modified detection to be based on the last time any contents of a folder were changed, not just the folder and it's subfolders
#TODO add in dummy data for games where no save data was detected
#TODO add in support for writing our local dictionary data to a file
#TODO add in functionality to actually back up the found save paths to a folder based on it's last modified time
#TODO add in support for comparing found data to our backed up data
#TODO add in support for referencing local library of save paths before making request to PCGW
#TODO add in GUI for easier end user experience
#TODO rewrite to new files to add in support for adding a separate machine to the overall library
#TODO add in support for dedicated save files for individual machines
#TODO add in support for windows
#TODO add in support for multithreading for each application scanned
#Process should go read application -> spawn thread checking for it in our local library -> make PCGW request if not found



import requests
import json
import os
import vdf
import re
import time
from sys import platform

home = "/home/tanner"
exclusionlist = ['320','1580130','1245040','228980','1054830','1391110','1493710','1887720']

ManualFilePathReplacementList = {}

ManualFilePathReplacementList['435150'] = {}
ManualFilePathReplacementList['435150']['original'] = 'Divinity Original Sin 2'
ManualFilePathReplacementList['435150']['replacement'] = 'Divinity Original Sin 2 Definitive Edition'

ManualFilePathReplacementList['307690'] = {}
ManualFilePathReplacementList['307690']['original'] = 'Data'
ManualFilePathReplacementList['307690']['replacement'] = 'data'

ManualFilePathReplacementList['594570'] = {}
ManualFilePathReplacementList['594570']['original'] = 'save_games'
ManualFilePathReplacementList['594570']['replacement'] = ''

FileExclusionList = {}
FileExclusionList['286690'] = ['2033']
FileExclusionList['361670'] = ['WAVE.plt','RESDATA.plt','FRONTRES.plt','MISSIONS.plt','MOVIES.plt','FLIGHTMODELS.plt','SKIRMISH.plt','RESOURCE.plt','SFX.plt','MUSIC.plt','MELEE.plt','Test1.plt','Test0.plt']

GlobalDict = {}

#Function used to sanitize the values pulled in from our json query
def GenerateFilepathList(Filepaths):
    #Initialize return value
    ReturnList = []
    #For each path in our filepath list
    for path in Filepaths:
        #create a tempororay path, sanitized for double slashes, backslashes, and brackets which may be leftover from our initial pull from the wiki
        temppath = path.replace('\\','/').replace('//','/').replace('}}','')
        #create an extra entry for each pipe in the string, indicates multiple potential save paths for this game
        if '|' in temppath:
            templist = temppath.split('|')
            #append each path back into our return value
            for entry in templist:
                ReturnList.append(entry.replace('//','/'))
        else:
            #we know this path only contains one true filepath, so append it to our return list
            ReturnList.append(temppath.replace('//','/'))
    return ReturnList


def UIDFinder(Paths,Exclusions):
    #Initialize Final Return Value List
    ReturnPaths = []
    #For each path in the paths list
    for Path in Paths:
        print(Path)
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
        SplitPath = Path.replace('\\','/').replace('//','/').replace('}}','').split('{ UID }')
        print(SplitPath)
        #remove empty values that may be present from our split on the UIDs
        if '' in SplitPath:
            SplitPath.remove('')
        #if the first character is a . after our last UID substitution, we flag that the last UID is a filename
        if SplitPath[-1][0] == '.':
            FilenameFlag = True
        #if the last character before our current UID substitution is not a /, we flag that the current UID is a partial folder or filename
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
                        #Recursive function call to attempt replacements for the rest of the filepath if there are further UIDs to be substituted
                        ReturnPaths.extend(UIDFinder(TempPaths,Exclusions))
                elif UIDCount == 0 and len(SplitPath) > 2:
                    print("ERROR! Expecting to fill more UIDs")
                #if there are no more UIDs to replace
                else:
                    #we can append our current paths onto our return value
                    ReturnPaths.extend(TempPaths)
        #if this is the last UID replacement and we know it's a filename
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
                #for each file in the current directory
                for file in files:
                    #make sure it's a directory, not a file
                    if os.path.isdir(SplitPath[0] + file):
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
                        ReturnPaths.extend(UIDFinder(TempPaths,Exclusions))
                #our UIDCount is acceptable, and we have more UIDs to find/substitute
                elif UIDCount > 0 and found and UIDCount < len(SplitPath) and UIDCount >= len(SplitPath) - 2:
                    #append the UID substitution string for each UID we still need to find
                    for i in range(0,len(TempPaths)):
                        for j in range(0,UIDCount):
                            TempPaths[i] += '{ UID }' + SplitPath[j+2]
                    #recursively call the function on our updated list of UID substitutions we still need to make
                    ReturnPaths.extend(UIDFinder(TempPaths,Exclusions))
                #if we've found all the UIDs
                elif UIDCount == 0 and found:
                    #if there's still a partial filepath after our UID replacement
                    if len(SplitPath) == 2:
                        #append the partial filepath onto each of our temporary paths
                        for i in range(0,len(TempPaths)):
                            TempPaths[i] += SplitPath[1]
                    #extend our return value with our final filepath after all the UIDs have been substituted/found
                    ReturnPaths.extend(TempPaths)
                #our UIDCount was considered unacceptable, so we return the original filepath we were passed
                else:
                    ReturnPaths.extend(Path)
    #if we didn't find anything to return, return the original paths we were passed
    if ReturnPaths == []:
        ReturnPaths = Paths
    return ReturnPaths


def FindAndVerifySave(ReferencePaths):
    #initialize variables we will be using in our return dictionary
    ReturnList = []
    SaveType = ''
    ReturnType = ''
    ReturnDict = {}
    ReturnTime = 0
    #for each filepath we were passed
    for filepath in ReferencePaths:
        #get a list of directories and create a temporary value to hold each directory name
        Directories = filepath.split('/')
        NonEmptyDirectoryList = []
        for directory in Directories:
            if directory != '':
                NonEmptyDirectoryList.append(directory)
        #if there is at least one directory listed
        if len(NonEmptyDirectoryList) > 0:
            #Check if we're matching to a filename
            if SaveType in ['Filename','Unfound',''] and (NonEmptyDirectoryList[-1][-1] == '*' or ('.' in NonEmptyDirectoryList[-1])):
                temppath = ''

                #create a new filepath preceding our presumed filename or extension we are matching to
                for i in range(0,len(NonEmptyDirectoryList) - 1):
                    temppath += '/' + NonEmptyDirectoryList[i]
                #correct the filename patter we're going to be matching to to be correctly interpreted by our regular expressions
                filename = NonEmptyDirectoryList[-1].replace('.','\.').replace('*','.*')
                #check if the path to our file we're matching to exists
                if os.path.isdir(temppath):
                    #iterate through each file in the directory
                    for file in os.listdir(temppath):
                        #compile our regular expression
                        regexp = re.compile(filename)
                        #if we match on a file
                        if regexp.match(file):
                            #set our SaveType to a filename match, get the time it was last modified, and append the full filepath to our return list
                            SaveType = 'Filename'
                            ReturnPath = temppath + '/' + file
                            if ReturnTime < os.path.getmtime(ReturnPath):
                                ReturnTime = os.path.getmtime(ReturnPath)
                            if ReturnPath.replace('//','/') not in ReturnList:
                                ReturnList.append(ReturnPath.replace('//','/'))
            #Check if we're matching a directory and if it exists
            if os.path.isdir(filepath) and SaveType in ['Directory','Unfound','']:
                #set our savetype to a directory match, get the time it was last modified and append the full filepath to our return list
                #TODO edit the time modified portion to be based on the last time a file within the folder was modified, not the last time a folder was modified
                if SaveType == 'Unfound':
                    ReturnList = []
                SaveType = 'Directory'
                ReturnPath = filepath
                TempTime = max(os.path.getmtime(root) for root,_,_ in os.walk(ReturnPath))
                if ReturnTime < TempTime:
                    ReturnTime = TempTime
                if ReturnPath not in ReturnList:
                    ReturnList.append(ReturnPath)
            #if there's no match on a filename or a directory, we consider the save path passed in to be unfound and add the originally passed in filepath to our return list
            elif SaveType in ['','Unfound']:
                SaveType = 'Unfound'
                ReturnPath = filepath
                if ReturnPath not in ReturnList:
                    ReturnList.append(filepath)
            #Declare our final values for our return dictionary
            ReturnDict['TimeModified'] = ReturnTime
            ReturnDict['SaveType'] = SaveType
            ReturnDict['SavePaths'] = ReturnList
    #if our ReturnDict is still empty, return our original filepaths and declare that we didn't find a save
    if ReturnDict == {}:
        ReturnDict['SaveType'] = 'Unfound'
        ReturnDict['TimeModified'] = 0
        for path in ReferencePaths:
            if path.replace('//','/') not in ReturnDict['SavePaths']:
                ReturnDict['SavePaths'].append(path.replace('//','/'))
    return ReturnDict

#Our function to generate our final dictionary
def GenerateSaveDataDictionary(ApplicationDict):
    #initialize empty values for use later
    SubstitutionDict = {}
    SaveType = ''
    SteamPaths = []
    WindowsPaths = []
    LinuxPaths = []
    SteamList = []
    WindowsList = []
    LinuxList = []
    FinalSaveDict = {}
    TempDict = {}
    found = False
    #initialize our Substitution Dictionary for values we expect from PCGW
    SubstitutionDict['\{\{p\|game\}\}'] = ApplicationDict['InstallDir']
    #Substitution generation for when the game is running through proton instead of natively on linux
    #NOTE these are not native linux folders, so there should be no instances of a native linux save utilizing these substitutions
    if ApplicationDict['GamePlatform'] != ApplicationDict['SystemPlatform']:
        SubstitutionDict['\{\{p\|localappdata\}\}'] = ApplicationDict['CompatDir'] + 'pfx/drive_c/users/steamuser/AppData/Local/'
        SubstitutionDict['\{\{p\|appdata\}\}'] = ApplicationDict['CompatDir'] + 'pfx/drive_c/users/steamuser/AppData/Roaming/'
        SubstitutionDict['\{\{p\|userprofile\\Documents\}\}'] = ApplicationDict['CompatDir'] + 'pfx/drive_c/users/steamuser/My Documents/'
        SubstitutionDict['\{\{Path\|localappdata\}\}'] = ApplicationDict['CompatDir'] + 'pfx/drive_c/users/steamuser/AppData/Local/'
        SubstitutionDict['\{\{p\|userprofile\}\}'] = ApplicationDict['CompatDir'] + 'pfx/drive_c/users/steamuser/'
        SubstitutionDict['\{\{p\|programdata\}\}'] = ApplicationDict['CompatDir'] + 'pfx/drive_c/programdata/'
        SubstitutionDict['\{\{p\|userprofile'] = ApplicationDict['CompatDir'] + 'pfx/drive_c/users/steamuser/'
        SubstitutionDict['\{\{p\|username\}\}'] = ApplicationDict['CompatDir'] + 'pfx/drive_c/users/steamuser/'
    #Substitution generation for when the game is running natively on windows
    #TODO add support for windows in general and correct this to accurately detect the expected folders
    else:
        SubstitutionDict['\{\{p\|localappdata\}\}'] = ''
        SubstitutionDict['\{\{p\|appdata\}\}'] = ''
        SubstitutionDict['\{\{p\|userprofile\\Documents\}\}'] = ''
        SubstitutionDict['\{\{Path\|localappdata\}\}'] = ''
        SubstitutionDict['\{\{p\|userprofile\}\}'] = ''
        SubstitutionDict['\{\{p\|userprofile'] = ''
    #Substitution generation for native linux folders
    if ApplicationDict['SystemPlatform'] == 'Linux':
        SubstitutionDict['\{\{p\|linuxhome\}\}'] = home
        SubstitutionDict['\{\{p\|xdgdatahome\}\}'] = home + '/.local/share/'
        SubstitutionDict['\{\{p\|xdgconfighome\}\}'] = home + '/.config/'
        SubstitutionDict['\{\{p\|steam\}\}'] = home + "/.steam/steam/"
        SubstitutionDict['~'] = home
    
    #Exactly one game that I've found uses this substitution
    #substitution for usage with the windows registry
    #TODO add support for windows registry saves
    SubstitutionDict['\{\{p\|hkcu\}\}'] = '{ HKEY CURRENT USER }'

    #populate our save files we're looking at with information from our passed in dictionary
    #NOTE some games have incorrect or incomplete information on PCGW
    #this is a simple workaround to fix known erroneous entries in PCGW with a precompiled list of replacements
    #replacement list generation is done above with global values currently
    #TODO move these filepath replacements to a dedicated function, move replacement list generation to separate file or function
    if ApplicationDict['AppID'] in ManualFilePathReplacementList:
        SteamSave = ApplicationDict['SteamSavePath'].replace(ManualFilePathReplacementList[ApplicationDict['AppID']]['original'],ManualFilePathReplacementList[ApplicationDict['AppID']]['replacement'])
        WindowsSave = ApplicationDict['WinSavePath'].replace(ManualFilePathReplacementList[ApplicationDict['AppID']]['original'],ManualFilePathReplacementList[ApplicationDict['AppID']]['replacement'])
        LinuxSave = ApplicationDict['LinuxSavePath'].replace(ManualFilePathReplacementList[ApplicationDict['AppID']]['original'],ManualFilePathReplacementList[ApplicationDict['AppID']]['replacement'])
    else:
        SteamSave = ApplicationDict['SteamSavePath']
        WindowsSave = ApplicationDict['WinSavePath']
        LinuxSave = ApplicationDict['LinuxSavePath']
    #replace our PCGW save path information with our corrected local paths
    for substitution in SubstitutionDict:
        SubVar = re.compile(substitution,re.IGNORECASE)
        if SteamSave != 'NULL':
            SteamSave = SubVar.sub(SubstitutionDict[substitution],SteamSave)
        if WindowsSave != 'NULL':
            WindowsSave = SubVar.sub(SubstitutionDict[substitution],WindowsSave)
        if LinuxSave != 'NULL':
            LinuxSave = SubVar.sub(SubstitutionDict[substitution],LinuxSave)
    

    #Special circumstances for UID's, since we don't have any idea what these values will be
    SubVar = re.compile('\{\{p\|uid\}\}',re.IGNORECASE)
    #Always check for the steam save if it's present and no savedata has been found
    if SteamSave != 'NULL' and not found:
        #replace our PCGW instance with a specific string { UID } to make replacement easier on us later on
        SteamSave = SubVar.sub('{ UID }',SteamSave)
        #| from PCGW indicates another savepath, so we split on it to get all of the filepaths we're checking
        SteamSaves = SteamSave.split('|')
        #if we have a UID that we need to fill in, we send our paths to the UIDFinder function
        if '{ UID }' in SteamSave:
            SteamPaths = UIDFinder(SteamSaves,ApplicationDict['FileExclusions'])
        #otherwise we consider this more or less a filepath
        else:
            SteamPaths = SteamSaves
        #sanitize our filepath string to get a filepath we can actually check on the local machine
        TempPaths = GenerateFilepathList(SteamPaths)
        #if we've got at least one steam filepath to check
        if len(TempPaths) > 0:
            SteamPaths = TempPaths
            #pass our paths into the FindAndVerifySave function, which checks for existence of files/folders and determines the save type and last modified time
            TempDict = FindAndVerifySave(SteamPaths)
            #so long as our savetype isn't unfound, we consider the dictionary passsed back by FindAndVerifySave to be our final save dictionary
            if TempDict['SaveType'] != 'Unfound':
                FinalSaveDict = TempDict
    #if our game platform is windows, we have a save path to check against, and we haven't found a save yet, check to see if we can find a local save from the windows path
    if WindowsSave != 'NULL' and ApplicationDict['GamePlatform'] == 'windows' and FinalSaveDict == {}:
        #replace our PCGW instance with a specific string { UID } to make replacement easier on us later on
        WindowsSave = SubVar.sub('{ UID }',WindowsSave)
        #| from PCGW indicates another savepath, so we split on it to get all of the filepaths we're checking
        WindowsSaves = WindowsSave.split('|')
        #if we have a UID that we need to fill in, we send our paths to the UIDFinder function
        if '{ UID }' in WindowsSave:
            WindowsPaths = UIDFinder(WindowsSaves,ApplicationDict['FileExclusions'])
        #otherwise we consider this more or less a filepath
        else:
            WindowsPaths = WindowsSaves
        #sanitize our filepath string to get a filepath we can actually check on the local machine
        TempPaths = GenerateFilepathList(WindowsPaths)
        #if we've got at least one windows filepath to check
        if len(TempPaths) > 0:
            WindowsPaths = TempPaths
            #pass our paths into the FindAndVerifySave function, which checks for existence of files/folders and determines the save type and last modified time
            TempDict = FindAndVerifySave(WindowsPaths)
            #so long as our savetype isn't unfound, we consider the dictionary passsed back by FindAndVerifySave to be our final save dictionary
            if TempDict['SaveType'] != 'Unfound':
                FinalSaveDict = TempDict
    #if our game platform is linux, we have a save path to check against, and we haven't found a save yet, check to see if we can find a local save from the windows path
    if LinuxSave != 'NULL' and ApplicationDict['GamePlatform'] == 'Linux' and FinalSaveDict == {}:
        #replace our PCGW instance with a specific string { UID } to make replacement easier on us later on
        LinuxSave = SubVar.sub('{ UID }',LinuxSave)
        #| from PCGW indicates another savepath, so we split on it to get all of the filepaths we're checking
        LinuxSaves = LinuxSave.split('|')
        #if we have a UID that we need to fill in, we send our paths to the UIDFinder function
        if '{ UID }' in LinuxSave:
            LinuxPaths = UIDFinder(LinuxSaves,ApplicationDict['FileExclusions'])
        #otherwise we consider this more or less a filepath
        else:
            LinuxPaths = LinuxSaves
        #sanitize our filepath string to get a filepath we can actually check on the local machine
        TempPaths = GenerateFilepathList(LinuxPaths)
        #if we've got at least one linux filepath to check
        if len(TempPaths) > 0:
            LinuxPaths = TempPaths
            #pass our paths into the FindAndVerifySave function, which checks for existence of files/folders and determines the save type and last modified time
            TempDict = FindAndVerifySave(LinuxPaths)
            #so long as our savetype isn't unfound, we consider the dictionary passsed back by FindAndVerifySave to be our final save dictionary
            if TempDict['SaveType'] != 'Unfound':
                FinalSaveDict = TempDict
    #if we never populated our final save dictionary, initialize one to return with an unfound save type and the original paths we were passed
    if FinalSaveDict == {}:
        FinalSaveDict['SaveType'] = 'Unfound'
        FinalSaveDict['SavePaths'] = []
        if len(SteamPaths) > 0:
            for path in SteamPaths:
                FinalSaveDict['SavePaths'].append(path)
        if len(WindowsPaths) > 0:
            for path in WindowsPaths:
                FinalSaveDict['SavePaths'].append(path)
        if len(LinuxPaths) > 0:
            for path in LinuxPaths:
                FinalSaveDict['SavePaths'].append(path)
    #initialize a few extra values for our return dictionary from our passed in dictionary
    FinalSaveDict['Title'] = ApplicationDict['Title']
    FinalSaveDict['SteamCloud'] = ApplicationDict['SteamCloud']
    FinalSaveDict['GamePlatform'] = ApplicationDict['GamePlatform']

    return FinalSaveDict



#Outside function call to begin detection of our full library
def DetectLocalGameSaves(PathToSteam, IncludeSteamCloud):
    #import the library and initialize empty values
    l = vdf.load(open(PathToSteam))
    libID = 0
    systemplatform = ""
    libraries = []
    steamsavelibrary = {}
    FinalDict = {}
    #check for the system platform
    #TODO verify this on other systems, add windows support
    if platform == "linux" or platform == "linux2":
        systemplatform = "Linux"
    elif platform == "darwin":
        systemplatform = "macOS"
    elif platform == "win32":
        systemplatform = "Windows"
    #get our paths to each library
    for library in l["libraryfolders"]:
        libraries.append(l["libraryfolders"][library]["path"])
    #for each of our local libraries
    for library in l["libraryfolders"]:
        #get the local filepath to the library
        filepath = l["libraryfolders"][library]["path"]
        #for each application installed at the library
        for application in l["libraryfolders"][library]["apps"]:
            #default the game platform to be that of the system platform
            gameplatform = systemplatform
            compatdir = ""
            #load in the applications installation information from it's app manifest
            f = vdf.load(open(filepath + "/steamapps/appmanifest_" + application +".acf"))
            title = f["AppState"]["name"]
            compatpathlist = []
            #initialize the install directory of the game, by using the current path and then the path to the installed steam applications
            installdir = filepath + "/steamapps/common/" + f["AppState"]["installdir"]
            #if the game's library entry indicates it is running on a non-native system
            if "platform_override_dest" in f["AppState"]["UserConfig"]:
                #if the game is being run through Proton, consider the game platform to be windows
                if f["AppState"]["UserConfig"]["platform_override_dest"] == "linux" and f["AppState"]["UserConfig"]["platform_override_source"] == "windows":
                    gameplatform = "windows"
                #otherwise consider it to be linux
                else:
                    gameplatform = "linux"
            #if we're running a compatibility layer
            if gameplatform != systemplatform:
                #find any associated proton prefixs for the current applications
                for lib in libraries:
                    if (os.path.isdir(lib + "/steamapps/compatdata/" + application)):
                        compatpathlist.append(lib + "/steamapps/compatdata/" + application)
            #generate our request URL for PCGW
            wikiURL = "https://www.pcgamingwiki.com/w/api.php?action=cargoquery&tables=Infobox_game,Cloud&fields=Cloud.Steam,Cloud.GOG_Galaxy,Cloud.Discord,Cloud.Epic_Games_Launcher,Cloud.EA_Desktop,Cloud.OneDrive,Cloud.Ubisoft_Connect,Cloud.Xbox,Infobox_game._pageID=PageID,Infobox_game._pageName=Page,Infobox_game.Developers,Infobox_game.Released,Infobox_game.Cover_URL&join_on=Infobox_game._pageID=Cloud._pageID&where=Infobox_game.Steam_AppID%20HOLDS%20%22" + application + "%22&format=json"
            #make our json request to PCGW
            r = requests.get(wikiURL)
            #if our request was a success, unpack the request into a new value we can work with
            if 'cargoquery' in r.json():
                cargo = r.json()['cargoquery']
            #if our request didn't succeed, print the error causing request, url and application id, and nullify our cargo value to indicate we don't have any cargo to work with
            else:
                print(r.json())
                print(wikiURL)
                print(application)
                cargo = {}
            #initialize empty/placeholder values
            steamcloud = 'Unknown'
            pageID = 'Unknown'
            q = ""
            #if we got a correct response from PCGW
            if len(cargo) > 0:
                #check for steam cloud sync on the current app id
                steamcloud = cargo[0]['title']['Steam']
                #get our page id from the initial PCGW request
                pageID = cargo[0]['title']['PageID']
                #make a new request for the full save path information from PCGW with our newly obtained page id
                q = requests.get("https://www.pcgamingwiki.com/w/api.php?action=parse&format=json&pageid=" + pageID + "&prop=wikitext")
            #check to make sure we haven't loaded the current application into our steamsavelibrary
            if application not in steamsavelibrary:
                #populate values for our local application data in our local dictionary
                steamsavelibrary[application] = {}
                steamsavelibrary[application]['Title'] = title
                steamsavelibrary[application]['InstallDir'] = installdir
                steamsavelibrary[application]['AppID'] = application
                steamsavelibrary[application]['SteamCloud'] = steamcloud
                steamsavelibrary[application]['PageID'] = pageID
                steamsavelibrary[application]['CompatDir'] = '{ PROTON PREFIX }'
                steamsavelibrary[application]['GamePlatform'] = gameplatform
                steamsavelibrary[application]['SystemPlatform'] = systemplatform
                #check if our application has any hardcoded filename exclusions
                #used to prevent filename matches when the filename pattern from PCGW may match systemm or game files as well
                if application in FileExclusionList:
                    steamsavelibrary[application]['FileExclusions'] = FileExclusionList[application]
                else:
                    steamsavelibrary[application]['FileExclusions'] = []
                #initalize empty value for our proton prefix
                CompatPath = ''
                #get our final compatibility/proton prefix path for our current application
                if gameplatform != systemplatform:
                    for i in compatpathlist:
                        #prioritize the compatibility directory closed to the game's install directory
                        #i.e. if multiple steam libraries are present and multiple compatibility paths are found for this game, prioritize the one in the same location as the game's install folder
                        if i.replace('compatdata/' + application,'') in installdir:
                            CompatPath = i +'/'
                    if CompatPath == '' and len(compatpathlist) != 0:
                        CompatPath = compatpathlist[0] + '/'
                    if CompatPath != '':
                        steamsavelibrary[application]['CompatDir'] = CompatPath
                    #if we may need a proton prefix but none was found, substitute in an easily catchable string instead
                    else:
                        steamsavelibrary[application]['CompatDir'] = '{ PROTON PREFIX }/'
                #initialize empty values for our savepaths
                steamsavelibrary[application]['WinSavePath'] = 'NULL'
                steamsavelibrary[application]['SteamSavePath'] = 'NULL'
                steamsavelibrary[application]['LinuxSavePath'] = 'NULL'
            #if we got a correct response from PCGW for our final request
            if q != "":
                #search our json output for the string indicating savedata
                #lots of weird formatting here specific to working with PCGW and pulling data from it's full response
                search = q.json()['parse']['wikitext']['*']
                m = re.search('===Save game data location===[\S\n ]+?===.+===',search)
                if m:
                    #searching for saves by each platform
                    windowssave =re.search("Windows\|.+\}\}",m.group())
                    steamsave = re.search("Steam\|.+\n",m.group())
                    linuxsave = re.search("Linux\|.+\n",m.group())
                    #pulls the raw data for the related section if it finds references to the related platform
                    if windowssave:
                        windowspath = re.search('\{\{.+\}\}',windowssave.group())
                        windowsprefix = re.search('\{\{.+?\}\}',windowssave.group())
                        if windowspath:
                            steamsavelibrary[application]['WinSavePath'] = windowspath.group()
                    if steamsave:
                        steampath = re.search('\{\{.+\}\}',steamsave.group())
                        steamprefix = re.search('\{\{.+?\}\}',steamsave.group())
                        if steampath:
                            steamsavelibrary[application]['SteamSavePath'] = steampath.group()
                    if linuxsave:     
                        if linuxsave.group()[6] == '~':
                            linuxpath = re.search('\~.+\}\}',linuxsave.group())
                        else:
                            linuxpath = re.search('\{\{.+\}\}',linuxsave.group())
                        linuxprefix = re.search('\{\{.+?\}\}',linuxsave.group())
                        if linuxpath:
                            steamsavelibrary[application]['LinuxSavePath'] = linuxpath.group()
            #initialize a value to indicate we found at least one save path
            SavePathFound = (steamsavelibrary[application]['LinuxSavePath'] != 'NULL' or steamsavelibrary[application]['WinSavePath'] != 'NULL' or steamsavelibrary[application]['SteamSavePath'] != 'NULL')
            #get this applications steam cloud status in a boolean
            #if the game supports steam cloud it's true, if not it's false
            SteamCloud = (steamsavelibrary[application]['SteamCloud'] == 'true')
            #check if we're including steam cloud games in our local save detection or not
            #TODO add in dummy data for games where no save data was found
            if IncludeSteamCloud:
                #check to make sure we found at least one save path to check and our application isn't excluded
                if str(application) not in exclusionlist and SavePathFound:
                    FinalDict[application] = GenerateSaveDataDictionary(steamsavelibrary[application])
            #if steam cloud games aren't included, we also need to check the steam cloud value
            else:
                #check to make sure we found at least one save path to check and our application isn't excluded, and it's not supported by SteamCloud
                if str(application) not in exclusionlist and SavePathFound and not SteamCloud:
                    FinalDict[application] = GenerateSaveDataDictionary(steamsavelibrary[application])
    return FinalDict




SteamPath = home + "/.steam/steam/steamapps/libraryfolders.vdf"
SteamSaveLibrary = DetectLocalGameSaves(SteamPath, False)

for App in SteamSaveLibrary:
    if SteamSaveLibrary[App]['SaveType'] != 'Unfound':
        print("Application: " + App)
        print("Title: " + SteamSaveLibrary[App]['Title'])
        print("SaveType: " + SteamSaveLibrary[App]['SaveType'])
        print("Save Paths: ")
        for path in SteamSaveLibrary[App]['SavePaths']:
            print(path)
        print("Time Modified: " + str(time.ctime(SteamSaveLibrary[App]['TimeModified'])))
        print("")






