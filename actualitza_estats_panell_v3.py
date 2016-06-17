#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Autor: Joan Arbona
# Script que actualitza la web de panell-estats, d'informació sobre l'estat de la infraestructura del CTI
# Es tracta d'una web que fa servir el gestor de continguts CACHET amb la qual s'hi interactua amb JSON
#

import sys
from datetime import datetime, date, time



sys.path.append("/home/stashboard/panell_serveis_critics_dev/ZenossToCachet/API/")
sys.path.append("/home/stashboard/secrets/")

from secrets import prod_public_hq_token,prod_private_hq_token,deve_public_hq_token,deve_private_hq_token

import treu_events_grup_xml
import api_stashboard_panell_v2 #Stashboard extens
import xml.etree.ElementTree as ET
import ZenossAPI


MIN_SEVERITY = 5

xml_string = treu_events_grup_xml.treu_events_grup_xml('/zport/dmd/Groups/serveis/serveis_critics')

root = ET.fromstring(xml_string)

# SERVIDORS PROVA
st = api_stashboard_panell_v2.api_stashboard_panell("http://10.80.87.76",deve_public_hq_token);
st2 = api_stashboard_panell_v2.api_stashboard_panell("http://10.80.87.76:9080",deve_private_hq_token);

# SERVIDORS PRODUCCIO
#st = api_stashboard_panell_v2.api_stashboard_panell("http://panell-estats-cti.sint.uib.es:8080",deve_private_hq_token);# Exclusiu del CTI 
#st2 = api_stashboard_panell_v2.api_stashboard_panell("http://panell-estats.sint.uib.es:8080",deve_public_hq_token);# Public

zp=ZenossAPI.ZenossAPI()



#DUMPING ET:
#ET.dump(TREE)

def actualitza(st, id, nom, perfok, aixeca, maint, maintmsg,date):
# 
# Funció que actualitza l'estat dels components i incidents del Cachet en funció de tres flags: perfok, aixeca i maint
# Té en compte els casos en què:
# 1. Hi ha problemes de rendiment. aixeca = 1, perfok = 0, maint=0
# 2. Hi ha problemes de rendiment, però està en manteniment. aixeca = 1, perfok = 0, maint=1
# 2. El servei torna a funcionar correctament. aixeca = 1, perfok = 1, maint = 0
# 2. El servei torna a funcionar correctament estant en manteniment. aixeca = 1, perfok = 1, maint = 1
# 3. El servei NO funciona. Aixeca = 0, perfok=X, maint = 0
# 4. El servei NO funciona però està en manteniment. Aixeca = 0, perfok=X, maint = 1
#
# En cas que el servei estigui en manteniment, maint=1, modificam el component però no aixecam incident.
	
	# Si hi ha algun manteniment programat generam un incident
	# miram primer si l'incident ja existeix i si no és així el cream.
	#print "--"+nom+"--"+str(id)
	#print "maint="+str(maint)
	#print "maintmsg="+maintmsg
	#print "perfok="+str(perfok)
	#print "aixeca="+str(aixeca)
	#print " "
	maint_act=st.componentEnManteniment(id);
	#print "maint_act="+maint_act
	if maint==1:
		# Si hi ha algun event de manteniment, miram si ja està reportat. Si no ho està l'afegim.
		# Si el dispositiu ja té algun incident de manteniment no el tornam a afegir
		if maint_act == "False":
			#st.ReportaIncidentManteniment(nom,id,maintmsg)
			st.ReportaSchedule(nom,maintmsg,date)
			st.posaComponentEnManteniment(id)
	else:
		# Si no n'hi ha cap, miram si no està reportat. Si hi està el treim.
		if maint_act == "True": # Si el dispositiu té algun incident de manteniment
#			st.ArreglaIncident(nom,id,"Manteniment finalitzat")
			st.llevaComponentDeManteniment(id)
		
	if aixeca == 1:
        	if perfok == 0:
                	if st.getEstatId(id) != "perf":
				# Cas en que hi ha problemes de rendiment
				st.ReportaComponent(id)
				if maint == 0:
					st.ReportaIncident(nom,id,"El servei està experimentant problemes de rendiment.")
                else:
                        if st.getEstatId(id) != "up":
				# Cas en que el servei torna a funcionar
				st.AixecaComponent(id)
				if maint == 0:
					st.ArreglaIncident(nom,id,"El servei funciona correctament.")
        else:
               if st.getEstatId(id) != "down":
			# Cas en que el servei deixa de funcionar
			st.TombaComponent(id)
			if maint == 0:
				st.ReportaIncident(nom,id,"Sembla que el servei està experimentant alguns problemes. Estam treballant perquè torni a estar operatiu el més aviat possible.")

for disp in root.findall('dispositiu'):

	aixeca = 1 # Variable per saber si hem d'aixecar o no el servei en qüestoó
	perfok = 1 # Variable per saber si el servei té un rendiment correcte
	maint = 0
	maintmsg = ""
	scheduled_at = ""
	if disp.text != "udp.sint.uib.ess":
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
						if  int(severity.text) == 2 and component.text != "" and eventClassKey.text != "":
							data_sch = component.text;
							t_data_sch=datetime.strptime(data_sch, "%Y-%m-%d %H:%M")
							if eventClassKey.text == "manteniment":
								maint=1
								maintmsg=message.text
								scheduled_at=t_data_sch.strftime("%d/%m/%Y %H:%M")
						
							
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

		actualitza(st,id,nom,perfok,aixeca,maint,maintmsg,scheduled_at)
	#	if nompublic != "null":
#			actualitza(st2,id2,nompublic,perfok,aixeca,maint,maintmsg,scheduled_at)

