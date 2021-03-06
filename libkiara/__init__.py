#!/usr/bin/env python3

import os, os.path
import sys
import socket
import time

# Used to gracefully aborting stuff.. like a hippo exiting a stage
class AbandonShip(BaseException):
	pass

# Default config values.
_config = {
	'host': 'api.anidb.net',
	'port': '9000',
	'session': '~/.kiara.session',
	'database': '~/.kiara.db',
}

def _config_items(file):
	for line in map(lambda s: s.strip(), file.readlines()):
		if line.startswith('#') or not line:
			continue
		yield line.split(None, 1)

def load_config_file(file_name):
	global _config
	try:
		with open(file_name, 'r') as fp:
			_config.update(_config_items(fp))
	except: pass
load_config_file('/etc/kiararc')
load_config_file(os.path.expanduser('~/.kiararc'))

def check_config():
	config_ok = True
	for key in 'host port user pass database session ' \
		'basepath_movie basepath_series'.split():
		if not key in _config:
			print('ERROR: Missing config variable:', key, file=sys.stderr)
			config_ok = False
	return config_ok

def _send(msg):
	print()
	def inner():
		client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		client.connect(os.path.expanduser(_config['session']))
		client.sendall(bytes(msg, 'UTF-8'))
		data = ''
		while True:
			data += str(client.recv(1024), 'UTF-8')
			if data == '---end---':
				client.close()
				return
			if '\n' in data:
				item, data = data.split('\n', 1)
				yield item
	try:
		for i in inner():
			yield i
	except socket.error:
		print('Unable to contact the backend. Will try to start one...')
		if os.fork():
			# Wait for it...
			time.sleep(2)
			# Then try the command again. If it fails again, something we
			# cannot fix is wrong
			for i in inner():
				yield i
			return
			print('Unable to start a new backend, sorry :(')
		else:
			from libkiara import backend
			backend.serve(_config)

def ping():
	wah = False
	for l in _send('- ping'):
		print(l)
		wah = l == 'pong'
	return wah

def process(file, watch=False, organize=False):
	q = 'a'
	if watch:
		q += 'w'
	if organize:
		q += 'o'
	
	for line in _send(q + ' ' + file):
		print(line)

def find_duplicates():
	for line in _send('- dups'):
		print(line)

def forget(*fids):
	for line in _send('- forget ' + ' '.join(list(map(str, fids)))):
		print(line)
