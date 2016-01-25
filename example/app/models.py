# -*- coding: utf-8 -*-

from django.db import models

# from xadmin.dmqs.manager import MemoryManager


from django.core.exceptions import MultipleObjectsReturned, \
                                    ObjectDoesNotExist


def type_and_instance(type_name, **kwargs):
    _id = 'id'
    new_class = type(type_name, (object,), {
        '__eq__': lambda x, y: x.__dict__[_id] == y.__dict__[_id],
        '__ne__': lambda x, y: x.__dict__[_id] != y.__dict__[_id],
        '__lt__': lambda x, y: x.__dict__[_id] < y.__dict__[_id],
        '__gt__': lambda x, y: x.__dict__[_id] > y.__dict__[_id]
    })
    instance = new_class()
    instance.__dict__ = kwargs
    return instance

instance_id = 1

def type_and_instance_attr_eq(type_name, **kwargs):
    global instance_id
    attr = 'id'

    new_class = type(type_name, (object,),
    {
        '__eq__': lambda x, y: x.id == y.id,
        '__ne__': lambda x, y: x.id != y.id,
    })
    instance = new_class()
    instance.__dict__ = kwargs
    instance.__dict__['id'] = instance_id
    instance_id += 1
    setattr(new_class, 'DoesNotExist', ObjectDoesNotExist)
    setattr(new_class, 'MultipleObjectsReturned', MultipleObjectsReturned)
    return instance


person1 = type_and_instance_attr_eq('MyModel',
                            pk = 1,
                            name="Name 1",
                            description="Nickname 1",
                            memory=True)

person2 = type_and_instance_attr_eq('MyModel',
                           pk = 1,
                            name="Name 2",
                            description="Nickname 2",
                            memory=True)

person3 = type_and_instance_attr_eq('MyModel',
                            pk = 1,
                            name="Name 2",
                            description="Nickname 3",
                            memory=True)

data = [person1, person2, person3]


SERVER_STATUS = (
    (0, u"Normal"),
    (1, u"Down"),
    (2, u"No Connect"),
    (3, u"Error"),
)
SERVICE_TYPES = (
    ('moniter', u"Moniter"),
    ('lvs', u"LVS"),
    ('db', u"Database"),
    ('analysis', u"Analysis"),
    ('admin', u"Admin"),
    ('storge', u"Storge"),
    ('web', u"WEB"),
    ('email', u"Email"),
    ('mix', u"Mix"),
)


class IDC(models.Model):
    name = models.CharField(max_length=64)
    description = models.TextField()

    contact = models.CharField(max_length=32)
    telphone = models.CharField(max_length=32)
    address = models.CharField(max_length=128)
    customer_id = models.CharField(max_length=128)

    create_time = models.DateField(auto_now=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = u"IDC"
        verbose_name_plural = verbose_name


class Host(models.Model):
    idc = models.ForeignKey(IDC)
    name = models.CharField(max_length=64)
    nagios_name = models.CharField(u"Nagios Host ID", max_length=64, blank=True, null=True)
    ip = models.IPAddressField(blank=True, null=True)
    internal_ip = models.IPAddressField(blank=True, null=True)
    user = models.CharField(max_length=64)
    password = models.CharField(max_length=128)
    ssh_port = models.IntegerField(blank=True, null=True)
    status = models.SmallIntegerField(choices=SERVER_STATUS)

    brand = models.CharField(max_length=64, choices=[(i, i) for i in (u"DELL", u"HP", u"Other")])
    model = models.CharField(max_length=64, default='', blank=True,null=True)
    cpu = models.CharField(max_length=64)
    core_num = models.SmallIntegerField(choices=[(i * 2, "%s Cores" % (i * 2)) for i in range(1, 15)])
    hard_disk = models.IntegerField()
    memory = models.IntegerField()

    system = models.CharField(u"System OS", max_length=32, choices=[(i, i) for i in (u"CentOS", u"FreeBSD", u"Ubuntu")])
    system_version = models.CharField(max_length=32)
    system_arch = models.CharField(max_length=32, choices=[(i, i) for i in (u"x86_64", u"i386")])

    create_time = models.DateField()
    guarantee_date = models.DateField()
    service_type = models.CharField(max_length=32, choices=SERVICE_TYPES)
    description = models.TextField()

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = u"Host"
        verbose_name_plural = verbose_name


class MaintainLog(models.Model):
    host = models.ForeignKey(Host)
    maintain_type = models.CharField(max_length=32)
    hard_type = models.CharField(max_length=16)
    time = models.DateTimeField()
    operator = models.CharField(max_length=16)
    note = models.TextField()

    def __unicode__(self):
        return '%s maintain-log [%s] %s %s' % (self.host.name, self.time.strftime('%Y-%m-%d %H:%M:%S'),
                                               self.maintain_type, self.hard_type)

    class Meta:
        verbose_name = u"Maintain Log"
        verbose_name_plural = verbose_name


class HostGroup(models.Model):

    name = models.CharField(max_length=32)
    description = models.TextField()
    hosts = models.ManyToManyField(
        Host, verbose_name=u'Hosts', blank=True, related_name='groups')

    class Meta:
        verbose_name = u"Host Group"
        verbose_name_plural = verbose_name

    def __unicode__(self):
        return self.name
    
# class MyModel(models.Model):
# 
#     name = models.CharField(max_length=32)
#     description = models.TextField()
#     #idc = models.ManyToManyField(IDC)
# 
# #    _base_manager = MemoryManager()
#     objects = MemoryManager()
#     _default_manager = objects
#     _base_manager = objects
# #    _default_manager = MemoryManager(None)
#     data = data
# 
#     class Meta:
#         verbose_name = u"抽象模型"
#         verbose_name_plural = verbose_name
# 
#     def __unicode__(self):
#         return self.name
    
#MyModel.objects = MemoryManager(MyModel)
    
# class MyModel2(models.Model):
# 
#     name = models.CharField(max_length=32)
#     description = models.TextField()
#     fn = models.ForeignKey(MyModel)
# 
#     class Meta:
#         verbose_name = u"抽象模型2"
#         verbose_name_plural = verbose_name
# 
#     def __unicode__(self):
#         return self.name


class AccessRecord(models.Model):
    date = models.DateField()
    user_count = models.IntegerField()
    view_count = models.IntegerField()

    class Meta:
        verbose_name = u"Access Record"
        verbose_name_plural = verbose_name

    def __unicode__(self):
        return "%s Access Record" % self.date.strftime('%Y-%m-%d')
