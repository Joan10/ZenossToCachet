#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import requests
import unittest
import random
import os
import sys
import time 
from datetime import datetime, timedelta
from os import listdir
from os.path import isfile, join
from subprocess import Popen, PIPE



STR_MAINT="--Servei en manteniment--"
MAIN_PATH="/home/stashboard/develop/"

class CachetResponseError(Exception):
	def __init__(self, status, message):
		self.status = status
		self.message = message

	def __str__(self):
		return "CachetHQ Error. Code " + repr(self.status) + ". Message: " + str(self.message)

class api_stashboard_panell:

	VER=False
	base_url=""
	headers = {'content-type': 'application/json', 'X-Cachet-Token':'TGUTJqjJ6GXlTndt27hP'}

	
	user="joan.arbona@uib.es"
	pas=""

	schedule_list=[]

	def __init__(self, url, token, pas):
		self.base_url = url
		self.headers = {'content-type': 'application/json', 'X-Cachet-Token' :token}
		self.pas=pas
		self.schedule_list=self.treuLlistaSchedule0()
		

	def preprocess(self, nomservei):
		ret=nomservei	
#		ret = ret.lower()
		return ret


	###################################
	#
	# FUNCIONS DE COMPONENTS 
	#
	###################################
	def treuComponentIdFromName(self, nom_component, grup=False):
		# Se li passa el nom d'un component i retorna l'id d'aquest servei.
		if grup == False :
	                append_url="/api/v1/components"
		elif grup == True :
	                append_url="/api/v1/components/groups"

                r = requests.get(self.base_url+append_url, headers=self.headers, verify=self.VER)
                if r.status_code != 200:
                        raise CachetResponseError(r.status_code, json.loads(r.text)['errors'][0]['detail'])

		try:
			while r != None:
			# Iteram per tots els components fins trobar el que conicideix el nom amb el passat per 
			# paràmetre
				for comp in json.loads(r.text)['data']:
					if nom_component == comp["name"]:
						return comp["id"] # Retornam l'id
				r_json=json.loads(r.text)
				r = requests.get(r_json['meta']['pagination']['links']['next_page'], headers=self.headers, verify=self.VER)
		                if r.status_code != 200:
                		        raise CachetResponseError(r.status_code, json.loads(r.text)['errors'][0]['detail'])

				# Seguim iterant si no l'hem trobat
		except requests.exceptions.MissingSchema as e:
			return "null" # Retornam null si no existeix.

		return "null"		


	
	def componentEnManteniment0(self,cid):

		# Retorna True si el dispositiu esta en manteniment. Aixo es que tingui a la descripcio
		# l'item STR_MAINT(**Servei en manteniment**)
		# cid: Component ID a posar en manteniment.

                append_url="/api/v1/components/"+str(cid)
                r = requests.get(self.base_url+append_url, headers=self.headers, verify=self.VER)
		desc=json.loads(r.text)['data']['description']
		if desc.find(STR_MAINT) == 0: #Si l'string esta al principi...
			return "True"	
		else:
			return "False"




	def posaComponentEnManteniment(self,cid):

		# Posa el component en Manteniment.
		# Bàsicament, modifica el camp description i hi posa davant l'string STR_MAINT
		# cid: ID del component a posar en manteniment.

                #append_url="/api/v1/components/"+str(cid) # Primer cal treure la descripcio i l'status.
		#r1 = requests.get(self.base_url+append_url, headers=self.headers, verify=self.VER)
                #data = json.dumps({"id":cid, "status": json.loads(r1.text)['data']['status'],"description": STR_MAINT+" "+ json.loads(r1.text)['data']['description']})
                #append_url="/api/v1/components/"+str(cid)
                #r2 = requests.put(self.base_url+append_url, data=data, headers=self.headers, verify=self.VER)

		# Posa component amb id passat a l'estat de MANTENIMENT
                data = json.dumps({"id":cid, "status":3})
                append_url="/api/v1/components/"+str(cid)
                r = requests.put(self.base_url+append_url, data=data, headers=self.headers, verify=self.VER)
                if r.status_code == 200:
                        return
                else:
                        raise CachetResponseError(r.status_code, json.loads(r.text)['errors'][0]['detail'])
	

	def llevaComponentDeManteniment(self,cid):

		# Lleva el component de Manteniment.
		# Bàsicament, lleva del camp description una quantitat de caràcters igual als de STR_MAINT. NO comprova abans
		# si està en manteniment.
		# cid: ID del component a posar en manteniment.

                append_url="/api/v1/components/"+str(cid)
		r1 = requests.get(self.base_url+append_url, headers=self.headers, verify=self.VER)
                if r1.status_code == 200:
                        return
                else:   
                        raise CachetResponseError(r1.status_code, json.loads(r1.text)['errors'][0]['detail'])


		try:
			text=json.loads(r1.text)['data']['description'][len(STR_MAINT)+1:]
			# Si hi ha algun problema simplement retorna.
		except:
			print "Wrong component description"	
			return
		
                data = json.dumps({"id":cid,"status": json.loads(r1.text)['data']['status'] , "description":text})
                append_url="/api/v1/components/"+str(cid)
                r2 = requests.put(self.base_url+append_url, data=data, headers=self.headers, verify=self.VER)
                if r2.status_code == 200:
                        return
                else:   
                        raise CachetResponseError(r2.status_code, json.loads(r2.text)['errors'][0]['detail'])

	def TombaComponent(self, id):
		# Posa component amb id passat a l'estat de DOWN
                data = json.dumps({"id":id, "status":4})
                append_url="/api/v1/components/"+str(id)
                r = requests.put(self.base_url+append_url, data=data, headers=self.headers, verify=self.VER)
                if r.status_code == 200:
                        return
                else:   
                        raise CachetResponseError(r.status_code, json.loads(r.text)['errors'][0]['detail'])


	def AixecaComponent(self, id):
		# Posa component amb id passat a l'estat de UP
                data = json.dumps({"id":id, "status":1})
                append_url="/api/v1/components/"+str(id)
                r = requests.put(self.base_url+append_url, data=data, headers=self.headers, verify=self.VER)
                if r.status_code == 200:
                        return 
                else:  
                        raise CachetResponseError(r.status_code, json.loads(r.text)['errors'][0]['detail'])

        def ReportaComponent(self, id, outage=False):
               # Posa component amb id passat a l'estat de problemes
                # Si outage = false, reportam problema de rendiment. Sino, problema de funcionament parcial
                if outage == True:
                    data = json.dumps({"id":id, "status":3})
                else:
                    data = json.dumps({"id":id, "status":2})
                append_url="/api/v1/components/"+str(id)
                r = requests.put(self.base_url+append_url, data=data, headers=self.headers, verify=self.VER)
                if r.status_code == 200:
                        return
                else:
                        raise CachetResponseError(r.status_code, json.loads(r.text)['errors'][0]['detail'])


 
	def getNomComponent(self,id):
                append_url="/api/v1/components/"+str(id)
                r = requests.get(self.base_url+append_url,  headers=self.headers, verify=self.VER)
		if r.status_code == 200:
			return json.loads(r.text)['data']['name']
		else:
			raise CachetResponseError(r.status_code, json.loads(r.text)['errors'][0]['detail'])

	def getNomComponentTest(self,id):
                append_url="/api/v1/components/"+str(id)
                r = requests.get(self.base_url+append_url,  headers=self.headers, verify=self.VER)
		return r

	def setNomComponent(self,id,nom):
        # Set nom dispositiu
                data = json.dumps({"id":id, "name":nom, "status":self.getStatusFromId(id)})
                append_url="/api/v1/components/"+str(id)
                r = requests.put(self.base_url+append_url, data=data, headers=self.headers, verify=self.VER)
                if r.status_code == 200:
                        return
                else:  
                        raise CachetResponseError(r.status_code, json.loads(r.text)['errors'][0]['detail'])


	def getDescComponent(self,id):
                append_url="/api/v1/components/"+str(id)
                r = requests.get(self.base_url+append_url,  headers=self.headers, verify=self.VER)
                if r.status_code == 200:
                        return json.loads(r.text)['data']['description']
                else:  
                        raise CachetResponseError(r.status_code, json.loads(r.text)['errors'][0]['detail'])

		
	def setDescComponent(self,id,desc):
                data = json.dumps({"id":id, "description":desc, "status":self.getStatusFromId(id)})
                append_url="/api/v1/components/"+str(id)
                r = requests.put(self.base_url+append_url, data=data, headers=self.headers, verify=self.VER)
		if r.status_code == 200:
                        return 
                else:  
                        raise CachetResponseError(r.status_code, json.loads(r.text)['errors'][0]['detail'])


	###################################
	#
	# FUNCIONS DE INCIDENTS
	#
	###################################
	def treuIncidentIdFromNameAndMsg(self, cid, msg):
		#
		# Treu l'identificador de l'incident que correspon al component passat mitjançant ID i 
		# que coincideix amb el missatge passat.
		# cid: Component ID al qual pertany l'incident
		# msg: El cos del missatge de l'incident ha de coincidir
		#
	        append_url="/api/v1/incidents"

                r = requests.get(self.base_url+append_url, headers=self.headers, verify=self.VER)
                if r.status_code != 200:
	                raise CachetResponseError(r.status_code, json.loads(r.text)['errors'][0]['detail'])
		try:
			while r != None:
                        # Iteram per tots els incidents fins trobar el que conicideix el nom i cid amb el passat per 
                        # paràmetre

				for inc in json.loads(r.text)['data']:
					if cid == inc["component_id"] and msg == inc["message"]:
						return inc["id"]
				r = requests.get(json.loads(r.text)['meta']['pagination']['links']['next_page'], headers=self.headers, verify=self.VER)
                                if r.status_code != 200:
                                        raise CachetResponseError(r.status_code, json.loads(r.text)['errors'][0]['detail'])

		except requests.exceptions.MissingSchema as e:
			return "null"		
		return "null"		


        def getIncidentStatus(self, id):

                # Retorna l'status de l'incident

                append_url="/api/v1/incidents/"+str(id)
		r = requests.get(self.base_url+append_url, headers=self.headers, verify=self.VER)
                if r.status_code == 200:
			return json.loads(r.text)['data']['status']
                else:
                        raise CachetResponseError(r.status_code, json.loads(r.text)['errors'][0]['detail'])


	def ReportaIncident(self, nom, id, missatge):

		# Crea incident amb el missatge passat i de nom "nom" i s'assigna al component amb id "id".
		# El crea amb estatus=1, és a dir, obert
		# nom: nom de l'incident.
		# id: id del component relacionat amb l'incident
		# missatge: missatge que donam a l'incident.

                data = json.dumps({"name":nom,"message":missatge,"status":1,"component_id":id})
                append_url="/api/v1/incidents"
                r = requests.post(self.base_url+append_url, data=data, headers=self.headers, verify=self.VER)
                if r.status_code == 200 or r.status_code == 400: #Error estrany
			return 
                else:
                        raise CachetResponseError(r.status_code, json.loads(r.text)['errors'][0]['detail'])

	def ArreglaIncident(self, nom, missatge, id="null"):
		
		# Crea incident amb el missatge passat i de nom "nom" i s'assigna al component amb id "id".
		# El crea amb status=4, fixed.
		# nom: nom de l'incident.
		# id: id del component relacionat amb l'incident
		# missatge: missatge que donam a l'incident.
		if id != "null":
	                data = json.dumps({"name":nom,"message":missatge,"status":4,"component_id":id})
		else:
			data = json.dumps({"name":nom,"message":missatge,"status":4})
                append_url="/api/v1/incidents"
                r = requests.post(self.base_url+append_url, data=data, headers=self.headers, verify=self.VER)
                if r.status_code == 200 or r.status_code == 400: #Error estrany
                        return 
                else:  
                        raise CachetResponseError(r.status_code, json.loads(r.text)['errors'][0]['detail'])


	def ReportaIncidentManteniment(self, nom, id, missatge):
	#
	# Crea un incident de manteniment pel dispositiu passat.
	# nom: nom del dispositiu
	# missatge: descripcio
	#
                data = json.dumps({"name":nom,"message":missatge,"status":0,"component_id":id})
                append_url="/api/v1/incidents"
                r = requests.post(self.base_url+append_url, data=data, headers=self.headers, verify=self.VER)
                if r.status_code == 200:
                        return 
                else:  
                        raise CachetResponseError(r.status_code, json.loads(r.text)['errors'][0]['detail'])

	def ReportaSchedule(self, nom, missatge, date):
	#
	# Totalment diferent. En aquest cas feim una crida al sistema per executar un script que prepara un webinject. Per tant, l'afegito
	# de l'schedule es fa per HTTP, no per l'API de REST, ja que aquesta encara no està disponible.
	# nom: nom del dispositiu
	# missatge: descripció
	# date: data d'inici del manteniment. Format DD/MM/YYYY HH:MM
	#
        	reload(sys)
	        sys.setdefaultencoding("utf-8") # FUCK YOU python
		comanda="/bin/bash "+MAIN_PATH+"API/webinject/webinject0.sh "+self.base_url+" \""+nom+"\" \""+missatge+"\" \""+date+"\"  \""+self.pas+"\""
		time.sleep(1) # Si no posam l'sleep s'estressa i fica dos pics la mateixa entrada....?
		return Popen(comanda, stdout=PIPE, shell=True)

	def treuIdFromSchedule(self, nom, sch_at):
	# Treu l'schedule de api/v1/incidents/id filtrant els incidents amb human_status Scheduled i status 0
        # nom: nom del dispositiu
	# sch_at: data de la forma YYYY-MM-DD HH:MM:SS
	# end_time: datetime

                append_url="/api/v1/incidents"
                r = requests.get(self.base_url+append_url, headers=self.headers, verify=self.VER)
		if r.status_code != 200:
                	raise CachetResponseError(r.status_code, json.loads(r.text)['errors'][0]['detail'])
                try:
                        while r != None:
                        # Iteram per tots els incidents fins trobar el que conicideix el nom amb el passat per 
                        # paràmetre i es un schedule
                                for inc in json.loads(r.text)['data']:
                                        if nom == inc["name"] and inc["human_status"] == "Scheduled" and inc["status"] == 0 and inc["scheduled_at"] == sch_at:
                                                return inc["id"]
                                r = requests.get(json.loads(r.text)['meta']['pagination']['links']['next_page'], headers=self.headers, verify=self.VER)
				if r.status_code != 200:
                                        raise CachetResponseError(r.status_code, json.loads(r.text)['errors'][0]['detail'])
                except requests.exceptions.MissingSchema as e:
                        return "null"
                return "null"

