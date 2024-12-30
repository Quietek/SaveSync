#!/usr/bin/env python
import os
import time
import json
import requests
import vdf
import re
import time
import sqlite3
from SQLFunctions import *
from ClientFunctions import *
from sys import platform


def GenerateFileExclusions():
    print("Generating file exclusion values...")
    ExistingExclusions = SQLGetEntry('FileExclusions',{})
    KnownAppIDList = []
    for val in ExistingExclusions:
        if val not in KnownAppIDList:
            KnownAppIDList.append(val['AppID'])
    #This Function is used to create a list of folder or file names that should be ignored when UID Finder is called
    #Metro 2033 and Metro Last Light both have folders that need to be ignored, titled 2033 and pc respectively
    if 287390 not in KnownAppIDList:
        SQLCreateEntry('FileExclusions',{'AppID':287390, 'Filename':'pc'})
    if 286690 not in KnownAppIDList:
        SQLCreateEntry('FileExclusions',{'AppID':286690, 'Filename':'2033'})
    if 2835570 not in KnownAppIDList:
        SQLCreateEntry('FileExclusions',{'AppID':2835570, 'Filename':'shader_cache'})
        SQLCreateEntry('FileExclusions',{'AppID':2835570, 'Filename':'vulkan'})
    #Star Wars X-Wing Alliance matches on .plt files, but we can ignore the test files
    if 361670 not in KnownAppIDList:
        SQLCreateEntry('FileExclusions',{'AppID':361670, 'Filename':'Test0.plt'})
        SQLCreateEntry('FileExclusions',{'AppID':361670, 'Filename':'Test1.plt'})
    print("Finished generating file exclusions!")
    return 0

