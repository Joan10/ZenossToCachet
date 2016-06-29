#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import re
import requests
import unittest
import random
import os
import sys
from datetime import datetime, timedelta, time
from os import listdir
from os.path import isfile, join
from subprocess import Popen, PIPE


class schedule:


	MESSAGE_FORMAT="El servei %s estarà aturat per tasques de manteniment des del dia %s a les %s fins el dia %s a les %s."

	name=""
	zdevice=""
	message=""
	start_time=""
	end_time=""
	cachet_id=""


	
	def __init__(self, name):
		if isinstance(name,str) == False:
			return ValueError("Invalid schedule initialization")
		self.name=name

	def fromDate(self, start_time, end_time, zdevice, cachet_id = 0):
		if isinstance(cachet_id,int) == False or isinstance(start_time,datetime) == False or isinstance(end_time,datetime) == False or isinstance(zdevice,str) == False:
			raise ValueError("Invalid schedule initialization")

		self.start_time=start_time
		self.end_time=end_time
		self.cachet_id=cachet_id
		self.zdevice=zdevice
                self.message=self.calculaMessage()

	def fromDuration(self, start_time, zdevice,  duration=timedelta(minutes=60), cachet_id = 0):
                if isinstance(cachet_id,int) == False or isinstance(start_time,datetime) == False or isinstance(duration,timedelta) == False or isinstance(zdevice,str) == False:
                        raise ValueError("Invalid schedule initialization")
		
                self.start_time=start_time
                self.end_time=start_time+duration
                self.cachet_id=cachet_id
		self.zdevice=zdevice
                self.message=self.calculaMessage()


	def fromMessage(self, message, cachet_id = 0):
                if isinstance(cachet_id,int) == False or isinstance(message,str) == False:
                        raise ValueError("Invalid schedule initialization")

                self.cachet_id=cachet_id
		self.message=message
		r=self.MESSAGE_FORMAT.replace("%s","(?P<serv>.*)",1).replace("%s","(?P<d0>.*)",1).replace("%s","(?P<h0>.*)",1).replace("%s","(?P<d1>.*)",1).replace("%s","(?P<h1>.*)",1)
		di=re.compile(r).match(message)
		if di:
                	self.zdevice=di.groupdict()['serv']
                	self.start_time=datetime.strptime(di.groupdict()['d0'] + " " + di.groupdict()['h0'], "%d-%m-%Y %H:%M")
                	self.end_time=datetime.strptime(di.groupdict()['d1'] + " " + di.groupdict()['h1'], "%d-%m-%Y %H:%M")
		else:	
			raise ValueError("Invalid schedule initialization: Message wrong")

	def calculaMessage(self):
		return self.MESSAGE_FORMAT % (self.zdevice, self.start_time.strftime("%d-%m-%Y"), self.start_time.strftime("%H:%M"),self.end_time.strftime("%d-%m-%Y"), self.end_time.strftime("%H:%M"))		




        def calculaEndTime(self):
		i1=self.message.find("fins el dia")
		if i1 == -1:
			raise NameError('Cannot find proper message format on schedule')
                str1=self.message[i1+len("fins el dia "):]
		i2=str1.find(" a les ")
                if i2 == -1:
                        raise NameError('Cannot find proper message format on schedule')
                data=str1[:i2]
                hora=str1[i2+len(" a les "):-1]
		try:
			dt=datetime.strptime(data+" "+hora, '%d-%m-%Y %H:%M')
		except Exception as e:
			raise NameError('Cannot find proper message format on schedule')

                return dt


        def calculaComponent(self):
                i1=self.message.find("El servei")
                if i1 == -1:
                        raise NameError('Cannot find proper message format on schedule')
                str1=self.message[i1+len("fins el dia "):]
                i2=str1.find(" a les ")
                if i2 == -1:
                        raise NameError('Cannot find proper message format on schedule')
                data=str1[:i2]
                hora=str1[i2+len(" a les "):-1]
                try:   
                        dt=datetime.strptime(data+" "+hora, '%d-%m-%Y %H:%M')
                except Exception as e:
                        raise NameError('Cannot find proper message format on schedule')

                return dt



	def treuEndTime(self):
		return self.end_time
	def treuName(self):
		return self.name
	def treuStartTime(self):
		return self.start_time
	def treuId(self):
		return self.cachet_id
	def treuComponent(self):
		return self.zdevice
	def treuMessage(self):
		return self.message
	def treuDuracio(self):
	#retorna un timedelta
		return self.end_time-self.start_time

	def isEqual(self,s1):
		if self.zdevice == s1.zdevice and self.start_time==s1.start_time and self.end_time==s1.end_time:
			return True
		else:
			return False

	def pinta(self):
		print "Name: "+self.name
		print "Start Time: "+self.start_time.strftime("%d-%m-%Y %H:%M")
		print "End Time: "+self.end_time.strftime("%d-%m-%Y %H:%M")
		print "Duration: "+str(self.treuDuracio())
		print "Zenoss Device: "+self.zdevice
		print "Message: "+self.message
		print "Cachet Id: "+str(self.cachet_id)