#        def treuIdFromSchedule0(self, nom, sch_at):
#        # Treu l'schedule de api/v1/incidents/id filtrant els incidents amb human_status Scheduled i status 0
#	 # Ho consulta a la llista d'incidents per fer més via
#        # nom: nom del dispositiu
#        # sch_at: data de la forma YYYY-MM-DD HH:MM:SS
#        # end_time: datetime

#                for inc in self.schedule_list:
#                        if inc["missatge"].find(nomcomp) > -1 and inc["start"].strftime("%Y-%m-%d %H:%M:%S") == sch_at :
#				return inc["id"]
#                return "null"



	def treuEndTime(self, msg):
		str1=msg[msg.find("fins el dia")+len("fins el dia "):]
                data=str1[:str1.find(" a les ")]
                hora=str1[str1.find(" a les ")+len(" a les "):-1]
		return datetime.strptime(data+" "+hora, '%d-%m-%Y %H:%M')
		

	def treuLlistaSchedule(self,nomcomp = "null"):
        # Treu la llista de Schedules de la llista creada a l'inici. Això ho feim perquè l'script sigui més ràpid. 
	# Si se li passa un nom, ho filtra per dispositiu.
        # nomcomponent: nom del COMPONENT (no del dispositiu den Zenoss) el que apareix a la descripció.

		if nomcomp == "null":
			return self.schedule_list
		llista_ls = []	
		for inc in self.schedule_list:
			if inc["missatge"].find(nomcomp) > -1:
				llista_ls.append(inc)
		return llista_ls	


	def treuLlistaSchedule0(self, nomcomp = "null"):
	# Treu la llista de Schedules. Més lent q l'anterior perquè va a cercar la llista al servidor. 
	# Si se li passa un nom, ho filtra per dispositiu.
	# nomcomponent: nom del COMPONENT (no del dispositiu den Zenoss) el que apareix a la descripció.
	# 
                append_url="/api/v1/incidents"

		ls = {}
		llista_ls = []
                r = requests.get(self.base_url+append_url, headers=self.headers, verify=self.VER)
                if r.status_code != 200:
                        raise CachetResponseError(r.status_code, json.loads(r.text)['errors'][0]['detail'])

                try:   
                        while r != None:
                        # Iteram per tots els incidents fins trobar el que conicideix el nom amb el passat per 
                        # paràmetre i es un schedule
                                for inc in json.loads(r.text)['data']:
					# Treim l'endtime de la descripció de l'incident
					try:
						dt_schat = datetime.strptime(inc["scheduled_at"],"%Y-%m-%d %H:%M:%S")
						dt_endtime=self.treuEndTime(inc["message"])
						if nomcomp == "null":
		                                        if inc["human_status"] == "Scheduled" and inc["status"] == 0 and datetime.now() < dt_endtime:
								ls["nom"] = inc["name"]
								ls["missatge"] = inc["message"]
								ls["start"] = dt_schat 
								ls["end"] = dt_endtime
								ls["id"] = inc["id"]
								llista_ls.append(ls)
								ls = {}
						else:
			                                if inc["message"].find(nomcomp) > -1 and inc["human_status"] == "Scheduled" and inc["status"] == 0 and datetime.now() < dt_endtime:
								ls["nom"] = inc["name"]
								ls["missatge"] = inc["message"]
								ls["start"] = dt_schat 
								ls["end"] = dt_endtime
								ls["id"] = inc["id"]
								llista_ls.append(ls)
								ls = {}	
					except:
						pass
                                                
                                r = requests.get(json.loads(r.text)['meta']['pagination']['links']['next_page'], headers=self.headers, verify=self.VER)
				if r.status_code != 200:
                                        raise CachetResponseError(r.status_code, json.loads(r.text)['errors'][0]['detail'])

		except requests.exceptions.MissingSchema as e:
			pass
			
		return llista_ls

 	def eliminaIncident(self, id):
	#Retorna l'estat del servei: up o down.
		append_url="/api/v1/incidents/"+str(id)
		r = requests.delete(self.base_url+append_url,  headers=self.headers, verify=self.VER)
                if r.status_code != 204:
	                raise CachetResponseError(r.status_code, json.loads(r.text)['errors'][0]['detail'])


        def actualitzaComponentIncident(self,id_in,id_co):

		# Actualitza el component a que fa referència l'Incident.
		# id_in: id de l'incident
		# id_co: id del component


                data = json.dumps({"id":id_in, "status":self.getIncidentStatus(id_in), "component_id":id_co})
                append_url="/api/v1/incidents/"+str(id)
                r = requests.put(self.base_url+append_url, data=data, headers=self.headers, verify=self.VER)
		if r.status_code != 200:
                	raise CachetResponseError(r.status_code, json.loads(r.text)['errors'][0]['detail'])
                # Modificam el component



	###################################
	#
	# FUNCIONS DE SERVEIS I DISPOSITIUS
	#
	###################################

	def ActualitzaEstatDispositiu(self,nom,missatge,estat):

		# Actualitza l'estat del component de nom "nom" amb l'estat "estat". Aixeca també un
		# incident amb missatge "missatge".
		# nom: nom del component
		# missatge: missatge de l'incident
		# estat: estat al qual passarà el component i amb el qual es crearà l'incident.
		# Pot ser "down", "up" o "perf" per problemes de performance.
		nomservei=self.preprocess(nom)
                id=self.treuComponentIdFromName(nom)
		if estat=="down":
			incident_status=1
			component_status=4
		elif estat == "up":
			incident_status=4
			component_status=1
		elif estat == "perf":
		#perf issues
			incident_status=1
			component_status=2
		else:
			return -1

                data = json.dumps({"name":nomservei,"message":missatge,"status":incident_status,"component_id":id})
                append_url="/api/v1/incidents" 
                r = requests.post(self.base_url+append_url, data=data, headers=self.headers, verify=self.VER)
		if r.status_code != 200:
                	raise CachetResponseError(r.status_code, json.loads(r.text)['errors'][0]['detail'])
		# Cream l'incident
   		
	        data = json.dumps({"id":id, "status":component_status})
        	append_url="/api/v1/components/"+str(id)
                r = requests.put(self.base_url+append_url, data=data, headers=self.headers, verify=self.VER)
                if r.status_code != 200:
                        raise CachetResponseError(r.status_code, json.loads(r.text)['errors'][0]['detail'])

		# Modificam el component


	def TombaServei(self, nom, missatge):
		# Wrapper d'ActualitzaEstatDispositiu
		self.ActualitzaEstatDispositiu(nom,missatge,"down")

	def AixecaServei(self, nom, missatge):
		# Wrapper d'ActualitzaEstatDispositiu
		self.ActualitzaEstatDispositiu(nom,missatge,"up")

	def ReportaServei(self, nom, missatge):
		# Wrapper d'ActualitzaEstatDispositiu
		self.ActualitzaEstatDispositiu(nom,missatge,"perf")


	def CreaServei(self, nom, descripcio):
	#Crea el servei o l'actualitza si ja existeix		
	# Retorna Id del component
		nomservei = self.preprocess(nom)
		idservei=self.treuComponentIdFromName(nomservei)
		if idservei != "null" :
		# Si ja existeix el servei actualitzam i tornam
			return idservei

		else:
		# Si no existeix el servei el cream
			data = json.dumps({"name":nomservei,"description":descripcio,"status":1})
	                append_url="/api/v1/components"
        	        r = requests.post(self.base_url+append_url, data=data,  headers=self.headers, verify=self.VER)
			if r.status_code == 200:
	                        return json.loads(r.text)["data"]["id"]

			else:
                        	raise CachetResponseError(r.status_code, json.loads(r.text)['errors'][0]['detail'])



	def getEstat(self, nom):
	#Retorna l'estat del servei: up o down.
		nomservei = self.preprocess(nom)
		id = self.treuComponentIdFromName(nomservei)
		if id == "null":
			return "null"
		append_url="/api/v1/components/"+str(id)
		r = requests.get(self.base_url+append_url,  headers=self.headers, verify=self.VER)
		if r.status_code != 200:
			raise CachetResponseError(r.status_code, json.loads(r.text)['errors'][0]['detail'])

		if json.loads(r.text)['data']['status'] == 1:
			return "up"
		elif  json.loads(r.text)['data']['status'] == 2:
			return "perf"
		else:
			return "down"
		

	def getEstatId(self, id):
	#Retorna l'estat del servei: up o down.
		append_url="/api/v1/components/"+str(id)
		r = requests.get(self.base_url+append_url,  headers=self.headers, verify=self.VER)
                if r.status_code != 200:
                        raise CachetResponseError(r.status_code, json.loads(r.text)['errors'][0]['detail'])

		if json.loads(r.text)['data']['status'] == 1:
			return "up"
		elif  json.loads(r.text)['data']['status'] == 2:
			return "perf"
		elif json.loads(r.text)['data']['status'] == 3:
			return "inte"
		else:
			return "down"

	def getStatusFromId(self, id):
	#Retorna l'estat del servei: up o down.
		append_url="/api/v1/components/"+str(id)
		r = requests.get(self.base_url+append_url,  headers=self.headers, verify=self.VER)
		if r.status_code == 200:
			return json.loads(r.text)['data']['status']
                else:
			raise CachetResponseError(r.status_code, json.loads(r.text)['errors'][0]['detail'])

	def eliminaServei(self, id):
	#Retorna l'estat del servei: up o down.
		append_url="/api/v1/components/"+str(id)
		r = requests.delete(self.base_url+append_url,  headers=self.headers, verify=self.VER)
                if r.status_code != 204:
                        raise CachetResponseError(r.status_code, json.loads(r.text)['errors'][0]['detail'])




	###################################
	#
	# FUNCIONS DE GRUPS DE COMPONENTS 
	#
	###################################

	def ActualitzaGrup(self, nom, grup):
	# Actualtiza el grup dun servei. Si grup=="null" el borra.
		if grup == "":
			return "null"

                nomservei = self.preprocess(nom)
                idservei=self.treuComponentIdFromName(nomservei)
                if idservei == "null" :
			raise Exception("El servei no existeix")
			return "null"
		else:
			if grup != "null" :
				self.setGrup(idservei,grup)
			else:
                                self.delGrup(idservei)
			return idservei


	def CreaGrup(self, grup):
	# Crea el grup. Si ja existeix retorna el seu ID
		gr_id=self.treuComponentIdFromName(grup, grup=True);
                if gr_id  == "null" :
                        # Si el grup no existeix
                        data = json.dumps({"name":grup, "collapsed":"1"})
                        append_url="/api/v1/components/groups"
                        r  = requests.post(self.base_url+append_url, data=data,  headers=self.headers, verify=self.VER)
                        gr_id=json.loads(r.text)["data"]["id"]
		return gr_id
			
	def setGrup(self, id, grup):
	# Set grup dispositiu
		gr_id = self.CreaGrup(grup)
                data = json.dumps({"id":id, "group_id":gr_id, "status":self.getStatusFromId(id)})
                append_url="/api/v1/components/"+str(id)
	        r = requests.put(self.base_url+append_url, data=data, headers=self.headers, verify=self.VER)		
			
	def delGrup(self, id):
	# Elimina el grup del component
                data = json.dumps({"id":id, "group_id":0, "status":self.getStatusFromId(id)})
                append_url="/api/v1/components/"+str(id)
	        r = requests.put(self.base_url+append_url, data=data, headers=self.headers, verify=self.VER)		


	def getGrup(self, id):
	# Get grup dispositiu
                append_url="/api/v1/components/"+str(id)
                r = requests.get(self.base_url+append_url,  headers=self.headers, verify=self.VER)
                gr_id=json.loads(r.text)['data']['group_id']
                append_url="/api/v1/components/groups/"+str(gr_id)
		try:
			r = requests.get(self.base_url+append_url,  headers=self.headers, verify=self.VER)
			return json.loads(r.text)['data']['name']
		except:
			print "Component "+str(id)+" no te grup"
			return "null";

	def eliminaGrups(self, id):
	#Retorna l'estat del servei: up o down.
		append_url="/api/v1/components/groups/"+str(id)
		r = requests.delete(self.base_url+append_url,  headers=self.headers, verify=self.VER)