def GenerateSkippedGames():
    #This Function is used to create a list of games that are always skipped in the databasei
    #This prevents unnecessary PCGW Requests each time we run this, since a missing PCGW page doesn't necessarily indicate that it should always be skipped
    ExistingEntries = SQLGetEntry('SteamApps',{})
    print("Generating list of auto-skipped Steam games...")
    KnownAppIDList = []
    for val in ExistingEntries:
        if val not in KnownAppIDList:
            KnownAppIDList.append(int(val['AppID']))
    #Hyper Light Drifter uses PC specific save files
    if 257850 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':257850, 'AlwaysSkipped':1, 'Title':'Hyper Light Drifter'})
    #Valve games with no local save data
    if 10 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':10, 'AlwaysSkipped':1, 'Title':'Counter-Strike'})
    if 20 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':20, 'AlwaysSkipped':1, 'Title':'Team Fortress Classic'})
    if 30 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':30, 'AlwaysSkipped':1, 'Title':'Day of Defeat'})
    if 40 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':40, 'AlwaysSkipped':1, 'Title':'Deathmatch Classic'})
    if 60 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':60, 'AlwaysSkipped':1, 'Title':'Ricochet'})
    if 240 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':240, 'AlwaysSkipped':1, 'Title':'Counter-Strike: Source'})
    if 320 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':320, 'AlwaysSkipped':1, 'Title': 'Half-Life 2: Deathmatch'})
    if 360 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':360, 'AlwaysSkipped':1, 'Title': 'Half-Life Deathmatch: Source'})
    if 300 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':300, 'AlwaysSkipped':1, 'Title':'Day of Defeat: Source'})
    if 570 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':570, 'AlwaysSkipped':1, 'Title':'Dota 2'})
    if 440 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':440, 'AlwaysSkipped':1, 'Title':'Team Fortress 2'})
    if 583950 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':730, 'AlwaysSkipped':1, 'Title':'Counter-Strike: Global Offensive'})
    if 583950 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':583950, 'AlwaysSkipped':1, 'Title':'Artifact'})
    if 1269260 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':1269260, 'AlwaysSkipped':1, 'Title':'Artifact Foundry'})
    #Other Always online games or games that have no save data associated
    if 331670 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':331670, 'AlwaysSkipped':1, 'Title':'The Jackbox Party Pack'})
    if 1172470 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':1172470, 'AlwaysSkipped':1, 'Title':'Apex Legends'})
    if 1085660 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':1085660, 'AlwaysSkipped':1, 'Title':'Destiny 2'})
    if 761890 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':761890, 'AlwaysSkipped':1, 'Title':'Albion Online'})
    if 120440 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':120440, 'AlwaysSkipped':1, 'Title':'Halo Infinite'})
    if 230410 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':230410, 'AlwaysSkipped':1, 'Title':'Warframe'})
    if 8500 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':8500, 'AlwaysSkipped':1, 'Title':'EVE Online'})
    if 238960 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':238960, 'AlwaysSkipped':1, 'Title':'Path of Exile'})
    if 386360 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':386360, 'AlwaysSkipped':1, 'Title':'Smite'})
    if 1286830 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':1286830, 'AlwaysSkipped':1, 'Title':'Star Wars: The Old Republic'})
    if 578080 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':578080, 'AlwaysSkipped':1, 'Title':'PUBG: Battlegrounds'})
    if 159340 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':159340, 'AlwaysSkipped':1, 'Title':'Lost Ark'})
    if 552990 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':552990, 'AlwaysSkipped':1, 'Title':'World of Warships'})
    if 1449850 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':1449850, 'AlwaysSkipped':1, 'Title':'Yu-Gi-Oh: Master Duel'})
    if 1284210 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':1284210, 'AlwaysSkipped':1, 'Title':'Guild Wars 2'})
    if 601510 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':601510, 'AlwaysSkipped':1, 'Title':'Yu-Gi-Oh: Duel Links'})
    if 2064650 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':2064650, 'AlwaysSkipped':1, 'Title':'Tower of Fantasy'})
    if 1343400 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':1343400, 'AlwaysSkipped':1, 'Title':'Runescape'})
    if 1407200 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':1407200, 'AlwaysSkipped':1, 'Title':'World of Tanks'})
    if 218230 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':218230, 'AlwaysSkipped':1, 'Title':'PlanetSide 2'})
    if 1997040 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':1997040, 'AlwaysSkipped':1, 'Title':'Marvel Snap'})
    if 1056640 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':1056640, 'AlwaysSkipped':1, 'Title':'Phantasy Star Online 2'})
    if 438100 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':438100, 'AlwaysSkipped':1, 'Title':'VRChat'})
    if 444090 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':444090, 'AlwaysSkipped':1, 'Title':'Paladins'})
    if 39210 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':39210, 'AlwaysSkipped':1, 'Title':'Final Fantasy XIV'})
    if 331670 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':397460, 'AlwaysSkipped':1, 'Title':'The Jackbox Party Pack 2'})
    if 434170 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':434170, 'AlwaysSkipped':1, 'Title':'The Jackbox Party Pack 3'})
    if 610180 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':610180, 'AlwaysSkipped':1, 'Title':'The Jackbox Party Pack 4'})
    if 774461 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':774461, 'AlwaysSkipped':1, 'Title':'The Jackbox Party Pack 5'})
    if 257850 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':1005300, 'AlwaysSkipped':1, 'Title':'The Jackbox Party Pack 6'})
    if 1211630 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':1211630, 'AlwaysSkipped':1, 'Title':'The Jackbox Party Pack 7'})
    #Various Steam and proton executables which don't have save data associated
    if 228980 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':228980, 'AlwaysSkipped':1, 'Title':'Steamworks Common Redistributables'})
    if 1070560 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':1070560, 'AlwaysSkipped':1, 'Title':'Steam Linux Runtime'})
    if 1391110 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':1391110, 'AlwaysSkipped':1, 'Title':'Steam Linux Runtime - Soldier'})
    if 1493710 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':1493710, 'AlwaysSkipped':1, 'Title':'Proton Experimenta'})
    if 1826330 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':1826330, 'AlwaysSkipped':1, 'Title':'Proton EasyAntiCheat Runtime'})
    if 1628350 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':1628350, 'AlwaysSkipped':1, 'Title':'Proton Steam Linux Runtime - Sniper'})
    if 1161040 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':1161040, 'AlwaysSkipped':1, 'Title':'Proton BattlEye Runtime'})
    if 2180100 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':2180100, 'AlwaysSkipped':1, 'Title':'Proton Hotfix'})
    if 2230260 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':2230260, 'AlwaysSkipped':1, 'Title':'Proton Next'})
    if 961940 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':961940, 'AlwaysSkipped':1, 'Title':'Proton 3.16'})
    if 858280 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':858280, 'AlwaysSkipped':1, 'Title':'Proton 3.7'})
    if 1113280 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':1113280, 'AlwaysSkipped':1, 'Title':'Proton 4.11'})
    if 1054830 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':1054830, 'AlwaysSkipped':1, 'Title':'Proton 4.2'})
    if 1245040 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':1245040, 'AlwaysSkipped':1, 'Title':'Proton 5.0'})
    if 1420170 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':1420170, 'AlwaysSkipped':1, 'Title':'Proton 5.13'})
    if 1580130 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':1580130, 'AlwaysSkipped':1, 'Title':'Proton 6.3'})
    if 1887720 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':1887720, 'AlwaysSkipped':1, 'Title':'Proton 7.0'})
    if 2348590 not in KnownAppIDList:
        SQLCreateEntry('SteamApps',{'AppID':2348590, 'AlwaysSkipped':1, 'Title':'Proton 8.0'})
    print("List finished generating!")
    return 0

