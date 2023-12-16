
# SaveSync

## Description
This is a tool to backup and sync Save Games and ROMs across multiple linux PCs, making it easier to keep your systems on the same save versions. It's primarily targeted towards Steam games that don't support Steam Cloud, but has built in functionality to backup cartridge ROM Game saves in your ROMs folder, as well as functionality to sync any non-Steam games you may have as well. This doesn't require more than one PC, and can also easily be used as a tool to simply backup your game saves for an OS reinstall or to move them to a new computer or just for peace of mind! This software also supports rolling back saves, so if you're ever worried about getting soft locked in a game or having a corrupted save file, you should always have the option to roll back your game save to an earlier version.

## Features
- Automatically back up saves for steam games based on information from PC Gaming Wiki.
- Automatically back up emulator saves, bios, and firmware based on their default local or flatpak paths.
- Keep saves in sync across multiple machines, even if they don't support steam cloud.
- Keep ROM folders in sync across multiple machines.
- Save version history.
- Save Rollback/Restoration.
- Manually specified non-Steam game save backups.
- Automatic detection of non-Steam game saves across multiple clients after the first manual addition, including those installed to differing proton prefixes across multiple clients.

## Disclaimers
This is beta software being developed by one person in their free time, bugs are expected. If you encounter a bug and are looking for help, please consider submitting a bug report or opening an issue on github. Many of these features have been minimally tested, so you may encounter issues where I haven't. Games that generate PC-specific save files are unsupported. Using this software in conjunction with games that are enabled for Steam Cloud may cause unexpected behavior. 

## Appimage Release
A newly compiled appimage has been released, it is no longer recommended to directly use the python code in this repository. Instead simply download the appimage from the releases page, then run:

	$ mkdir SaveSync
        $ mv savesync.AppImage SaveSync/
	$ cd SaveSync/
	$ chmod +x savesync.AppImage
	$ ./SaveSync.AppImage

### To run a full system sync run:
	$ ./SaveSync.AppImage --sync
        
### To add a non-steam game to the SaveSync database: 
	$ ./SaveSync.AppImage --add 'title={ INSERT TITLE HERE }' 'path={ INSERT PATH TO SAVE FILE(s) HERE }'

### To get a list of all known games in the database:
	$ ./SaveSync.AppImage --list

### To manually add or modify an undetected game path:
	$ ./SaveSync.AppImage --add 'appid={ INSERT APPID HERE }' 'path={ INSERT PATH TO SAVE FILE(s) HERE }'
    NOTE: replace the AppID with the gameID for non-steam games.

### To use most other functions, run without command line arguments.
	$ ./SaveSync.AppImage


To uninstall simply delete the SaveSync folder and the configuration file/directory. This will also delete all your backed up saves, so make sure you've gotten any you need out of the SaveSync folder before deleting. 
	   
    $ rm -r ./SaveSync
    $ rm -r ~/.config/SaveSync

If you use a systemd service to run your syncs, you will need to disable it and remove the relevant .service file.
    
    $ systemctl --user disable SaveSyncOnMount.service
    $ rm ~/.config/systemd/SaveSyncOnMount.service

## Usage
After initial setup navigate to the directory where you saved the folder from Github, and run SaveSync.py --sync to sync your folder. Make sure to run SaveSync.py without command line arguments at least once on each PC you use SaveSync with, this is so that it can prompt you again to add a new client when used with an unrecognized PC.


The interactive database manager can be used to handle all the following functionality, save rollback, and manual database edits. Running the interactive database manager is the default behavior for SaveSync after the first run of the program.

    $ python SaveSync.py

#### Command Line Arguments

If you're ever stuck, or want more information on what the interactive manager lets you do, use the --help command line argument.

    $ python SaveSync.py --help

If you want to run a sync comparing the backed up saves with what's on your computer, use the --sync command line argument. 

    $ python SaveSync.py --sync

If you want to add a non-Steam game to the database or specify a custom save path for an existing non-Steam game, use the --add command line argument. Note that you should only need to use the first one, unless you have your games installed in an unexpected location (This generally includes Wine games not installed via proton into compatdata or via wine into $HOME/Games, game saves that are located outside your home directory, and emulator saves located outside of the default path)

    $ python SaveSync.py --add 'title={ INSERT TITLE HERE }' 'path={ INSERT PATH TO SAVE FILE(s) HERE }'
    $ python SaveSync
If you want to get a list of games in the database, which includes all known GameIDs and AppID's, use the --list command line argument.
    
    $ python SaveSync.py --list

