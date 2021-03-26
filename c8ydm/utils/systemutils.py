#!/usr/bin/env python
# -*- coding: utf-8 -*-
from uuid import getnode

def getSerial():
  return str(getnode())