def GenerateAutoDetectedNonSteamGames():
    print("Generating list of auto-detected non-Steam games...")
    ExistingEntries = SQLGetEntry('SteamApps',{})
    KnownGameIDList = []
    for val in ExistingEntries:
        if val not in KnownGameIDList:
            KnownGameIDList.append(val['AppID'])
    #Emulator Auto Detection
    if 9999 not in KnownGameIDList:
        SQLCreateEntry('NonSteamApps',{'GameID': 9999, 'Title': 'Dolphin Gamecube Saves', 'RelativeSavePath': '{ HOME }.local/share/dolphin-emu/GC/', 'MostRecentSaveTime': 0 }) 
    if 9998 not in KnownGameIDList:
        SQLCreateEntry('NonSteamApps',{'GameID': 9998, 'Title': 'Dolphin Wii Saves', 'RelativeSavePath': '{ HOME }.local/share/dolphin-emu/Wii/title/', 'MostRecentSaveTime': 0 }) 
    if 9997 not in KnownGameIDList:
        SQLCreateEntry('NonSteamApps',{'GameID': 9997, 'Title': 'Yuzu Saves', 'RelativeSavePath':'{ HOME }.local/share/yuzu/nand/user/save/0000000000000000/{ UID}/', 'MostRecentSaveTime': 0 })
    if 9996 not in KnownGameIDList:
        SQLCreateEntry('NonSteamApps',{'GameID': 9996, 'Title': 'Yuzu Keys', 'RelativeSavePath': '{ HOME }.local/share/yuzu/keys/', 'MostRecentSaveTime': 0 })
    if 9995 not in KnownGameIDList:
        SQLCreateEntry('NonSteamApps',{'GameID': 9995, 'Title': 'Yuzu Mods', 'RelativeSavePath': '{ HOME }/.local/share/yuzu/load', 'MostRecentSaveTime': 0})
    if 9994 not in KnownGameIDList:
        SQLCreateEntry('NonSteamApps',{'GameID': 9994, 'Title': 'Ryujinx Saves', 'RelativeSavePath': '{ HOME }.config/Ryujinx/bis/user/save/0000000000000001', 'MostRecentSaveTime': 0 })
    if 9993 not in KnownGameIDList:
        SQLCreateEntry('NonSteamApps',{'GameID': 9993, 'Title': 'Ryujinx Keys', 'RelativeSavePath': '{ HOME }.config/Ryujinx/system/', 'MostRecentSaveTime': 0 })
    if 9992 not in KnownGameIDList:
        SQLCreateEntry('NonSteamApps',{'GameID': 9992, 'Title': 'Ryujinx Firmware', 'RelativeSavePath': '{ HOME }.config/Ryujinx/bis/system/Contents/', 'MostRecentSaveTime': 0 })
    if 9991 not in KnownGameIDList:
        SQLCreateEntry('NonSteamApps',{'GameID': 9991, 'Title': 'Duckstation Memory Cards', 'RelativeSavePath': '{ HOME }.local/share/duckstation/memcards/', 'MostRecentSaveTime': 0 })
    if 9990 not in KnownGameIDList:
        SQLCreateEntry('NonSteamApps',{'GameID': 9990, 'Title': 'Duckstation BIOS', 'RelativeSavePath': '{ HOME }.local/share/duckstation/bios/', 'MostRecentSaveTime': 0 })
    if 9989 not in KnownGameIDList:
        SQLCreateEntry('NonSteamApps',{'GameID': 9989, 'Title': 'PCSX2 Memory Cards', 'RelativeSavePath': '{ HOME }.config/PCSX2/memcards/', 'MostRecentSaveTime': 0 })
    if 9988 not in KnownGameIDList:
        SQLCreateEntry('NonSteamApps',{'GameID': 9988, 'Title': 'PCSX2 BIOS', 'RelativeSavePath':'{ HOME }.config/PCSX2/bios/', 'MostRecentSaveTime': 0 })
    if 9987 not in KnownGameIDList:
        SQLCreateEntry('NonSteamApps',{'GameID': 9987, 'Title': 'RPCS3 Saves', 'RelativeSavePath':'{ HOME }/.config/rpcs3/dev_hdd0/home/00000001/savedata', 'MostRecentSaveTime': 0})
    if 9986 not in KnownGameIDList:
        SQLCreateEntry('NonSteamApps',{'GameID': 9986, 'Title': 'Citra Saves', 'RelativeSavePath':'{ HOME }.local/share/citra-emu/sdmc/Nintendo 3DS/00000000000000000000000000000000/00000000000000000000000000000000/title/', 'MostRecentSaveTime': 0 })
    if 9985 not in KnownGameIDList:
        SQLCreateEntry('NonSteamApps',{'GameID': 9985, 'Title': 'Mupen64Plus Saves', 'RelativeSavePath':'{ HOME }/.local/share/mupen64plus/save', 'MostRecentSaveTime': 0 })
    if 9984 not in KnownGameIDList:
        SQLCreateEntry('NonSteamApps',{'GameID': 9984, 'Title': 'zSNES saves', 'RelativeSavePath': '{ HOME }/.zsnes', 'MostRecentSaveTime': 0 })
    if 9983 not in KnownGameIDList:
        SQLCreateEntry('NonSteamApps',{'GameID': 9983, 'Title': 'Retroarch BIOS', 'RelativeSavePath': '{ HOME }/.config/retroarch/system/', 'MostRecentSaveTime': 0})
    if 9982 not in KnownGameIDList:
        SQLCreateEntry('NonSteamApps',{'GameID': 9982, 'Title': 'Retroarch saves', 'RelativeSavePath': '{ HOME }/.config/retroarch/saves/', 'MostRecentSaveTime': 0})
    if 9981 not in KnownGameIDList:
        SQLCreateEntry('NonSteamApps',{'GameID': 9981, 'Title': 'Xemu BIOS', 'RelativeSavePath': '{ HOME }/.local/share/xemu/bios/', 'MostRecentSaveTime': 0})
    if 9980 not in KnownGameIDList:
        SQLCreateEntry('NonSteamApps',{'GameID': 9980, 'Title': 'Xemu Saves', 'RelativeSavePath': '{ HOME }/.local/share/xemu/hdd_0/', 'MostRecentSaveTime': 0})
    if 9979 not in KnownGameIDList:
        SQLCreateEntry('NonSteamApps',{'GameID': 9979, 'Title': 'Cemu Saves', 'RelativeSavePath': '{ HOME }/.local/share/Cemu/mlc01/usr/save/00050000', 'MostRecentSaveTime': 0})
    if 9978 not in KnownGameIDList:
        SQLCreateEntry('NonSteamApps',{'GameID': 9978, 'Title': 'Cemu Mods', 'RelativeSavePath': '{ HOME }/.local/share/Cemu/graphicPacks/downloadedGraphicPacks', 'MostRecentSaveTime': 0})
    if 9977 not in KnownGameIDList:
        SQLCreateEntry('NonSteamApps',{'GameID': 9977, 'Title': 'Primehack Flatpak Saves', 'RelativeSavePath': '{ HOME }/.var/app/io.github.shiiion.primehack/data/dolphin-emu/Wii/title/00010000', 'MostRecentSaveTime': 0})
    if 9976 not in KnownGameIDList:
        SQLCreateEntry('NonSteamApps',{'GameID': 9976, 'Title': 'shadPS4 Saves', 'RelativeSavePath': '{ HOME }/.local/share/shadPS4/savedata', 'MostRecentSaveTime': 0})
    print("List finished generating!")
    return 0