Additionally, if you have SaveSync on a removable drive and plan to remove it immediately after a sync has completed, you may need to run an additional command to make sure that the data has indeed finished copying and isn't still in the buffer. This is mostly only needed if you're copying over large amounts of data such as large ROM folders. This command will produce no output, but will not finish executing until the buffer has been completely written to the removable drive.
   
     $ sync


## Supported Emulators

This is a list of emulators that support automatic save, bios, and firmware detection and backup based on their default linux and flatpak save locations.

- zsnes
- mupen64plus
- Duckstation
- PCSX2
- RPCS3 [No firmware/bios sync]
- ryujinx
- yuzu

If you know of another commonly used emulator, especially if it's for a system that isn't covered by these, consider submitting an issue/bug report with any information you can provide about it's default save game locations.

## F.A.Q.

#### Why should I use this?
Many games on Steam still do not support steam cloud saves, meaning that there's no recourse if you end up losing access to that game's save data from an OS reinstall, a lost device, data corruption, or soft locking yourself in a game. While this is mostly relevant to older games, there are still some AA and AAA newer games that don't release with cloud save support, some notable games that don't support cloud saves in my own library include Dark Souls 2 and 3, the Quarry, Sleeping Dogs, and a variety of retro games. This software is here to make keeping your games that don't support steam cloud in sync with each other across multiple linux computers, store multiple backups of your game saves, and keep your game saves for games from outside of Steam backed up/synced as well.

#### Do I need multiple PCs to get use out of this?
Nope! SaveSync can work great as a simple save backup tool, and can absolutely be run on only one computer if you want to keep backups of your saves in case of an OS reinstall, a drive failure, or any number of other reasons. It also offers save rollback, which may come in handy if you find yourself soft locked in a game or with a corrupted save file on your system.

#### Where am I intended to put the SaveSync folder?
The SaveSync folder is intended to be placed on a removable drive such as a flash drive or an SD card. I personally have been keeping it on my Steam Deck's sd card. It can be placed and used anywhere though, so you can place it on a NAS or even just somewhere generic on your PC's SSD/HDD.

#### Is this software compatible with Windows?
No, and it probably won't be for a while, if ever. My priority is on compatibility with the Steam Deck and general Linux PCs, since those are what I actually use on a daily basis, and many use cases for this with the Steam Deck in particular would have you placing SaveSync on a drive with a filesystem format that windows doesn't support.

#### Is there a Decky plugin for this?
Not currently, I have considered making one, but the last time I took a look, much of decky was still undocumented.  Also, until I feel better about the state of testing and bugs, I want this project to prioritize general linux compatibility rather than focusing on steam deck specific features. I may revisit this later though.


#### Where are the backed up files located?
- Backed up Steam saves will be located at ./SteamSaves/[AppID]/[Timestamp]
- Backed up non-Steam saves will be located at ./NonSteamSaves/[GameID]/[Timestamp]
- Backed up ROM saves will be located at ./ROMSaves/[Filename]/Timestamp
- Backed up ROMs will be located at ./ROMs/

#### What's the difference between all the different save types?
- A Steam save is always from an installed Steam game. This does not include games that are added to steam as non-Steam games or games installed directly into a proton directory.
- A Non-Steam save is any save file that you manually specify that isn't installed through steam. This could be the path to an emulator's save data for example, or really any game you're willing to manually locate the save data for that you don't own on Steam. This includes games that were installed into a proton directory or added as non-Steam games.
- A ROM Save file is a save file that is located in the same directory as the ROM itself. This is generally specific to cartridge based systems that stored their game saves on the cartridge. These are distinguished from normal ROMs by their save extensions. Currently supported ROM Save extensions include .sav, .eep, .fla, .srm, and .ss\*. if you know of a file extension that should be treated as a save instead of a ROM, please consider letting me know on GitHub.

#### What's an AppID and a GameID and how do I find them?
The AppID is Steam's way of keeping track of which games are which within the steam database. It's a numerical value that won't be changed and will always refer to the same game. A GameID is a custom value created specifically for 
275
7. Check "Force the use of a specific Steam Play compatibility tool" you can change the proton version if you want to, but most games will likely work fine with the default.

	$ python SaveSync.py --list
	
If you need to reference an AppID that isn't registered to the SaveSync database, you're best bet is to search for it here: https://steamdb.info/apps/ or you can get it from the url of the steam store page, which has it's urls formatted like  this: https://store.steampowered.com/app/[APPID]/[Title]

#### How do I manually add an undetected Steam Game?
The interactive Database Manager will help you with that, specifically use option 8 from the main menu, and type the AppID of the game you want to manually specify a path for.

