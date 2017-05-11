# coding: utf-8

"""
pyftp - high-level FTP client library

"""

__version__ = "0.1.1"
__all__ = ['StatResult', 'PyFTP']

import os
import stat

import ftplib
from ftplib import FTP, error_perm, error_temp

import time
from contextlib import contextmanager


def ftp_host(address, port=None):
    '''extract protocol/host/port from input host string'''
    PORT_MAP = {'ftp': 21, 'sftp': 22}
    _port, _prot, _addr = port, 'ftp', address

    npos = address.find('://')
    if npos != -1:
        _prot = address[:npos].lower()
        _addr = address[npos + 3:]
        _port = PORT_MAP.get(_prot.lower(), 21) if not port else port
    return _addr, _port, _prot



class StatResult(tuple):
    """
    Support class resembling a tuple like that returned from `os.stat`.
    """

    _index_mapping = {
      "st_mode":  0, "st_ino":   1, "st_dev":   2, "st_nlink":  3,
      "st_uid":   4, "st_gid":   5, "st_size":  6,
      "st_atime": 7, "st_mtime": 8, "st_ctime": 9 }

    def __init__(self, sequence):
        # Don't call `__init__` via `super`. Construction from a
        # sequence is implicitly handled by `tuple.__new__`, not
        # `tuple.__init__`. As a by-product, this avoids a
        # `DeprecationWarning` in Python 2.6+ .
        #
        # Use `sequence` parameter to remain compatible to `__new__`
        # interface.
        #
        self.st_name = ""
        self.st_path = ""


    def __getattr__(self, attr_name):
        if attr_name in self._index_mapping:
            return self[self._index_mapping[attr_name]]
        else:
            raise AttributeError("'StatResult' object has no attribute '{0}'".format(attr_name))


    def __repr__(self):
        # "Invert" `_index_mapping` so that we can look up the names
        # for the tuple indices.
        index_to_name = dict((v, k) for k, v in self._index_mapping.items())
        argument_strings = []
        for index, item in enumerate(self):
            argument_strings.append("{0}={1!r}".format(index_to_name[index], item))

        return "{0}({1})".format(type(self).__name__, ", ".join(argument_strings))
    

    @staticmethod
    def parse_mode(mode_string):
        """
        Return an integer from the `mode_string`, compatible with
        the `st_mode` value in stat results. Such a mode string
        may look like "drwxr-xr-x".

        If the mode string can't be parsed, raise an `ValueError`.
        """
        if len(mode_string) != 10:
            raise ValueError("invalid mode string '{0}'".format(mode_string))
        
        st_mode = 0
        #TODO Add support for "S" and sticky bit ("t", "T").
        for bit in mode_string[1:10]:
            bit = (bit != "-")
            st_mode = (st_mode << 1) + bit
        if mode_string[3] == "s":
            st_mode = st_mode | stat.S_ISUID
        if mode_string[6] == "s":
            st_mode = st_mode | stat.S_ISGID
        file_type_to_mode = {"b": stat.S_IFBLK, "c": stat.S_IFCHR,
                             "d": stat.S_IFDIR, "l": stat.S_IFLNK,
                             "p": stat.S_IFIFO, "s": stat.S_IFSOCK,
                             "-": stat.S_IFREG, "?": 0,
                             }
        file_type = mode_string[0]
        if file_type in file_type_to_mode:
            st_mode = st_mode | file_type_to_mode[file_type]
        else:
            raise ValueError("unknown file type character '{0}'".format(file_type))
        return st_mode