def GenerateSecondaryPaths():
    print('Generating secondary paths values...')
    ExistingSecondaryPaths = SQLGetEntry('SecondaryPaths',{})
    KnownGameIDList = []
    for val in ExistingSecondaryPaths:
        if val['GameID'] not in KnownGameIDList:
            KnownGameIDList.append(val['GameID'])
    if 9978 not in KnownGameIDList:
        SQLCreateEntry('SecondaryPaths',{ 'GameID': 9978, 'SecondaryPath': '{ HOME }/.var/app/info.cemu.Cemu/data/Cemu/graphicPacks/downloadedGraphicPacks', 'Description': 'Flatpak'})
    if 9979 not in KnownGameIDList:
        SQLCreateEntry('SecondaryPaths',{ 'GameID': 9979, 'SecondaryPath': '{ HOME }/.var/app/info.cemu.Cemu/data/Cemu/mlc01/usr/save/00050000', 'Description': 'Flatpak'})
    if 9983 not in KnownGameIDList:
        SQLCreateEntry('SecondaryPaths',{ 'GameID': 9983, 'SecondaryPath':'{ HOME }/.var/app/org.libretro.RetroArch/config/retroarch/saves/', 'Description':'Flatpak'})
    if 9984 not in KnownGameIDList:
        SQLCreateEntry('SecondaryPaths',{ 'GameID': 9984, 'SecondaryPath':'{ HOME }/.var/app/org.libretro.RetroArch/config/retroarch/system/', 'Description':'Flatpak'})
    if 9985 not in KnownGameIDList:
        SQLCreateEntry('SecondaryPaths',{ 'GameID': 9985, 'SecondaryPath':'{ HOME }/.var/app/io.github.xyproto.zsnes/config/zsnes', 'Description':'Flatpak'})
    if 9986 not in KnownGameIDList:
        SQLCreateEntry('SecondaryPaths',{ 'GameID': 9986, 'SecondaryPath':'{ HOME }/.var/app/com.github.Rosalie241.RMG/data/RMG/Save/Game/', 'Description':'Flatpak - Mupen64Plus with a GUI'})
    if 9987 not in KnownGameIDList:
        SQLCreateEntry('SecondaryPaths',{ 'GameID': 9987, 'SecondaryPath':'{ HOME }/.var/app/org.citra_emu.citra/data/citra-emu/sdmc/Nintendo 3DS/00000000000000000000000000000000/00000000000000000000000000000000/title/', 'Description':'Flatpak'})
    if 9988 not in KnownGameIDList:
        SQLCreateEntry('SecondaryPaths',{ 'GameID': 9988, 'SecondaryPath':'{ HOME }/.var/app/net.rpcs3.RPCS3/config/rpcs3/dev_hdd0/home/00000001/savedata', 'Description':'Flatpak'})
    if 9989 not in KnownGameIDList:
        SQLCreateEntry('SecondaryPaths',{ 'GameID': 9989, 'SecondaryPath': '{ HOME }/.var/app/net.pcsx2.PCSX2/config/PCSX2/bios/', 'Description': 'Flatpak'})
    if 9990 not in KnownGameIDList:
        SQLCreateEntry('SecondaryPaths',{ 'GameID': 9990, 'SecondaryPath': '{ HOME }/.var/app/net.pcsx2.PCSX2/config/PCSX2/memcards/', 'Description': 'Flatpak'})
    if 9991 not in KnownGameIDList:
        SQLCreateEntry('SecondaryPaths',{ 'GameID': 9991, 'SecondaryPath': '{ HOME }/.var/app/org.duckstation.DuckStation/config/duckstation/bios/', 'Description': 'Flatpak'})
    if 9992 not in KnownGameIDList:
        SQLCreateEntry('SecondaryPaths',{ 'GameID': 9992, 'SecondaryPath': '{ HOME }/.var/app/org.duckstation.DuckStation/config/duckstation/memcards/', 'Description': 'Flatpak'})
    if 9993 not in KnownGameIDList:
        SQLCreateEntry('SecondaryPaths',{ 'GameID': 9993, 'SecondaryPath': '{ HOME }/.var/app/org.ryujinx.Ryujinx/config/Ryujinx/bis/system/Contents/', 'Description': 'Flatpak'})
    if 9994 not in KnownGameIDList:
        SQLCreateEntry('SecondaryPaths',{ 'GameID': 9994, 'SecondaryPath': '{ HOME }/.var/app/org.ryujinx.Ryujinx/config/Ryujinx/system/', 'Description': 'Flatpak'})
    if 9995 not in KnownGameIDList:
        SQLCreateEntry('SecondaryPaths',{ 'GameID': 9995, 'SecondaryPath': '{ HOME }/.var/app/org.ryujinx.Ryujinx/config/Ryujinx/bis/user/save/0000000000000001/', 'Description': 'Flatpak'})
    if 9996 not in KnownGameIDList:
        SQLCreateEntry('SecondaryPaths',{ 'GameID': 9996, 'SecondaryPath': '{ HOME }/.var/app/org.yuzu_emu.yuzu/data/yuzu/keys/', 'Description': 'Flatpak' })
    if 9997 not in KnownGameIDList:
        SQLCreateEntry('SecondaryPaths',{ 'GameID': 9997, 'SecondaryPath': '{ HOME }/.var/app/org.yuzu_emu.yuzu/data/yuzu/nand/user/save/0000000000000000/{ UID }/', 'Description': 'Flatpak' })
    if 9998 not in KnownGameIDList:
        SQLCreateEntry('SecondaryPaths',{ 'GameID': 9998, 'SecondaryPath': '{ HOME }/.var/app/org.DolphinEmu.dolphin-emu/data/dolphin-emu/Wii/title/', 'Description': 'Flatpak' })
    if 9999 not in KnownGameIDList:
        SQLCreateEntry('SecondaryPaths',{ 'GameID': 9999, 'SecondaryPath': '{ HOME }/.var/app/org.DolphinEmu.dolphin-emu/data/dolphin-emu/GC/', 'Description': 'Flatpak' })
    print('Finished generating secondary paths!')