#### I'm using the interactive database manager and it's making references to prefixes and suffixes, what are they?
The prefix is the path before a potential split in the filepath, while the suffixes are the paths after it. Any game that has a unique UserID/Profile in the path will be treated as the prefix being the portion before the UserID, and the suffix being the portion after it. New UserIDs should be automatically detected and backed up. If a game doesn't have a UserID associated with it, the prefix will be the full filepath.

An example to demonstrate can be seen with the game Heroes of Might and Magic V. This game allows users to create individually create profiles, each of which has it's own saves, and the paths to get to each profiles saves would be something like:

1. ~/.local/steam/steamapps/compatdata/15170/pfx/drive\_c/users/steamuser/Documents/My Games/Heroes of Might and Magic V/Profiles/USER1/Saves/
2. ~/.local/steam/steamapps/compatdata/15170/pfx/drive\_c/users/steamuser/Documents/My Games/Heroes of Might and Magic V/Profiles/USER2/Saves/

So, we take the filepath from before where it splits as the prefix, and the parts after as our suffixes. So our values would look like:

##### Prefix: 
- ~/.local/steam/steamapps/compatdata/15170/pfx/drive\_c/users/steamuser/Documents/My Games/Heroes of Might and Magic V/Profiles/
##### Suffixes:
- USER1/Saves/
- USER2/Saves/

#### How does adding multiple ROM folders work?
The purpose of adding multiple ROM Folders would be if you want some of your ROM files in one location, while you want the others in another, or you want to include/exclude specific folders on sync. For example, if you want your gba ROMs in ~/Games/gba/, but you want all your other roms in ~/ROMs/, You can specify a new ROM subfolders by adding/verifying the existence of lines to your config that looks like this: 

- ROMs:gba=\~/Games/gba/ 
- ROMs=\~/ROMs/

Or with a more generic notation:

- ROMs={ PATH WHERE YOU WANT ALL YOUR UNSPECIFIED ROMS/SUBFOLDERS }
- ROMs:{ SUBFOLDER NAME }={ PATH TO WHERE YOU  WANT THOSE ROMS }
 
If you want to only sync a specific subfolder on a client, you should leave the portion after the = sign for your root ROM folder blank, and use the subfolder notation as normal like so:
- ROMs=
- ROMs:{ SUBFOLDER NAME }={ PATH TO WHERE YOU  WANT THOSE ROMS }

Or if you want to sync all, excluding a specific folder:
- ROMs={ PATH WHERE YOU WANAT YOUR UNSPECIFIED ROMS/SUBFOLDER}
- ROMs:{ EXCLUDED SUBFOLDER }=

There is also a helper function within the interactive database manager, specifically option #3 on the main menu, but the helper function does not currently support explicit folder inclusion/exclusion.

#### Why do I have to run this from the command line? Wouldn't it be easier/nicer to have a full blown GUI?
My background is mostly in data analytics, and simply put I have very little experience with UI coding or design. The priority was also getting this working on the command line since that makes it easy tu run in the background and it should improve compatibility across linux distributions. I may attempt to code in a GUI eventually, but I make no guarantees.

