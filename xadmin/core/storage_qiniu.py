# coding=utf-8
import StringIO
import os
import datetime
import posixpath
try:
    import six
    from six.moves.urllib_parse import urljoin
except:
    pass
import urlparse
import logging

from django.core.files.base import File
from django.utils.encoding import force_text, force_bytes, filepath_to_uri
from django.core.files.storage import Storage
from django.core.exceptions import SuspiciousOperation
from django.conf import settings

try:
    import qiniu    # for v6.1.6
    from qiniu import resumable_io as rio
    from qiniu import rs as qiniu_rs
    
    qiniu.conf.ACCESS_KEY = settings.QINIU_CONF['access_key']
    qiniu.conf.SECRET_KEY = settings.QINIU_CONF['secret_key']
    qiniu_bucket = settings.QINIU_CONF['bucket']
except:
    pass

log = logging.getLogger('django.request')

def upload_by_rawdata(rawdata, length):
    
    policy = qiniu_rs.PutPolicy(qiniu_bucket)
    uptoken = policy.token()
    extra = rio.PutExtra(qiniu_bucket)
    ret, err = rio.put(uptoken, None, rawdata, length, extra)
    if err is not None:
        log.error('rio put raw file return ret:%s, err:%s' %(str(ret), err))
        return None
    else:
        log.info('rio put raw file return ret:%s, err:%s' %(str(ret), err))

    return ret['key']


def save_imgs(imgs, ret_size=False):
    import Image
    result = []
    for img in imgs:
        qiniu_key = upload_by_rawdata(img, len(img))
        log.info('upload stream img to qiniu, return: %s' % (qiniu_key,))
        img_width = 0
        img_height = 0 
        if ret_size:
            s = ''
            for c in img.chunks():
                s += c
            imagefile = StringIO.StringIO(s)
            im = Image.open(imagefile)
            img_width, img_height = im.size
        result.append({'img':'/'+qiniu_key.lstrip('/'),'img_width':img_width,'img_height':img_height})
    return result


class QiniuFile(File):
    def __init__(self, name, storage, mode):
        self._storage = storage
        self._name = name[len(self._storage.location):].lstrip('/')
        self._mode = mode
        self.file = six.BytesIO()
        self._is_dirty = False
        self._is_read = False

    @property
    def size(self):
        if self._is_dirty or self._is_read:
            # Get the size of a file like object
            # Check http://stackoverflow.com/a/19079887
            old_file_position = self.file.tell()
            self.file.seek(0, os.SEEK_END)
            self._size = self.file.tell()
            self.file.seek(old_file_position, os.SEEK_SET)
        if not hasattr(self, '_size'):
            self._size = self._storage.size(self._name)
        return self._size

    def read(self, num_bytes=None):
        if not self._is_read:
            content = self._storage._read(self._name)
            self.file = six.BytesIO(content)
            self._is_read = True

        if num_bytes is None:
            data = self.file.read()
        else:
            data = self.file.read(num_bytes)

        if 'b' in self._mode:
            return data
        else:
            return force_text(data)

    def write(self, content):
        if 'w' not in self._mode:
            raise AttributeError("File was opened for read-only access.")

        self.file.write(force_bytes(content))
        self._is_dirty = True
        self._is_read = True

    def close(self):
        if self._is_dirty:
            self.file.seek(0)
            self._storage._save(self._name, self.file)
        self.file.close()
        
class QiniuStorage(Storage):
    """
    Qiniu Storage Service
    """
    location = ""

    def __init__(self):
        pass

    def _clean_name(self, name):
        """
        Cleans the name so that Windows style paths work
        """
        # Normalize Windows style paths
        clean_name = posixpath.normpath(name).replace('\\', '/')

        # os.path.normpath() can strip trailing slashes so we implement
        # a workaround here.
        if name.endswith('/') and not clean_name.endswith('/'):
            # Add a trailing slash as it was stripped.
            return clean_name + '/'
        else:
            return clean_name

    def _normalize_name(self, name):
        """
        Normalizes the name so that paths like /path/to/ignored/../foo.txt
        work. We check to make sure that the path pointed to is not outside
        the directory specified by the LOCATION setting.
        """

        base_path = force_text(self.location)
        base_path = base_path.rstrip('/')

        final_path = urljoin(base_path.rstrip('/') + "/", name)

        base_path_len = len(base_path)
        if (not final_path.startswith(base_path) or
                final_path[base_path_len:base_path_len + 1] not in ('', '/')):
            raise SuspiciousOperation("Attempted access to '%s' denied." %
                                      name)
        return final_path.lstrip('/')

    def _open(self, name, mode='rb'):
        return QiniuFile(name, self, mode)

    def _save(self, name, content):
        cleaned_name = self._clean_name(name)
        name = self._normalize_name(cleaned_name)

        if hasattr(content, 'open'):
            # Since Django 1.6, content should be a instance
            # of `django.core.files.File`
            content.open()

        res = self._put_file(name, content)
        content.close()
        return '/%s'%res

    def _put_file(self, name, content):
        log.info('>>> QiniuStorage put_file: %s'%name)
        qiniu_key = upload_by_rawdata(content, len(content))
        log.info('upload stream img to qiniu, return: %s' % (qiniu_key,))
        return qiniu_key

    def _read(self, name):
        import requests
        log.info('>>> QiniuStorage read: %s'%name)
        return requests.get(self.full_url(name)).content

    def delete(self, name):
        name = self._normalize_name(self._clean_name(name))
        if six.PY2:
            name = name.encode('utf-8')
        log.info('>>> QiniuStorage delete: %s'%name)

    def _file_stat(self, name, silent=False):
        name = self._normalize_name(self._clean_name(name))
        if six.PY2:
            name = name.encode('utf-8')
        log.info('>>> QiniuStorage _file_stat: %s'%name)
        return None

    def exists(self, name):
        stats = self._file_stat(name, silent=True)
        return True if stats else False

    def size(self, name):
        stats = self._file_stat(name)
        if stats:
            return stats['fsize']
        else:
            return len(self._read(name))

    def modified_time(self, name):
        stats = self._file_stat(name)
        if stats:
            time_stamp = float(stats['putTime']) / 10000000
            return datetime.datetime.fromtimestamp(time_stamp)
        else:
            return None

    def listdir(self, name):
        name = self._normalize_name(self._clean_name(name))
        if name and not name.endswith('/'):
            name += '/'
        log.info('>>> QiniuStorage listdir: %s'%name)
        return [], []

    def full_url(self, name):
        name = self._normalize_name(self._clean_name(name))
        name = filepath_to_uri(name)
        full_url = urlparse.urljoin(settings.REMOTE_MEDIA_URL, name)
        log.info('>>> QiniuStorage full_url: %s'%name)
        return full_url
    
    def url(self, name):
        name = self._normalize_name(self._clean_name(name))
        name = filepath_to_uri(name)
        return '/%s'%name