def GenerateGlobalVars():
    response = input("Please specify the maximum number of saves you wish to keep backed up (default: 10): ")
    MaxSaves = 0
    IncludeSteamCloud = False
    if response == '':
        MaxSaves = 10
    else:
        MaxSaves = int(response)
    response = input("Do you wish to include Steam Cloud saves in your save game syncs? [y/N]: ")
    if response.lower() not in ['y','yes']:
        IncludeSteamCloud = False
    else:
        IncludeSteamCloud = True
    ExistingSteamCloudEntry = SQLGetEntry('GlobalVars',{'Key':'IncludeSteamCloud'},[])
    ExistingMaxSavesEntry = SQLGetEntry('GlobalVars',{'Key':'MaxSaves'},[])
    if len(ExistingSteamCloudEntry) != 0:
        SQLUpdateEntry('GlobalVars',{'Value':str(IncludeSteamCloud)},{'Key':'IncludeSteamCloud'})
    else:
        SQLCreateEntry('GlobalVars',{'Key':'IncludeSteamCloud','Value':str(IncludeSteamCloud)})
    if len(ExistingMaxSavesEntry) != 0:
        SQLUpdateEntry('GlobalVars',{'Value':str(MaxSaves)})
    else:
        SQLCreateEntry('GlobalVars',{'Key':'MaxSaves','Value':str(MaxSaves)})
    return 0

