# -*- coding: utf-8 -*-

import json
#import schedule

import sys
import urllib
import urllib2
import ssl
import time as t

from datetime import datetime, time, timedelta
sys.path.append("/home/stashboard/secrets/")
from secrets import z6_kiosk_user, z6_kiosk_pass, z6_url

ZENOSS_INSTANCE = z6_url
ZENOSS_USERNAME = z6_kiosk_user
ZENOSS_PASSWORD = z6_kiosk_pass

ROUTERS = { 'MessagingRouter': 'messaging',
            'EventsRouter': 'evconsole',
            'ProcessRouter': 'process',
            'ServiceRouter': 'service',
            'DeviceRouter': 'device',
            'NetworkRouter': 'network',
            'TemplateRouter': 'template',
            'DetailNavRouter': 'detailnav',
            'ReportRouter': 'report',
            'MibRouter': 'mib',
            'ZenPackRouter': 'zenpack' }

class ZenossAPI():
    def __init__(self, debug=False):
        """
        Initialize the API connection, log in, and store authentication cookie
        """

        # Use the HTTPCookieProcessor as urllib2 does not save cookies by default
	# ctx = ssl.create_default_context(cafile = '/etc/ssl/certs/zenoss6_sint_uib_es.crt')
        # Falla la verificacio de la cadena

        ctx=ssl._create_unverified_context()
        self.urlOpener = urllib2.build_opener(urllib2.HTTPSHandler(context=ctx), urllib2.HTTPCookieProcessor())
        if debug: self.urlOpener.add_handler(urllib2.HTTPHandler(debuglevel=1))
        self.reqCount = 1

        # Contruct POST params and submit login.
        loginParams = urllib.urlencode(dict(
                        __ac_name = ZENOSS_USERNAME,
                        __ac_password = ZENOSS_PASSWORD,
                        submitted = 'true',
                        came_from = ZENOSS_INSTANCE + '/zport/dmd'))
        self.urlOpener.open(ZENOSS_INSTANCE + '/zport/acl_users/cookieAuthHelper/login',
                            loginParams)

    def _router_request(self, router, method, data=[]):
        if router not in ROUTERS:
            raise Exception('Router "' + router + '" not available.')

        # Contruct a standard URL request for API calls
        req = urllib2.Request(ZENOSS_INSTANCE + '/zport/dmd/' +
                              ROUTERS[router] + '_router')

        # NOTE: Content-type MUST be set to 'application/json' for these requests
        req.add_header('Content-type', 'application/json; charset=utf-8')

        # Convert the request parameters into JSON
        reqData = json.dumps([dict(
                    action=router,
                    method=method,
                    data=data,
                    type='rpc',
                    tid=self.reqCount)])

        # Increment the request count ('tid'). More important if sending multiple
        # calls in a single request
        self.reqCount += 1
        # Submit the request and convert the returned JSON to objects
        return json.loads(self.urlOpener.open(req, reqData).read())

    def _simple_get_request(self, path):
	req = urllib2.Request(ZENOSS_INSTANCE + path)
	req.add_header('Content-type', 'application/json; charset=utf-8')
	return self.urlOpener.open(req).read()


    def get_devices(self, deviceClass='/zport/dmd/Devices'):
        return self._router_request('DeviceRouter', 'getDevices',
                                    data=[{'uid': deviceClass,
                                           'limit': 200,  # Aquest parametre limita el numero de resultats. IMPORTANT
                                           'params': {} }])['result']

    def get_events(self, device=None, component=None, eventClass=None):
        data = dict(start=0, limit=100, dir='DESC', sort='severity')
        data['params'] = dict(severity=[5,4,3,2], eventState=[0,1])

        if device: data['params']['device'] = device
        if component: data['params']['component'] = component
        if eventClass: data['params']['eventClass'] = eventClass

	if device == None:
		return self._router_request('EventsRouter', 'query', [data])['result']
	else:
	        events = self._router_request('EventsRouter', 'query', [data])['result']
		for i in events['events']:
			if i['device']['text'] != device:
				events['events'].remove(i)
		return events
				
    def get_UID(self, device):
        return self._router_request('DeviceRouter', 'getDevices',
                                    data=[{'uid': '/zport/dmd/Groups/serveis/serveis_critics',
                                           'params': {'name': device} }])['result']['devices'][0]['uid']

    def get_group(self, device):
	# Retorna el grup on es troba dins serveis critics
        groups=self._router_request('DeviceRouter', 'getDevices',
                                    data=[{'uid': '/zport/dmd/Groups/serveis/serveis_critics',
                                           'params': {'name': device} }])['result']['devices'][0]['groups']
	
	for i in groups:
		len=i['path'].find("serveis/serveis_critics/")
		if len > -1:
			return i['path'][len+23:].replace("/","")
	raise Exception("No esta Dins cap grup")
			
    def get_devicecomment(self, device_uid):
	# Se li ha de passar forçosament un uid de Device Class
        try:
		comment=self._router_request('DeviceRouter', 'getInfo',data=[{'uid': device_uid}])['result']['data']['comments']
	except Exception as e:
		print "Error gathering comment in get_devicecomment " + device_uid + "... trying again"
		t.sleep(2)
		comment=self._router_request('DeviceRouter', 'getInfo',data=[{'uid': device_uid}])['result']['data']['comments']
	if comment == "":
		t.sleep(2)
		comment=self._router_request('DeviceRouter', 'getInfo',data=[{'uid': device_uid}])['result']['data']['comments']
                if comment == "":
                	t.sleep(2)
	                comment=self._router_request('DeviceRouter', 'getInfo',data=[{'uid': device_uid}])['result']['data']['comments']
			if comment == "":
				raise Exception("No te cap comentari");
	else:
		return comment

    def get_devicePrivateName(self, device_uid_path):
        # Se li ha de passar forçosament un uid de Device Class amb el path sencer
        # Parsejam el nom del dispositiu. Aquest anirà contingut dins el camp Comments del Zenoss de la forma següent:
        # cachet=<nom>;
       comentari=self.get_devicecomment(device_uid_path)
       print "I am in get_devicePrivateName with comentari:" + comentari
       print "---"
       offset0=comentari.find("cachet=");
       offset1=comentari.find(";");
       if offset0 > -1 and offset1 > -1:
               nom=comentari[offset0+7:offset1]
       else:  
               raise Exception("Comentari al Zenoss mal format. El nom va contingut dins cachet=<nom>;")
       return nom


    def get_devicePublicName(self, device_uid_path):
        # Se li ha de passar forçosament un uid de Device Class amb el path sencer
        # Parsejam el nom public del dispositiu. Aquest anirà contingut dins el camp Comments del Zenoss de la forma següent:
        # public=<nom>;
        comentari=self.get_devicecomment(device_uid_path)
        offset2=comentari.find("public=");
        offset3=comentari.find(";",offset2+1)
        if offset2 > -1 and offset3 > -1:
                nompublic=comentari[offset2+7:offset3]
        else:
                raise Exception("Comentari al Zenoss mal format. El nom públic va contingut dins public=<nom>;")
	return nompublic

    def isMaintWindowActive(self,id):
	if self._simple_get_request(id+"/maintenanceWindowDetail").find("<td class=\"tablevalues\">True</td>") > -1:
		return "True"
	else:
		return "False"

    def get_deviceMaintWindows(self,device_uid):
	mw_list_p = self._simple_get_request(device_uid+"/maintenanceWindows/")
	mw_list=mw_list_p[23:-2].split(">, <MaintenanceWindow at ")
	l_mw=[]
	mw={}
	if mw_list[0] == '':
		return []
	for i in mw_list:
		try:
			if self.isMaintWindowActive(i) == "True":
				start = datetime.fromtimestamp(float(self._simple_get_request(i+"/getProperty?id=start")))
				duration = timedelta(minutes=float(self._simple_get_request(i+"/getProperty?id=duration")))
				if start+duration > datetime.now():
					name = self._simple_get_request(i+"/getProperty?id=name")
					mw["nom"]=name
					mw["start"]=start
					mw["end"]=start+duration
					mw["id"]=i
					l_mw.append(mw)
					mw={}
		except Exception as e:
			pass
		
	return l_mw

    def is_inMaintenanceWindow(self, device_uid):
	mw = self.get_deviceMaintWindows(device_uid)
        for w in mw:
                sta_time=w["start"]
                end_time=w["end"]
                if datetime.now() < end_time and datetime.now() > sta_time and self.isMaintWindowActive(w["id"]) == "True": # Miram si estam en hora...
			return "True"
	return "False"	
#	status=self._simple_get_request(device_uid+"/getProductionStateString")
#	if status=="Maintenance":
#		return "True"
#	else:
#		return "False"

    def add_device(self, deviceName, deviceClass):
        data = dict(deviceName=deviceName, deviceClass=deviceClass)
        return self._router_request('DeviceRouter', 'addDevice', [data])

    def create_event_on_device(self, device, severity, summary):
        if severity not in ('Critical', 'Error', 'Warning', 'Info', 'Debug', 'Clear'):
            raise Exception('Severity "' + severity +'" is not valid.')

        data = dict(device=device, summary=summary, severity=severity,
                    component='', evclasskey='', evclass='')
        return self._router_request('EventsRouter', 'add_event', [data])




