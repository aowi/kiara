Kiara
=====

Kiara will hash your anime and add the episode to your anidb mylist.
It will also mark those files watched, and organize them nicely in folders.

Requirements
------------
Python 3.2 (or newer)

Installation
------------
1. `sudo python3 setup.py install`
2. See /etc/kiararc for further instructions

Usage
-----
From `kiara -h`:

	usage: kiara [-h] [-w] [-o] [-c CONFIG] [--find-duplicates]
				 [--forget [FID [FID ...]]]
				 [FILE [FILE ...]]
	
	Do stuff with anime files and anidb.
	
	positional arguments:
	  FILE                  a file to do something with
	
	optional arguments:
	  -h, --help            show this help message and exit
	  -w, --watch           Mark all the files watched.
	  -o, --organize        Organize ALL THE FILES _o/
	  -c CONFIG, --config CONFIG
							Alternative config file to use.
	  --find-duplicates     Lists all episode for which you have more than one
							file
	  --forget [FID [FID ...]]
							Delete all info from the database (but not the file
							itself) about the files with the giver anidb file-id.
							(These are the numbers output by --find-duplicates
