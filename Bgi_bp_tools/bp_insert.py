#! /usr/bin/env python3

# BGI .bp script inserter

import glob
import os
import re
import struct
import sys

import bp_common
import bp_setup

re_line = re.compile(r'<(\w\w)(\d+?)>(.*)')

def get_text(fi, ilang):
	texts = {}
	for line in fi:
		line = line.rstrip('\n')
		if re_line.match(line):
			lang, id, text = re_line.match(line).groups()
			id = int(id)
			if lang == ilang:
				texts[id] = bp_common.unescape(text)
	return texts
	
def insert_unique(code_bytes, code_section, texts, text_bytes):
	text_dict = {}
	code_size = len(code_bytes)
	offset = len(text_bytes)
	for addr in  sorted(code_section):
		text, id = code_section[addr]
		if text in text_dict:
			id, doffset = text_dict[text]
			code_bytes[addr+1:addr+3] = struct.pack('<H', doffset+code_size-addr)
		else:
			ntext = texts[id]
			nbytes = ntext.encode(bp_setup.ienc) + b'\x00'
			text_bytes += nbytes
			text_dict[text] = id, offset
			code_bytes[addr+1:addr+3] = struct.pack('<H', offset+code_size-addr)
			offset += len(nbytes)
	return text_bytes
	
def insert_sequential(code_bytes, code_section, texts, text_bytes):
	code_size = len(code_bytes)
	offset = len(text_bytes)
	for addr in sorted(code_section):
		text, id = code_section[addr]
		ntext = texts[id]
		nbytes = ntext.encode(bp_setup.ienc) + b'\x00'
		text_bytes += nbytes
		code_bytes[addr+1:addr+3] = struct.pack('<H', offset+code_size-addr)
		offset += len(nbytes)
	return text_bytes
	
def insert_script(odir, script, ilang):
	data = open(script, 'rb').read()
	hdr_bytes, code_bytes, text_bytes = bp_common.split_data(data)
	text_section = bp_common.get_text_section(text_bytes)
	code_section = bp_common.get_code_section(code_bytes, text_section)
	scriptname = os.path.splitext(script)[0]
	texts = get_text(open(scriptname+bp_setup.dext, 'r', encoding=bp_setup.denc), ilang)
	code_bytes = bytearray(code_bytes)
	text_bytes = b''
	text_bytes = insert_unique(code_bytes, code_section, texts, text_bytes)
	fo = open(os.path.join(odir,os.path.split(script)[1]), 'wb')
	fo.write(hdr_bytes)
	fo.write(code_bytes)
	fo.write(text_bytes)
	fo.close()
	
if __name__ == '__main__':
	if len(sys.argv) < 3:
		print('Usage: bp_insert.py <out_dir> <file(s)>')
		print("(<out_dir> will be created if it doesn't exist)")
		print('(only files with extension ._bp among <file(s)> will be processed)')
		sys.exit(1)
	out_dir = sys.argv[1]
	if not os.access(out_dir, os.F_OK):
		os.mkdir(out_dir)
	for arg in sys.argv[2:]:
		for script in glob.glob(arg):
			base, ext = os.path.splitext(script)
			if ext == '._bp':
				print('Inserting %s...' % script)
				insert_script(out_dir, script, bp_setup.ilang)