#### How do I install a Windows game with Proton so that it gets automatically detected by SaveSync on new clients?
- NOTE this is not inclusive of every game, and some games may require you to install additional components via protontricks, winetricks, or a custom proton or wine version.
- Also, I know this guide probably sucks to follow without any visuals or anything, I do plan to make a new one in the relatively near future with actual screenshots.
1. Within Steam, click add a game in the lower left hand corner. You will need to be in Desktop Mode if you're on the steam deck.
2. Click browse on the newly opened window.
3. Navigate it to your game's installer OR executable, depending on if you need to run an installer or already have all the game's data installed somewhere. NOTE: it is recommended to install your games directly to the C: drive within proton instead of installing them to a custom directory within your linux install, this is because a fairly significant number of games keep their saves in the same directory as the game, which may not be detected correctly if your game is installed outside of the proton or wine prefix.
4. Select the game's installer or executable, and click add game afterwards.
5. Right click the newly added game in your steam library and click on properties.
6. Go to Compatibility.
7. Check "Force the use of a specific Steam Play compatibility tool" you can change the proton version if you want to, but most games will likely work fine with the default.
8. Exit out of the properties box.
9. Click play on your newly added game, and go through the installation prompts if you're running an installer, then close the game/installer afterwards.
10. [OPTIONAL] go back into the properties of your non-Steam game, select "Browse..." again, and navigate to the installers for any mods, patches, or other executables you need to run related to the game. This is only relevant to mods and patches that are installed via a .exe file, if the game simply requires a file to be dropped somewhere, you can do so by navigating to the game's mod directory by referencing the path on windows and using that after the drive\_c portion of the game's filepath we'll get later.
11. Open up a file explorer
12. Navigate to your steam install, then go to steamapps/compatdata/
13. Look for numbers that are especially large compared to the others, generally these will be in the 1,000,000,000+ range
14. Click on each of these large numbered folders, and go into the folder labeled pfx. Try to navigating to where you expect the game save to be on Windows, except replacing C:/ with the path to the drive\_c directory and the Windows username with steamuser. Make a note of the full filepath to the saves or copy it into your clipboard. If your game didn't generate the save filepath immediately, it may be necessary to check each folder for the game's install directory instead, with the same C: and username substitutions.
15. [ONLY REQUIRED IF YOU RAN AN INSTALLER] Go back into steam, right click the non-Steam game you're trying to sync, click "Browse..." under the "Start In" section, and navigate to the folder where your game was installed, this will be in the same numbered folder as the one you just found as long as the game was installed on the C: drive. Select the game's primary launch executable.
16. [ONLY REQUIRED IF YOU RAN AN INSTALLER] Launch the game, some games may require you to save once as well to create the necessary directories/files for saves to be detected, but most should create the necessary directores just by running the game.
17. Run this command from the command line, substituting in the Game Title and the path to the game's save. 

		$ python SaveSync.py --add title={ GAME TITLE HERE } path={ PASTE PATH TO GAME SAVE HERE }

18. run a sync from the command line.

		$ python SaveSync.py --sync

19. Your game save should now be correctly backed up and should be automatically detected on other clients where the game is installed through Proton. Unfortunately you may have to search for which compatdata directory your non-Steam game gets installed to on each new install to change the shortcut to the the game launcher, but you (hopefully) shouldn't have to add it to SaveSync again. This is necessary because in order to launch the game (if you used an exe installer) you'll need to change the referenced exe in the steam shortcut, and you may need to also launch the game before the save directories needed for automatic detection get created.
- Games can also be installed through lutris as well and should be detected if they're in the $HOME/Games folder that lutris defaults it's wine prefixes to. The process to sync these games is the same, but instead of searching for the first path to the game's save files within your steam compatdata folder, you're going to be looking in $HOME/Games/[Game Title] instead. Games installed via lutris remain largely untested.

If a game's save directory isn't being detected on new machines, you can manually add the relevant path with the --add command line argument, referencing the GameID of the game you are syncing.

                $ python SaveSync.py --add gameid={ GAMEID HERE } path={ PASTE PATH TO GAME SAVE HERE }

#### Can I run SaveSync from the Steam Deck's game mode?
I would encourage you to use the provided systemd service file as opposed to running it as a dedicated application in steam, but I believe there should be no reason why you can't add SaveSync.py as an application so long as you make sure it's executable, though you may need to take extra steps to get the command line to pop up when you do.

#### A Steam game's save data isn't getting detected, what do I do?
This is likely because the entry on PC Gaming Wiki is either incorrect, incomplete, or entirely missing. If you can, it is highly encouraged to update/create the wiki page with the relevant save game information if you can. That said, there are cases where that either won't help or isn't a simple thing to do, so you can also manually update the entry in the database using the interactive database manager.


#### A folder that shouldn't be considered a save is getting detected as a save, what do I do?
If there's an incorrect folder being synced, it is likely because the UserID portion of the specified filepath is located in a folder with both UserID and non-UserID directories. These are manually excluded by SaveSync currently. Please let me know on GitHub if you find a game with this problem, so far the only ones I have found are Metro 2033 and Metro Last Light.

#### How can I help/contribute to the project?
Just using the software and helping identify any bugs you encounter is a big help! If you find something not working correctly, taking some time to submit a bug report would be a big help in squashing remaining issues and incompatibilities.

Also consider contributing to PC Gaming Wiki, it's a robust resource but there are always things that may be inaccurate or missing from the wiki, and any contributions you can make would help both this project and PC Gaming wiki as a whole!

This project is completely open source, so if you're ambitious enough you can absolutely feel free to fork the repository and program your own features! We can also merge in any community-created features that are especially useful. 

I will never ask you to pay for any open source software I develop on Github, but donations do help keep open source software alive and are always greatly appreciated. If you are generous enough to want to support the project monetarily, donations can be made here: https://www.buymeacoffee.com/TFTanner

## License
This software is licensed with the GNU General Public License v3, see LICENSE for more details.
