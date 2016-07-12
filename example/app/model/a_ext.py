# coding=utf-8

from django.db import models
from xadmin.util import User

from a import A

class AExt(object):
    
    def ename(self):
        return self.name

A.merge_class(AExt)