class PyFTP(object):
    # using new type class
    #__metaclass__ = type
    '''high-level FTP client library wrapper'''

    def __init__(self, host, username='', password='', port=None):
        self.host, self.port, self.type = ftp_host(host, port)
        self.user, self.pswd = username, password
        self.ftp = FTP(self.host)
        self._conn = False

    def connect(self):
        '''connect to ftp server using give credential'''
        self.ftp.login(self.user, self.pswd)
        self._conn = True


    def close(self):
        '''close connection'''
        if self._conn:
            self.ftp.quit()
            self.ftp = None
            self._conn = False

    '''
    Context manager methods
    '''
    def __enter__(self):
        # Return `self`, so it can be accessed as the variable
        # component of the `with` statement.
        if self.ftp is None:
            self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # We don't need the `exc_*` arguments here.
        # pylint: disable=unused-argument
        self.close()
        return False


    @contextmanager
    def cd(self, pathname=None):
        '''ftp server change folder with statement'''
        ori_path = self.ftp.pwd()
        try:
            if pathname is not None:
                self.ftp.cwd(pathname)
            yield
        finally:
            self.ftp.cwd(ori_path)

    @contextmanager
    def lcd(self, pathname):
        '''local path change folder with statement'''
        ori_path = os.getcwd()
        try:
            if pathname is not None:
                os.chdir(pathname)
            yield
        finally:
            os.chdir(ori_path)


    def getcwd(self):
        '''return current ftp server side directory'''
        return self.ftp.pwd()

    def chdir(self, pathname):
        '''change current folder'''
        try:
            self.ftp.cwd(pathname)
        except error_perm as e:
            raise IOError('%s not exist' % pathname)

    def chmode(self, pathname, mode='0755'):
        '''change file/path mode'''
        try:
            resp = self.ftp.sendcmd('SITE CHMOD %s %s' % (mode, pathname))
            return resp[0] == 2
        except error_perm as e:
            raise NotImplementedError('chmode is not supported.')
    
    def size(self, filename):
        ''''retrieve file size'''
        try:
            # 550 SIZE not allowed in ASCII mode
            self.ftp.voidcmd('TYPE I')
            return self.ftp.size(filename)
        except Exception as e:
            raise Exception(e.message)


    def exists(self, pathname):
        '''check if file or folder exist'''
        return self.isfile(pathname) or self.isdir(pathname)

    def isfile(self, pathname):
        '''check is file or not'''
        try:
            with self.cd(pathname):
                return False
        except error_perm as e:
            if self.get_mtime(pathname):
                return True
            else:
                return False

    def isdir(self, pathname):
        '''check is directory or not'''
        try:
            with self.cd(pathname):
                return True
        except error_perm as e:
            return False
    
    def get_mtime(self, remotepath):
        try:
            resp = self.ftp.sendcmd('MDTM %s' % remotepath)
            return self._mt_sec(resp.split()[1])
        except:
            return None

    def set_mtime(self, remotepath, time_seconds, ignore_error=False):
        '''set the modified time of file on ftp server
        
        :param str remotepath: 
            the remote path and filename, source
        :param int | long time_seconds:
            the time in seconds
        :raise IOError
            if failed to set modified time
        '''
        try:
            # try MFMT first
            mstr = self._sec_mt(time_seconds)
            self.ftp.sendcmd('MFMT %s %s' % (mstr, remotepath))
        except (Exception):
            try:
                # try MDTM second
                self.ftp.sendcmd('MDTM %s %s' % (mstr, remotepath))
            except (Exception):
                if not ignore_error:
                    raise IOError('Failed to sent modified time of file %s' % remotepath)

    def remove(self, pathname):
        '''remove file (remove directory using `rmdir` instead)'''
        if self.isfile(pathname):
            self.ftp.delete(pathname)
        else:
            raise IOError('%s is not exist, or not file' % pathname)

    def rmdir(self, pathname, force=False):
        '''remove an directory
        :param str pathname : directory path to remove
        :param bool force: force remove directory even not empty

        :raise IOError
        '''
        if not self.isdir(pathname):
            raise IOError('%s is not directory' % pathname)

        try:
            self.ftp.rmd(pathname)
        except error_temp as e:
            if not force:
                raise IOError('Directory %s is not exist or not empty' % pathname)
            def inner_rm(dirname):
                with self.cd(dirname):
                    for entry in self.listdir('.'):
                        if self.isfile(entry):
                            self.ftp.delete(entry)
                        else:
                            inner_rm(entry)
                self.ftp.rmd(dirname)
            return inner_rm(pathname)


    def mkdir(self, pathname):
        '''make directory under current folder
        :param str pathname:
            path name to create
        :return str
            return parent path name
        '''
        try:
            self.ftp.mkd(pathname)
        except error_perm as e:
            pass

    def makedirs(self, pathname):
        '''create all dirs in the pathname if not exist'''
        try:
            pathname = pathname.replace('\\', '/')
            resp = self.ftp.sendcmd('SITE MKDIR %s' % pathname)
            return resp[0] == 2
        except error_perm as e:
            # SITE MKDIR is not supported, then create it recursively
            with self.cd('.'):
                for d in pathname.split('/'):
                    if d == '.' or d == '':
                        continue
                    elif d == '..':
                        self.ftp.cwd('..')
                    else:
                        self.mkdir(d)
                        self.ftp.cwd(d)


    def listdir(self, pathname=None):
        '''get files/dirs under path

        :param str|None pathname
            dir path name
        :return list
            return stat list of specified pathname
        '''
        f_list, d_list = [], []
        with self.cd(pathname or '.'):
            rpath = self.ftp.pwd()
            if rpath == '/': rpath = ''

            dir_resp = []
            self.ftp.dir('.', dir_resp.append)

            for entry in dir_resp:
                ss = entry.split(None, 8)
                if len(ss) != 9:
                    raise ValueError('Invalid dir item: {0}'.format(entry))
                if ss[-1] == '.' or ss[-1] == '..':
                    continue
                
                st_size, st_time = 0, 0
                st_name = rpath + '/' + ss[-1]
                # analyze mode string
                st_mode = StatResult.parse_mode(ss[0])

                # file size, modified time
                if stat.S_ISREG(st_mode):
                    st_size = long(ss[4])
                    st_time = self.get_mtime(st_name)
                
                # new an stat oject
                fd_stat = StatResult((st_mode, None, None, None, None,
                    None, st_size, st_time, st_time, st_time))
                
                fd_stat.st_name = ss[-1]
                fd_stat.st_path = st_name

                if stat.S_ISREG(st_mode):
                    f_list.append(fd_stat)
                else:
                    d_list.append(fd_stat)
        
        d_list.extend(f_list)
        return d_list


    def _mt_sec(self, timestr):
        tmf = '%Y%m%d%H%M%S'
        return long(time.mktime(time.strptime(timestr, tmf)) - time.timezone)

    def _sec_mt(self, timesec):
        tmf = '%Y%m%d%H%M%S'
        return time.strftime(tmf, time.gmtime(timesec))


    def stat(self, pathname):
        ''''Retrieve limit file stat from ftp server
        !Important, folder not supported

        :param str pathname:
            the file path relative or full path
        '''
        if pathname is None or pathname == '.':
            return None
        
        try:
            resp = []
            self.ftp.dir(pathname, resp.append)

            ss = resp[0].split(None, 8)
            if ss[-1] != os.path.basename(pathname):
                raise NotImplementedError('stat function not support for item {0}'.format(pathname))

            st_size = long(ss[4])
            st_time = self.get_mtime(pathname)
            st_mode = StatResult.parse_mode(ss[0])
            
            # new an stat oject
            f_stat = StatResult((st_mode, None, None, None, None, 
                None, st_size, st_time, st_time, st_time))

            return f_stat
        except (error_perm, Exception):
            return None
        



    def get(self, remotepath, localpath=None, preserve_mtime=False):
        """Copies a file between the remote host and the local host.

        :param str remotepath: the remote path and filename, source
        :param str localpath:
            the local path and filename to copy, destination. If not specified,
            file is copied to local current working directory
        :param bool preserve_mtime:
            *Default: False* - make the modification time(st_mtime) on the
            local file match the time on the remote. (st_atime can differ
            because stat'ing the localfile can/does update it's st_atime)
        :raises: IOError
        """
        if not localpath:
            localpath = os.path.split(remotepath)[1]

        if preserve_mtime:
            mtime = self.get_mtime(remotepath)

        with open(localpath, 'wb') as f:
            # actual get file content
            self.ftp.retrbinary('RETR %s' % remotepath, f.write)

        if preserve_mtime:
            os.utime(localpath, (mtime, mtime))



    def get_d(self, remotedir, localdir, preserve_mtime=False):
        """get the contents of remotedir and write to locadir. (non-recursive)

        :param str remotedir: the remote directory to copy from (source)
        :param str localdir: the local directory to copy to (target)
        :param bool preserve_mtime: *Default: False* -
            preserve modification time on files

        :returns: 
            download files' count
        :raises:
            IOError if path not exist
        """
        if not os.path.exists(localdir):
            os.mkdir(localdir)

        if not self.exists(remotedir):
            raise IOError('Remote path {0} not exist.'.format(remotedir))
        
        file_cnt = 0
        with self.cd(remotedir), self.lcd(localdir):
            for name in self.listdir('.'):
                if self.isfile(name):
                    self.get(name, name, preserve_mtime=preserve_mtime)
                    file_cnt += 1
        return file_cnt


    def get_r(self, remotedir, localdir, preserve_mtime=False):
        """recursively copy remotedir structure to localdir

        :param str remotedir: the remote directory to copy from
        :param str localdir: the local directory to copy to
        :param bool preserve_mtime: *Default: False* -
            preserve modification time on files

        :returns: list 
            (dirs_cnt, files_cnt)
        :raises:
            IOError if path not exist
        """
        if not os.path.exists(localdir):
            raise IOError('Local path {0} not exist.'.format(localdir))

        if not self.exists(remotedir):
            raise IOError('Remote path {0} not exist.'.format(remotedir))

        def inner_get(remotedir, localdir):
            '''get file / dir recursively'''
            with self.cd(remotedir), self.lcd(localdir):
                dcnt, fcnt = 0, 0
                for name in self.listdir('.'):
                    if name == '.' or name == '..':
                        continue
                    elif self.isfile(name):
                        self.get(name, name, preserve_mtime=preserve_mtime)
                        fcnt += 1
                    else:
                        if not os.path.exists(name):
                            os.mkdir(name)
                        dcnt += 1
                        rs = inner_get(name, name)
                        dcnt, fcnt = rs[0] + dcnt, rs[1] + fcnt
                return (dcnt, fcnt)
         
        return inner_get(remotedir, localdir)



    def put(self, localpath, remotepath=None, preserve_mtime=False):
        """Copies a file between the local host and the remote host.

        :param str localpath: the local path and filename
        :param str remotepath:
            the remote path, else the remote :attr:`.pwd` and filename is used.
        :param bool preserve_mtime:
            *Default: False* - make the modification time(st_mtime) on the
            remote file match the time on the local. (st_atime can differ
            because stat'ing the localfile can/does update it's st_atime)

        :raises IOError: 
            if epath doesn't exist
        """
        if not os.path.exists(localpath):
            raise IOError('Local path {0} not exist.'.format(localpath))

        if not remotepath:
            remotepath = os.path.split(localpath)[1]

        if preserve_mtime:
            l_stat = os.stat(localpath)

        with open(localpath, 'rb') as fp:
            # actual upload file content
            self.ftp.storbinary('STOR %s' % remotepath, fp)
        
        if preserve_mtime:
            self.set_mtime(remotepath, l_stat.st_mtime)


    def put_d(self, localpath, remotepath, preserve_mtime=False):
        """Copies a local directory's contents to a remotepath

        :param str localpath: the local path to copy (source)
        :param str remotepath:
            the remote path to copy to (target)
        :param bool preserve_mtime:
            *Default: False* - make the modification time(st_mtime) on the
            remote file match the time on the local. (st_atime can differ
            because stat'ing the localfile can/does update it's st_atime)

        :returns:
            uploaded files' count 
        :raises IOError: 
            if path doesn't exist
        """
        if not os.path.exists(localpath):
            raise IOError('Local path {0} not exist.'.format(localpath))

        if not self.exists(remotepath):
            raise IOError('Remote path {0} not exist.'.format(remotepath))

        file_cnt = 0
        with self.lcd(localpath), self.cd(remotepath):
            for entry in os.listdir('.'):
                if os.path.isfile(entry):
                    self.put(entry, entry, preserve_mtime=preserve_mtime)
                    file_cnt += 1

        return file_cnt


    def put_r(self, localpath, remotepath, preserve_mtime=False):
        """Recursively copies a local directory's contents to a remotepath

        :param str localpath: the local path to copy (source)
        :param str remotepath:
            the remote path to copy to (target)
        :param bool preserve_mtime:
            *Default: False* - make the modification time(st_mtime) on the
            remote file match the time on the local. (st_atime can differ
            because stat'ing the localfile can/does update it's st_atime)
        
        :return:
            (dirs_count, files_count)
        :raises IOError:
            if path doesn't exist
        """
        if not os.path.exists(localpath):
            raise IOError('Local path {0} not exist.'.format(localpath))
            
        if not self.exists(remotepath):
            raise IOError('Remote path {0} not exist.'.format(remotepath))
        
        dcnt, fcnt = 0, 0
        with self.lcd(localpath), self.cd(remotepath):
            for root, dirs, files in os.walk('.'):
                rpath = root.replace('\\', '/')
                for fd in files:
                    self.put(os.path.join(root, fd), rpath + '/' + fd, preserve_mtime=preserve_mtime)
                    fcnt += 1
                for fd in dirs:
                    self.mkdir(rpath + '/' +fd)
                    dcnt += 1
        
        return (dcnt, fcnt)
        '''
        def inner_put(localdir, remotedir):
            with self.lcd(localdir), self.cd(remotedir):
                dcnt, fcnt = 0, 0
                for entry in os.listdir('.'):
                    if os.path.isfile(entry):
                        self.put(entry, entry, preserve_mtime=preserve_mtime)
                        fcnt += 1
                    else:
                        self.mkdir(entry)
                        dcnt += 1

                        rs = inner_put(entry, entry)
                        dcnt, fcnt = rs[0] + dcnt, rs[1] + fcnt
                return (dcnt, fcnt)
        return inner_put(localpath, remotepath)
        '''