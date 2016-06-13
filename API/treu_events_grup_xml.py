# -*- coding: utf-8 -*-

import ZenossAPI
from xml.etree.ElementTree import Element, SubElement, tostring

def treu_events_grup_xml(grup):
	z = ZenossAPI.ZenossAPI()
	try:
		devices = z.get_devices(grup)['devices']
	#	print devices
	except:
		devices = ""

	ndev=len(devices)

	root = Element('events')

	def processa_event(tag,element,pare):
		''' #DEBUG
			print "KEY:"
			print key
			print "ELEMENT:"
			print element
			print tostring(pare)
		'''
	
		if isinstance(element, basestring) or isinstance(element, int):
			# Cas base: element es string
			#print "----final:"+str(key)+":"+str(element)+"----"
			xml_subfield = SubElement(pare, tag)
			xml_subfield.text = str(element)
			return
		elif isinstance(element, dict):
			# Si és un diccionari, aprofundim en l'arbre XML. Ens
			# tornam a cridar amb les claus del diccionari com a tag
			# i amb element el valor del diccionari per l'entrada corresponent
			#print "----dict:"+str(key)+"----"
			xml_subfield = SubElement(pare, tag)
			for i in element:
				processa_event(i,element[i],xml_subfield)
		elif isinstance(element, list):
			# Si és una llista, recorrem tots els elements tenint en compte
			# que no hem d'aprofundir en l'arbre (no hem de crear nous tags XML)
			# per la qual cosa ens cridarem amb el mateix tag i amb el mateix pare.
			#print "----list:"+str(tag)+"----"
			for i in range(len(element)):
				processa_event(tag,element[i],pare)
		else:
			# Si està buit, és una variació del cas base.
			#print "----null:"+str(tag)+"----"
			xml_subfield = SubElement(pare, tag)
			xml_subfield.text = ""
		


	for i in range(ndev):
	#Iteram entre tots els dispositius
		dev = devices[i]['name']
		events=z.get_events(device=dev)['events']

		nevents=len(events)

	#	if nevents > 0 :
		xml_dev = SubElement(root, "dispositiu")
		xml_dev.text = dev

		for j in range(nevents):	
		#Iteram entre events de cada dispositiu
			processa_event("event", events[j], xml_dev)

	return tostring(root)
