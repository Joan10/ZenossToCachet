# -*- coding: utf-8 -*-

import json

import urllib
import urllib2
from datetime import datetime, time, timedelta


ZENOSS_INSTANCE = 'http://192.168.41.40:8080'
ZENOSS_USERNAME = 'kiosk'
ZENOSS_PASSWORD = 'kiosk'

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
        self.urlOpener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
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
                                           'params': {} }])['result']

    def get_events(self, device=None, component=None, eventClass=None):
        data = dict(start=0, limit=100, dir='DESC', sort='severity')
        data['params'] = dict(severity=[5,4,3,2], eventState=[0,1])

        if device: data['params']['device'] = device
        if component: data['params']['component'] = component
        if eventClass: data['params']['eventClass'] = eventClass

        return self._router_request('EventsRouter', 'query', [data])['result']

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
	raise Exception("No esta dins cap grup")
			
    def get_devicecomment(self, device_uid):
	# Se li ha de passar forçosament un uid de Device Class
        comment=self._router_request('DeviceRouter', 'getInfo',data=[{'uid': device_uid}])['result']['data']['comments']
	if comment == "":
		raise Exception("No te cap comentari");
	else:
		return comment


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
				name = self._simple_get_request(i+"/getProperty?id=name")
				start = self._simple_get_request(i+"/getProperty?id=start")
				duration = self._simple_get_request(i+"/getProperty?id=duration")
				mw["nom"]=name
				mw["start"]=start
				mw["duration"]=duration
				l_mw.append(mw)
				mw={}
		except:
			pass
		
	return l_mw

    def is_inMaintenanceWindow(self, device_uid):
#	mw = get_deviceMaintWindows(device_uid)
 #       for w in mw:
  #              sta_time=datetime.fromtimestamp(float(w["start"]))
   #             end_time=sta_time+timedelta(minutes=float(w["duration"]))
    #            if datetime.now() < end_time and datetime.now() > sta_time: # Miram si estam en hora...
#			return "True"
#	return "False"	
	status=self._simple_get_request(device_uid+"/getProductionStateString")
	if status=="Maintenance":
		return "True"
	else:
		return "False"

    def add_device(self, deviceName, deviceClass):
        data = dict(deviceName=deviceName, deviceClass=deviceClass)
        return self._router_request('DeviceRouter', 'addDevice', [data])

    def create_event_on_device(self, device, severity, summary):
        if severity not in ('Critical', 'Error', 'Warning', 'Info', 'Debug', 'Clear'):
            raise Exception('Severity "' + severity +'" is not valid.')

        data = dict(device=device, summary=summary, severity=severity,
                    component='', evclasskey='', evclass='')
        return self._router_request('EventsRouter', 'add_event', [data])




