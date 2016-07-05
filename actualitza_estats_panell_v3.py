#!/usr/bin/env python
# -*- coding: utf-8 -*-
# MAL MAL
#
# Autor: Joan Arbona
# Script que actualitza la web de panell-estats, d'informació sobre l'estat de la infraestructura del CTI
# Es tracta d'una web que fa servir el gestor de continguts CACHET amb la qual s'hi interactua amb JSON
#

import sys
from datetime import datetime, date, time, timedelta



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

# SERVIDORS PROVA
st = api_stashboard_panell_v2.api_stashboard_panell("http://10.80.87.76",deve_public_hq_token,web_password);
st2 = api_stashboard_panell_v2.api_stashboard_panell("http://10.80.87.76:9080",deve_private_hq_token,web_password);

# SERVIDORS PRODUCCIO
#st = api_stashboard_panell_v2.api_stashboard_panell("http://panell-estats-cti.sint.uib.es:8080",deve_private_hq_token,web_password);# Exclusiu del CTI 
#st2 = api_stashboard_panell_v2.api_stashboard_panell("http://panell-estats.sint.uib.es:8080",deve_public_hq_token,web_password);# Public

zp=ZenossAPI.ZenossAPI()



#DUMPING ET:
#ET.dump(TREE)

#
# Funció que sincronitza els schedules del CachetHQ amb els Maintenance Window.
# Primer els mira tots, i, si no existeixen ja, i no han caducat, els afegeix. 
# De comentari afegeix el nom del dispositiu, la data d'inici de l'aturada i la data de final.
# 

STR_FORMAT="El servei %s estarà aturat per tasques de manteniment des del dia %s a les %s fins el dia %s a les %s."

def actualitza_schedule(st, nomservei, l_sch_zenoss, l_sch_cachet):
	reload(sys) # fuck you python
	sys.setdefaultencoding("utf-8")
	# Passam dues llistes d'schedules, la del cachet i la del zenoss, i les comparam.
	# Si a la llista de zenoss n'hi ha algun que no existeix al cachet, cream l'schedule al cachet
	# Si a la llista de cachet n'hi ha algun que no és al zenoss, borram la del cachet

	for z in l_sch_zenoss:
	# Recorrem la llista d'schedules del zenoss per afegir els que toqui al cachet
		i=0
                trobat=False
		while trobat == False and i<len(l_sch_cachet):
		# Recorrem la llista del cachet
			c=l_sch_cachet[i]
			if c["start"] == z["start"] and c["end"] == z["end"]:
				trobat=True
			i=i+1
		if trobat == False:
			msg=STR_FORMAT % (nomservei, z["start"].strftime("%d-%m-%Y"), z["start"].strftime("%H:%M"), z["end"].strftime("%d-%m-%Y"), z["end"].strftime("%H:%M")) 
			# Formatejam el missatge i cream l'schedule
                        st.ReportaSchedule(nomservei,msg,z["start"].strftime("%d/%m/%Y %H:%M"))

        for c in l_sch_cachet:
	# Recorrem la llista d'schedules del cachet per afegir els que toqui al cachet
                i=0
                trobat=False
                while trobat == False and i<len(l_sch_zenoss):
		# Recorrem la llista del zenoss
                        z=l_sch_zenoss[i]
                        if c["start"] == z["start"] and c["end"] == z["end"]:
                                trobat=True
                        i=i+1
                if trobat == False:
			st.eliminaIncident(c["id"])

			





def actualitza_component(st, id, nom, znom, perfok, aixeca):
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
		if st.getEstatId(id) == "maint":
			st.ArreglaIncident(nom,"El període de manteniment ha finalitzat amb èxit.")
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
                                        st.ArreglaIncident(nom,"El servei funciona correctament.",id)


        	else:
               		if st.getEstatId(id) != "down":
			# Cas en que el servei deixa de funcionar
				st.TombaComponent(id)
				st.ReportaIncident(nom,id,"Sembla que el servei està experimentant alguns problemes. Estam treballant perquè torni a estar operatiu el més aviat possible.")

for disp in root.findall('dispositiu'):

	aixeca = 1 # Variable per saber si hem d'aixecar o no el servei en qüestoó
	perfok = 1 # Variable per saber si el servei té un rendiment correcte
	scheduled_at = ""
#	if disp.text == "udp.sint.uib.es":
	if disp.text != "udp.sint.uib.ess":
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
		print nom+ " " + nompublic
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
					print "Ooops. Error en un event de "+nom
					print("Exception:", sys.exc_info()[0])
					print("Error:", e)
					pass
					

		##########################################################
		# Miram si el dispositiu ja no té events, però també cal mirar 
		#la severitat d'aquests events! Si no cumpleix el mínim de severitat
		# per tal de ser tombat l'aixecam.
		##########################################################

		##########################################################
		# Sincronitzam els Maintenance Windows
                #########################################################
		l_sch_zenoss=zp.get_deviceMaintWindows(zp.get_UID(disp.text))

		actualitza_schedule(st,nom,l_sch_zenoss,st.treuLlistaSchedule(nom))
		actualitza_component(st,id,nom,disp.text,perfok,aixeca)
		if nompublic != "null":
			#actualitza_schedule(st2,nompublic,l_sch_zenoss,st2.treuLlistaSchedule(nompublic))
			actualitza_component(st2,id2,nompublic,disp.text,perfok,aixeca)

