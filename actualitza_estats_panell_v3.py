#!/usr/bin/env python
# -*- coding: utf-8 -*-
# MAL MAL
#
# Autor: Joan Arbona
# Script que actualitza la web de panell-estats, d'informació sobre l'estat de la infraestructura del CTI
# Es tracta d'una web que fa servir el gestor de continguts CACHET amb la qual s'hi interactua amb JSON
#


import sys, traceback
from datetime import datetime, date, time, timedelta

# ARGUMENT VALIDATION
if len(sys.argv) != 2:
	raise ValueError("Argument -d (debug) o -p (produccio) requerit")

if sys.argv[1] == "-d":
	PROD=False
elif sys.argv[1] == "-p":
	PROD=True
else:
        raise ValueError("Argument -d (debug) o -p (produccio) requerit")

# PATH load
if PROD == True:
	sys.path.append("/home/stashboard/panell_serveis_critics_prod/ZenossToCachet/API/")
else:
	print "---EN MODE DEVELOP---"
	sys.path.append("/home/stashboard/panell_serveis_critics_dev/ZenossToCachet/API/")


sys.path.append("/home/stashboard/secrets/")
from secrets import prod_public_hq_token,prod_private_hq_token,deve_public_hq_token,deve_private_hq_token,web_password
import treu_events_grup_xml
import api_stashboard_panell_v2 #Stashboard extens
import xml.etree.ElementTree as ET
import ZenossAPI


MIN_SEVERITY = 5

xml_string = treu_events_grup_xml.treu_events_grup_xml('/zport/dmd/Groups/serveis/serveis_critics')

root = ET.fromstring(xml_string)

if PROD == True:
# Servidors en producció
	st = api_stashboard_panell_v2.api_stashboard_panell("http://panell-estats-cti.sint.uib.es:8080",prod_private_hq_token,web_password)
	st2 = api_stashboard_panell_v2.api_stashboard_panell("http://panell-estats.sint.uib.es:8080",prod_public_hq_token,web_password)
else:
# Servidors de prova
	print "PROD fals, empram servidors de prova"
	st = api_stashboard_panell_v2.api_stashboard_panell("http://10.80.87.76",deve_public_hq_token,web_password);
	st2 = api_stashboard_panell_v2.api_stashboard_panell("http://10.80.87.76:9080",deve_private_hq_token,web_password);

zp=ZenossAPI.ZenossAPI()



#DUMPING ET:
#ET.dump(root)


def actualitza_component(st, id, nom, znom, estat):
# 
# Funció que actualitza l'estat dels components i incidents del Cachet en funció de tres flags: perfok, aixeca i maint
# Té en compte els casos en què:
# 1. Hi ha problemes de rendiment. estat="problemes_rendiment" ; aixeca = 1, perfok = 0
# 2. Interrupció parcial. estat="interrupcio_parcial"
# 3. El servei torna a funcionar correctament. estat="aixeca" aixeca = 1, perfok = 1
# 4. El servei NO funciona. estat="no_funciona" Aixeca = 0, perfok=X
	if estat == "problemes_rendiment":
		if st.getEstatId(id) != "perf":
			ReportaComponent(id, outage=False)
                        st.ReportaIncident(nom,id,"El servei està experimentant problemes de rendiment.")

	if estat == "interrupcio_parcial":
		if st.getEstatId(id) != "inte":
			st.ReportaComponent(id, outage=True)
			st.ReportaIncident(nom,id,"El servei està experimentant algunes interrupcions ")
			
	if estat == "aixeca":
		if st.getEstatId(id) != "up":
		# Cas en que el servei torna a funcionar
			if PROD == False: 
				print "AIXECA "+nom
			st.AixecaComponent(id)
			st.ArreglaIncident(nom,"El servei funciona correctament.",id)

	if estat == "no_funciona" :
       		if st.getEstatId(id) != "down":
		# Cas en que el servei deixa de funcionar
			if PROD == False: 
				print "TOMBA "+nom
			st.TombaComponent(id)
			st.ReportaIncident(nom,id,"Sembla que el servei està experimentant alguns problemes. Estam treballant perquè torni a estar operatiu el més aviat possible.")

