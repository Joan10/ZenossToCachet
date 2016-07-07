#!/usr/bin/env python
# -*- coding: utf-8 -*-
# master
#
# Autor: Joan Arbona
# Script que actualitza la web de panell-estats, d'informació sobre l'estat de la infraestructura del CTI
# Es tracta d'una web que fa servir el gestor de continguts CACHET amb la qual s'hi interactua amb JSON
#

import sys
from datetime import datetime, date, time, timedelta



sys.path.append("/home/stashboard/master/ZenossToCachet/API")
sys.path.append("/home/stashboard/secrets/")

from secrets import prod_public_hq_token,prod_private_hq_token,deve_public_hq_token,deve_private_hq_token,web_password

import treu_events_grup_xml
import api_stashboard_panell_v2 #Stashboard extens
import xml.etree.ElementTree as ET
import ZenossAPI


MIN_SEVERITY = 5

xml_string = treu_events_grup_xml.treu_events_grup_xml('/zport/dmd/Groups/serveis/serveis_critics')

root = ET.fromstring(xml_string)

# SERVIDORS PROVA
#st = api_stashboard_panell_v2.api_stashboard_panell("http://10.80.87.76","TGUTJqjJ6GXlTndt27hP");
#st2 = api_stashboard_panell_v2.api_stashboard_panell("http://10.80.87.76:9080","2I8GMpbCfL1lyqqK2Rlo");

# SERVIDORS PRODUCCIO
st = api_stashboard_panell_v2.api_stashboard_panell("http://panell-estats-cti.sint.uib.es:8080",prod_private_hq_token,web_password);
st2 = api_stashboard_panell_v2.api_stashboard_panell("http://panell-estats.sint.uib.es:8080",prod_public_hq_token,web_password);

zp=ZenossAPI.ZenossAPI()

#DUMPING ET:
#ET.dump(TREE)

#
# Funció que sincronitza els schedules del CachetHQ amb els Maintenance Window.
# Primer els mira tots, i, si no existeixen ja, i no han caducat, els afegeix. 
# De comentari afegeix el nom del dispositiu, la data d'inici de l'aturada i la data de final.
# 


def actualitza_schedule(st, nomservei, mw):
	reload(sys) # fuck you python
	sys.setdefaultencoding("utf-8")

	for w in mw:
		sta_time=datetime.fromtimestamp(float(w["start"]))
		end_time=sta_time+timedelta(minutes=float(w["duration"]))
		
		if st.treuIdFromSchedule(w["nom"],end_time.strftime("%Y-%m-%d %H:%M:%S")) == "null":
			if datetime.now() < end_time: # Només cream l'schedule si el maint window segueix vigent.
				msg="El servei "+nomservei+" estarà aturat per tasques de manteniment des del dia "+sta_time.strftime("%d-%m-%Y")+" a les "+sta_time.strftime("%H:%M")+" fins el dia "+end_time.strftime("%d-%m-%Y")+" a les "+ end_time.strftime("%H:%M")+"."

				st.ReportaSchedule(w["nom"],msg,end_time.strftime("%d/%m/%Y %H:%M"))

def actualitza(st, id, nom, znom, perfok, aixeca):
# 
# Funció que actualitza l'estat dels components i incidents del Cachet en funció de tres flags: perfok, aixeca i maint
# Té en compte els casos en què:
# 1. Hi ha problemes de rendiment. aixeca = 1, perfok = 0
# 2. El servei torna a funcionar correctament. aixeca = 1, perfok = 1
# 3. El servei NO funciona. Aixeca = 0, perfok=X
# SI el component està en manteniment, el posam en l'estat que toca i no hi feim canvis.
#	
	maint = zp.is_inMaintenanceWindow(zp.get_UID(znom))
	if maint == "True":
		if st.getEstatId(id) != "maint":
			st.posaComponentEnManteniment(id)
	else:
		if aixeca == 1:
        		if perfok == 0:
                		if st.getEstatId(id) != "perf":
					# Cas en que hi ha problemes de rendiment
					st.ReportaComponent(id)
					st.ReportaIncident(nom,id,"El servei està experimentant problemes de rendiment.")
        	        else:
                	        if st.getEstatId(id) != "up":
					# Cas en que el servei torna a funcionar
					st.AixecaComponent(id)
					st.ArreglaIncident(nom,id,"El servei funciona correctament.")
        	else:
               		if st.getEstatId(id) != "down":
			# Cas en que el servei deixa de funcionar
				st.TombaComponent(id)
				st.ReportaIncident(nom,id,"Sembla que el servei està experimentant alguns problemes. Estam treballant perquè torni a estar operatiu el més aviat possible.")

