# -*- coding: utf-8 -*-

import os
import logging

stdCompressions = ("gz", "bz2", "lzma")

log = logging.getLogger("pyglossary")


def compressionOpenFunc(c: str):
	if not c:
		return open
	if c == "gz":
		import gzip
		return gzip.open
	if c == "bz2":
		import bz2
		return bz2.open
	if c == "lzma":
		import lzma
		return lzma.open
	if c == "dz":
		import gzip
		return gzip.open
	return None


def compressionOpen(filename, dz=False, **kwargs):
	from os.path import splitext
	filenameNoExt, ext = splitext(filename)
	ext = ext.lower().lstrip(".")
	try:
		int(ext)
	except ValueError:
		pass
	else:
		_, ext = splitext(filenameNoExt)
		ext = ext.lower().lstrip(".")
	if ext in stdCompressions or (dz and ext == "dz"):
		_file = compressionOpenFunc(ext)(filename, **kwargs)
		_file.compression = ext
		return _file
	return open(filename, **kwargs)


def zipFileOrDir(glos: "GlossaryType", filename: str) -> "Optional[str]":
	import zipfile
	import shutil
	from os.path import (
		isfile,
		isdir,
		split,
	)
	from .os_utils import indir

	def _zipFileAdd(zf, filename):
		if isfile(filename):
			zf.write(filename)
			return
		if not isdir(filename):
			raise OSError(f"Not a file or directory: {filename}")
		for subFname in os.listdir(filename):
			_zipFileAdd(zf, join(filename, subFname))

	zf = zipfile.ZipFile(f"{filename}.zip", mode="w")

	if isdir(filename):
		dirn, name = split(filename)
		with indir(filename):
			for subFname in os.listdir(filename):
				_zipFileAdd(zf, subFname)

		shutil.rmtree(filename)
		return

	dirn, name = split(filename)
	files = [name]

	if isdir(f"{filename}_res"):
		files.append(f"{name}_res")

	with indir(dirn):
		for fname in files:
			_zipFileAdd(zf, fname)


def compress(glos: "GlossaryType", filename: str, compression: str) -> str:
	"""
	filename is the existing file path
	supported compressions: "gz", "bz2", "lzma", "zip"
	"""
	import shutil
	from os.path import isfile

	log.info(f"Compressing {filename!r} with {compression!r}")

	compFilename = f"{filename}.{compression}"
	if compression in stdCompressions:
		with compressionOpenFunc(compression)(compFilename, mode="wb") as dest:
			with open(filename, mode="rb") as source:
				shutil.copyfileobj(source, dest)
		return compFilename

	if compression == "zip":
		try:
			os.remove(compFilename)
		except OSError:
			pass
		try:
			error = zipFileOrDir(glos, filename)
		except Exception as e:
			log.error(
				f"{e}\nFailed to compress file \"{filename}\""
			)
	else:
		raise ValueError(f"unexpected {compression=}")

	if isfile(compFilename):
		return compFilename
	else:
		return filename


def uncompress(srcFilename: str, dstFilename: str, compression: str) -> None:
	"""
	filename is the existing file path
	supported compressions: "gz", "bz2", "lzma"
	"""
	import shutil
	log.info(f"Uncompressing {srcFilename!r} to {dstFilename!r}")

	if compression in stdCompressions:
		with compressionOpenFunc(compression)(srcFilename, mode="rb") as source:
			with open(dstFilename, mode="wb") as dest:
				shutil.copyfileobj(source, dest)
		return

	# TODO: if compression == "zip":
	raise ValueError(f"unexpected {compression=}")
