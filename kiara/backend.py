import os.path
import sys
import shutil
import argparse
from datetime import datetime, timedelta
import socketserver

import ed2khash
import database
import anidb

config = {}

# Define a dump object to pass around.
class KiaraFile(object):
	def __init__(self, name):
		self.file = open(name, 'rb')
		self.file_name = name
		self.name = os.path.basename(name)
		self.size = os.path.getsize(name)
		
		self.dirty = False # Should this be saved.
		self.updated = None
		self.in_anidb = True
		
		self.hash = None
		self.watched = False
		self.fid = None
		self.mylist_id = None
		self.aid = None
		self.crc32 = None
		
		self.anime_total_eps = None
		self.anime_name = None
		self.anime_type = None
		self.ep_no = None
		self.group_name = None
		
		self.added = False
	
	def misses_info(self):
		return (
			self.fid == None or
			self.mylist_id == None or
			self.aid == None or
			self.crc32 == None or
			self.anime_total_eps == None or
			self.anime_name == None or
			self.anime_type == None or
			self.ep_no == None or
			self.group_name == None)
	
	def is_movie(self):
		return (
			self.anime_type == 'Movie' or
			self.anime_type == 'OVA' and self.anime_total_eps == 1 or
			self.anime_type == 'Web' and self.anime_total_eps == 1)
	
	def __str__(self):
		parts = [self.name]
		if self.hash:
			parts.append(self.hash)
		if self.dirty:
			parts.append('(unsaved)')
		return ' '.join(parts)

def rmdirp(path):
	while path:
		if os.listdir(path) == []:
			yield 'The dir ' + path + ' is now empty, will remove it'
			os.rmdir(path)
			path = os.path.dirname(path)
		else:
			return
	
def pad(length, num):
	try:
		int(num)
		return "0" * max(0, (length - len(num))) + num
	except ValueError:
		return num

class Handler(socketserver.BaseRequestHandler):
	def __init__(self, *args, **kwargs):
		self.queued_messages = []
		return super().__init__(*args, **kwargs)
	
	def reply(self, message, catch_fails=True):
		self.write(message + '\n', catch_fails)
	
	def write(self, message, catch_fails=True):
		try:
			self.request.send(bytes(message, 'UTF-8'))
		except socket.error:
			if catch_fails:
				self.queued_messages.append(message)
	
	def exit(self, status):
		self.request.sendall(bytes('---end---', 'UTF-8'))
		sys.exit(status)
	
	def handle(self):
		while self.queued_messages:
			self.reply(self.queued_messages.pop(0), False)
		data = self.request.recv(1024).strip().decode('UTF-8')
		
		act, file_name = data.split(' ', 1)
		if act == '-':
			# Non-file related commands
			if file_name == 'ping':
				if anidb.ping(self):
					self.reply('pong')
				else:
					self.reply('No answer :(')
					self.exit(1)
			if file_name == 'quit':
				self.reply('shutting down the backend')
				self.exit(0)
		
		else:
			try:
				# File related commands
				file = KiaraFile(file_name)
				
				# Load file info.
				database.load(file)
				if not file.hash:
					self.reply('Hashing ' + file.name)
					file.hash = ed2khash.hash(file.file)
					database.load(file)
				
				if file.misses_info() or \
						file.updated < datetime.now() - timedelta(days=7):
					anidb.load_info(file, self)
				
				if not file.fid:
					self.reply('!!! File is unknown to anidb. '
						'Will not process further')
				else:
					if (not file.added) and 'a' in act:
						anidb.add(file, self)
					
					if not file.watched and 'w' in act:
						anidb.watch(file, self)
					
					if 'o' in act:
						anime_name = file.anime_name.replace('/', '_')
						dir = os.path.join(os.path.expanduser((
							config['basepath_movie']
							if file.is_movie()
							else config['basepath_series'])), anime_name)
						if 'debug' in config:
							self.reply('Type is ' + file.anime_type +
								', so I\'ll put this in ' + dir)
						
						os.makedirs(os.path.normpath(dir), exist_ok=True)
						new_name = None
						if file.anime_total_eps == "1":
							new_name = "[%s] %s [%s]%s" % (
								file.group_name, anime_name, file.crc32,
								os.path.splitext(file_name)[1])
						else:
							new_name = "[%s] %s - %s [%s]%s" % (
								file.group_name, anime_name,
								pad(
									len(str(file.anime_total_eps)),
									str(file.ep_no)),
								file.crc32, os.path.splitext(file_name)[1])
						new_path = os.path.join(dir, new_name)
						
						if file_name == new_path:
							self.reply(new_name + ' is already organized')
						else:
							if os.path.isfile(new_path):
								self.reply('!!! ' + new_path +
									' already existst, not overwriting')
							else:
								shutil.move(file_name, new_path)
								self.reply('Moved ' + file_name +
									' to ' + new_path)
								file.name = new_name
								file.dirty = True
						
							for r in rmdirp(os.path.dirname(file_name)):
								self.reply(r)
						
					database.save(file)
			except SystemExit as e:
				self.reply('wawa')
				self.exit(e.code)
			
		self.request.sendall(bytes('---end---', 'UTF-8'))

def serve(cfg):
	global config
	config = cfg
	anidb.config = config
	database.connect(os.path.expanduser(config['database']), config['user'])
	
	try:
		os.remove(os.path.expanduser(config['session']))
	except: pass
	socketserver.UnixStreamServer(
		os.path.expanduser(config['session']), Handler).serve_forever()