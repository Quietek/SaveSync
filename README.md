# SteamSync
## Description
This is a tool to sync Steam Save Games across PCs, regardless of if they support Steam Cloud saves or not. This tool is intended to be used with games that do not support steam cloud, and usage with games that support it may cause unexpected behavior. NOTE: this is still beta software and bugs are expected, use at your own risk! Additionally, the current iteration of this software will only backup files, not overwrite local files. More testing is required before allowing it to potentially overwrite local game saves!
## Requirements
Python
## Installation
First clone this github repository to a local directory
$ git clone

Next move the downloaded folder to the desired location and change the working directory to your new folder:
$ mv SteamSync /mnt/USB1/
$ cd /mnt/USB1/SteamSync

Make SteamSync.py and setup.py executable:
$ chmod +x SteamSync.py
$ chmod +x setup.py

Run setup.py to initialize the database, followed by SteamSync.py to create the necessary local configuration files and run your first SaveGame Backup
$ python setup.py
$ python SteamSync.py

## Usage
After initial setup simply navigate to the directory where the executables are located, and run SteamSync.py
$ cd .../SteamSync/
$ python SteamSync.py