for disp in root.findall('dispositiu'):

	estat="aixeca"
	scheduled_at = ""
	if (disp.text != "udp.sint.uib.ess" and PROD==False) or (disp.text != "udp.sint.uib.es" and PROD==True):
		try:
			# Parsejam el nom del dispositiu. Aquest anirà contingut dins el camp Comments del Zenoss de la forma següent:
			# cachet=<nom>;
			# Si no el troba posarà el nom del Device del Zenoss
			nom = zp.get_devicePrivateName(zp.get_UID(disp.text))
		except Exception as e:
			nom = disp.text
			# Parsejam el nom públic del dispositiu. 
			# Aquest anirà contingut dins el camp Comments del Zenoss de la forma següent:
			# public=<nom>;
			# Si no el troba posarà el nom "null"
		try:
			nompublic = zp.get_devicePublicName(zp.get_UID(disp.text))
		except:
			nompublic = "null"
		# No actualitzam el grup, finalment ho feim manualment.
		id=st.CreaServei(nom, "Dispositiu "+disp.text)
		
                if nompublic != "null":
                        id2=st2.CreaServei(nompublic, "")

		if PROD == False:
	                reload(sys)
        	        sys.setdefaultencoding("utf-8") # FUCK YOU python

			print "----"
			print "Zenoss: "+disp.text
			print "Cachet Public: "+nompublic
			print "Cachet Privat: "+nom
			print "Id public: "+str(id2)
			print "Id privat: "+str(id)
			print "Id grup: "+str(zp.get_group(disp.text))
			print "----"
		if len(disp) > 0:
			for event in disp.findall('event'):
				message = event.find('message')
				severity = event.find('severity')
				count = event.find('count')
				component = event.find('component').find('text')
				eventClassKey = event.find('eventClassKey')
				device_groups_str = ET.tostring(event)
				##########################################################
				#Cal mirar si el device de l'event es critic, 
				#ja que de vegades se'ns en colen: En fer
				#getEvent, apareixen events d'altres dispositius. 
				#Per exemple, en voler treure els events de rrhh apareixen també 
				#els events de rrhh.db.uib.es
				##########################################################
				try:
					if device_groups_str.find("serveis_critics") > -1:
						if int(severity.text) >= MIN_SEVERITY:
						##########################################################
						#Si l'event és de serveis crítics i la severitat de l'event és suficient tombam el servei
						#Sino, ignoram l'event.
						##########################################################
							estat="no_funciona"
						##########################################################
						#Si l'event no és crític, però té problemes de rendiment o l'event té de component "cachet", ho reflexam a la pàgina.
						##########################################################
						elif message.text.find("unreachable") > -1 and int(count.text) > 2 and estat != "no_funciona":
							estat="interrupcio_parcial"
						elif message.text.find("threshold of") > -1 and int(count.text) > 2 and estat != "interrupcio_parcial" and estat != "no_funciona":
							estat="problemes_rendiment"

							
				except Exception as e:
					if PROD == False:
						print "Ooops. Error en un event de "+nom
						print("Exception:", sys.exc_info()[0])
						print("Error:", e)
						traceback.print_exc(file=sys.stdout)
					pass
					

		##########################################################
		# Miram si el dispositiu ja no té events, però també cal mirar 
		#la severitat d'aquests events! Si no cumpleix el mínim de severitat
		# per tal de ser tombat l'aixecam.
		##########################################################
		##########################################################
		# Sincronitzam els Maintenance Windows
                #########################################################
		try:
			actualitza_component(st,id,nom,disp.text,estat)
		except api_stashboard_panell_v2.CachetResponseError as e:
			print "Error updating device "+disp.text+ " in private Cachet"
			print e
			traceback.print_exc(file=sys.stdout)
	
		try:	
			if nompublic != "null":
				actualitza_component(st2,id2,nompublic,disp.text,estat)
                except api_stashboard_panell_v2.CachetResponseError as e:
                        print "Error updating device "+disp.text+ " in public Cachet"
                        print e
			traceback.print_exc(file=sys.stdout)