for disp in root.findall('dispositiu'):

	aixeca = 1 # Variable per saber si hem d'aixecar o no el servei en qüestoó
	perfok = 1 # Variable per saber si el servei té un rendiment correcte
	scheduled_at = ""
	if disp.text != "udp.sint.uib.es":
		try:
			# Parsejam el nom del dispositiu. Aquest anirà contingut dins el camp Comments del Zenoss de la forma següent:
			# cachet=<nom>;
			# Si no el troba posarà el nom del Device del Zenoss
			comentari=zp.get_devicecomment(zp.get_UID(disp.text))
			offset0=comentari.find("cachet=");
			offset1=comentari.find(";");
			if offset0 > -1 and offset1 > -1:
				nom=comentari[offset0+7:offset1]
			else:
				raise Exception("Comentari al Zenoss mal format. El nom va contingut dins cachet=<nom>;")
			
                        offset2=comentari.find("public=");
                        offset3=comentari.find(";",offset2+1)
                        if offset2 > -1 and offset3 > -1:
                                nompublic=comentari[offset2+7:offset3]
                        else:
                                nompublic="null"

		except:
                        nompublic="null"
			nom=disp.text
		# No actualitzam el grup, finalment ho feim manualment.
		id=st.CreaServei(nom, "Dispositiu "+disp.text)
                if nompublic != "null":
                        id2=st2.CreaServei(nompublic, "")

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
						#	print disp.text+" tomba"
							aixeca = 0
						##########################################################
						#Si l'event no és crític, però té problemes de rendiment, ho reflexam a la pàgina.
						##########################################################
						elif message.text.find("threshold of") > -1 and int(count.text) > 2:
							perfok = 0	

						##########################################################
						#Si hi ha un scheduling programat ho reflectim també independentment 
						#de la resta. Si falla, simplement passam.
						##########################################################
						#if  int(severity.text) == 2 and component.text != "" and eventClassKey.text != "":
						#	data_sch = component.text;
						#	t_data_sch=datetime.strptime(data_sch, "%Y-%m-%d %H:%M")
						#	if eventClassKey.text == "manteniment":
						#		maint=1
						#		maintmsg=message.text
						#		scheduled_at=t_data_sch.strftime("%d/%m/%Y %H:%M")
									
							
				except Exception as e:
	#				print "Ooops. Error en un event de "+nom
	#				print("Exception:", sys.exc_info()[0])
	#				print("Error:", e)
					pass
					

		##########################################################
		# Miram si el dispositiu ja no té events, però també cal mirar 
		#la severitat d'aquests events! Si no cumpleix el mínim de severitat
		# per tal de ser tombat l'aixecam.
		##########################################################

		##########################################################
		# Sincronitzam els Maintenance Windows
                #########################################################
		mw=zp.get_deviceMaintWindows(zp.get_UID(disp.text))

		actualitza_schedule(st,nom,mw)
		actualitza(st,id,nom,disp.text,perfok,aixeca)
		if nompublic != "null":
			actualitza_schedule(st2,nompublic,mw)
			actualitza(st2,id2,nompublic,disp.text,perfok,aixeca)
