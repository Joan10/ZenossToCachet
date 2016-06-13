
import api_stashboard_panell_v2

print "SEGUR QUE VOLEU ESBORRAR TOOOTS ELS DISPOSITIUS? Escriviu SI"
s=raw_input('Enter your input:')
print s
if s != "SI":
	quit()
else:
	print "hello"
	st = api_stashboard_panell_v2.api_stashboard_panell("https://panell-estats.sint.uib.es:8080");
	for i in range(1,200):
		try:
			print str(i)
			st.eliminaGrups(str(i))
		except:
			pass
