#!/usr/bin/env python3


import getpass
from hs_restclient import HydroShare, HydroShareAuthBasic


def __connect(username):
    u = username
    p = getpass.getpass('Password:')
    auth = HydroShareAuthBasic(username=u, password=p)
    return HydroShare(auth=auth)


def connect():
    u = input('username: ')
    return __connect(u)