def InitializeDatabase():
    LibraryConnection = sqlite3.connect('saves.db')
    if LibraryConnection:
        Cursor = LibraryConnection.cursor()
        Tables = Cursor.execute("""SELECT name FROM sqlite_master WHERE type='table'""").fetchall()
        if len(Tables) != 0:
            print("Tables Already Present in Database")
            print("Checking for missing tables...")
        else:
            print("No tables in database")
            print("Creating database tables...")
        if ('ClientSaveInfo',) not in Tables:
            print("Creating ClientSaveInfo table...")
            LibraryConnection.execute("""CREATE TABLE ClientSaveInfo (
            AppID INT NOT NULL,
            Skipped INT,
            ClientID INT NOT NULL,
            InstallPath TEXT,
            MostRecentSaveTime REAL,
            ProtonPrefix TEXT);""")
            print("ClientSaveInfo table successfully created!")
        if ('ClientPrefixes',) not in Tables:
            print("Creating ClientPrefixes Table...")
            LibraryConnection.execute("""CREATE TABLE ClientPrefixes (
            AppID INT NOT NULL,
            ClientID INT NOT NULL,
            Prefix TEXT);""")
            print("ClientPrefixes table successfully created!")
        if ('ClientSuffixes',) not in Tables:
            print("Creating ClientSuffixes table...")
            LibraryConnection.execute("""CREATE TABLE ClientSuffixes (
            AppID INT NOT NULL,
            ClientID INT NOT NULL,
            Suffix TEXT);""")
            print("ClientSuffixes table successfully created!")
        if ('SteamApps',) not in Tables:
            print("Creating SteamApps table...")
            LibraryConnection.execute("""CREATE TABLE SteamApps (
            AppID INT PRIMARY KEY NOT NULL,
            AlwaysSkipped INT,
            SteamCloud INT,
            Title TEXT,
            MostRecentSaveTime REAL);""")
            print("SteamApps table successfully created!")
        if ('SaveTimestamps',) not in Tables:
            print("Creating SaveTimestamps table...")
            LibraryConnection.execute(""" CREATE TABLE SaveTimestamps (
            AppID INT  NOT NULL,
            Timestamp REAL);""")
            print("SaveTimestamps table successfully created!")
        if ('SavePathFixes',) not in Tables:
            print("Creating SavePathFixes table...")
            LibraryConnection.execute("""CREATE TABLE SavePathFixes (
            AppID INT NOT NULL,
            IncorrectString TEXT,
            FixedString TEXT);""")
            print("SavePathFixes table successfully created!")
        if ('SecondaryPaths',) not in Tables:
            print("Creating SecondaryPaths table...")
            LibraryConnection.execute(""" CREATE TABLE SecondaryPaths (
            GameID INT NOT NULL,
            SecondaryPath TEXT,
            Description TEXT);""")
            print("SecondaryPaths table sucessfully created!")
        if ('FileExclusions',) not in Tables:
            print("Creating FileExclusions table...")
            LibraryConnection.execute("""CREATE TABLE FileExclusions (
            AppID INT NOT NULL,
            Filename TEXT );""")
            print("FileExclusions table successfully created!")
        if ('RelativeSavePaths',) not in Tables:
            print("Creating RelativeSavePaths table...")
            LibraryConnection.execute("""CREATE TABLE RelativeSavePaths (
            AppID INT NOT NULL,
            RelativePath TEXT );""")
            print("RelativeSavePaths Table successfully created!")
        if ('Clients',) not in Tables:
            print("Creating Clients table...")
            LibraryConnection.execute(""" CREATE TABLE Clients (
            ClientID INT PRIMARY KEY NOT NULL,
            LastSyncTime REAL,
            SteamPath TEXT,
            HomeDir TEXT,
            ClientName TEXT)""")
            print("Clients table successfully created!")
        if ('ROMSaves',) not in Tables:
            print("Creating ROMSaves table...")
            LibraryConnection.execute("""CREATE TABLE ROMSaves (
            FileName TEXT NOT NULL,
            SubFolder TEXT,
            Timestamp REAL);""")
            print("ROMSaves table successfully created!")
        if ('RomSaveTimestamps',) not in Tables:
            print("Creating ROMSaves table...")
            LibraryConnection.execute("""CREATE TABLE RomSaveTimestamps (
            FileName TEXT NOT NULL,
            Timestamp REAL);""")
            print("RomSaveTimestamps table successfully created!")
        if ('NonSteamApps',) not in Tables:
            print("Creating NonSteamApps table...")
            LibraryConnection.execute(""" CREATE TABLE NonSteamApps (
            GameID INT NOT NULL,
            Title TEXT,
            RelativeSavePath TEXT,
            MostRecentSaveTime REAL);""")
            print("NonSteamApps table successfully created!")
        if ('NonSteamClientSaves',) not in Tables:
            print("Creating NonSteamClientSaves table...")
            LibraryConnection.execute("""CREATE TABLE NonSteamClientSaves (
            GameID INT NOT NULL,
            ClientID INT NOT NULL,
            MostRecentSaveTime REAL,
            LocalSavePath TEXT);""")
            print("NonSteamClientSaves table successfully created!")
        if ('NonSteamSaveTimestamps',) not in Tables:
            print("Creating NonSteamSaveTimestamps Table...")
            LibraryConnection.execute("""CREATE TABLE NonSteamSaveTimestamps (
            GameID INT NOT NULL,
            Timestamp REAL);""")
            print("NonSteamSaveTimestamps table successfully created!")
        if ('GlobalVars',) not in Tables:
            print("Creating GlobalVars table...")
            LibraryConnection.execute("""CREATE TABLE GlobalVars (
            Key Text,
            Value TEXT);""")
            print("GlobalVars table successfully created!")
        Tables = Cursor.execute("""SELECT name FROM sqlite_master WHERE type='table'""").fetchall()
        if len(Tables) == 16:
            print("All tables needed present in database.")
            print('Database successfully initialized!')
        else:
            print("Still missing tables! Consider deleting your saves.db file and rerunning SaveSync.py")
        GlobalVarCheck = SQLGetEntry('GlobalVars', {})
        if len(GlobalVarCheck) == 0:
            GenerateGlobalVars()
        GenerateFileExclusions()
        GenerateSkippedGames()
        GenerateAutoDetectedNonSteamGames()
        GenerateSecondaryPaths()
        LibraryConnection.commit()
        LibraryConnection.close()
