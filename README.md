# SteamSync
## Description
This is a tool to backup and sync Steam Save Games that do not support Steam Cloud across Linux PCs. This tool is intended to be used with games that do not support steam cloud, and usage with games that support it may cause unexpected behavior. NOTE: this is still beta software and bugs are expected, use at your own risk! This software can and will overwrite existing game saves, and I am not responsible if your usage results in loss of game save data. 
## Requirements
These are required on all PCs you intend to use with this software. Additional steps may be required on some systems.
- Python
- pip
- requests
- vdf

    $ pip install vdf
    $ pip install requests

## Installation
First clone this github repository to a local directory

    $ git clone https://github.com/Quietek/SteamSync.git

Next move the downloaded folder to the desired location of your Save Game Backups and change the working directory to your new folder (example path of /run/media/deck/USB1 shown):

    $ mv SteamSync /run/media/deck/USB1/
    $ cd /run/media/deck/USB1/SteamSync/

Make SteamSync.py and setup.py executable:

    $ chmod +x SteamSync.py
    $ chmod +x setup.py

Run setup.py to initialize the database, followed by SteamSync.py and follow the prompts to create the necessary local configuration files and run your first SaveGame Backup

    $ python setup.py
    $ python SteamSync.py

## Usage
After initial setup navigate to the directory where you saved the folder from Github, and run SteamSync.py to sync your game saves, it will automatically prompt you again to add a new client when used with an unrecognized PC.

    $ cd /run/media/deck/USB1/SteamSync/
    $ python SteamSync.py

