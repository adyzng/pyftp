# pyftp
High level ftp client wrapper based on python ftplib.

Based on Python 2.7.

# class
```Python
class StatResult(tuple)
	"""
	Support class resembling a tuple like that returned from `os.stat`
	Additional property :
	st_name : file & folder name
	st_path : full path on the ftp server
	"""

class PyFTP(object)
	"""
   	high-level FTP client library wrapper
	"""
```

# docs
PyFTP methods defined here:
- **cd(self, pathname)**

	ftp server change folder with statement

- **chdir(self, pathname)**

	change current folder

- **chmode(self, pathname, mode='0755')**

	change file/path mode

- **close(self)**

	close connection
	
- **connect(self)**

	connect to ftp server using give credential

- **exists(self, pathname)**

	check if file or folder exist

- **get_mtime(self, remotepath)**

	get file modified date time

- **set_mtime(self, remotepath, time_seconds, ignore_error=False)**

	set file modified date time on ftp server

- **getcwd(self)**

	return current ftp server side directory

- **isdir(self, pathname)**

	check is directory or not

- **isfile(self, pathname)**

	check is file or not

- **listdir(self, pathname=None)**

	get files/dirs under pathname, return a list of `StatResult`

- **get(self, remotepath, localpath=None, preserve_mtime=False)**

	copies a file between the remote host and the local host.

- **get_d(self, remotedir, localdir, preserve_mtime=False)**

	get the contents of remotedir and write to locadir. (non-recursive)

- **get_r(self, remotedir, localdir, preserve_mtime=False)**

	recursively copy remotedir structure to localdir

- **put(self, localpath, remotepath=None, preserve_mtime=False)**

	copies a file between the local host and the remote host.

- **put_d(self, localpath, remotepath, preserve_mtime=False)**

	copies a local directory's contents to a remotepath

- **put_r(self, localpath, remotepath, preserve_mtime=False)**

	Recursively copies a local directory's contents to a remotepath

- **remove(self, pathname)**

	remove file (remove directory using `rmdir` instead)

- **rmdir(self, pathname, force=False)**

	remove an directory

- **size(self, filename)**

	retrieve file size

- **stat(self, pathname)**

	Retrieve limit file stat from ftp server.
	**IMPORTANT**: folder not supported
