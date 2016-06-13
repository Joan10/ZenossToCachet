
import api_stashboard_panell_v2

st = api_stashboard_panell_v2.api_stashboard_panell("https://panell-estats.sint.uib.es:8080");

#Crea i tomba un servei
st.CreaServei("Test 01", "Aixo es una prova 01", "Grup 1");
st.TombaServei("Test 01", "Tombat")

#Crea i tomba un servei i tornal a aixecar
st.CreaServei("Test 02", "Aixo es una prova 02", "Grup 1");
st.TombaServei("Test 02", "Tombat")
st.AixecaServei("Test 02", "Tombat")

#Crea i tomba un servei i tornal a aixecar
st.CreaServei("Test 03", "");

#Actualitza la descripcio del primer servei
st.CreaServei("Test 01", "Aixo es una prova 01 canviada", "Grup 1");

#Actualitza el grup del primer servei
st.CreaServei("Test 01", "Aixo es una prova 01 canviada", "Grup 2");

# Treu id
print st.treuId("Test 01")
# Treu nom
print st.getNomComponent(st.treuId("Test 01"))
# Treu Desc
print st.getDescComponent(st.treuId("Test 01"))
# Treu Estat from id
print "Get status from Id de Test 01. Hauria de ser 4"
print st.getStatusFromId(st.treuId("Test 01"))
# Treu Estat
print "Get status from Id de Test 01. Hauria de ser Tombat"
print st.getEstat("Test 01")

print "Grup Test 01. Hauria de ser Grup 2"
print st.getGrup(st.treuId("Test 01"))
print "Grup Test 02. Hauria de ser Grup 1"
print st.getGrup(st.treuId("Test 02"))
print "Grup Test 03. Hauria de ser nul"
print st.getGrup(st.treuId("Test 03"))
print "Descripcio Test 03. Hauria de ser nul"
print st.getDescComponent(st.treuId("Test 03"))
print "Fet"
print "Esborrant"
print st.eliminaServei(st.treuId("Test 01"))
print st.eliminaServei(st.treuId("Test 02"))
print st.eliminaServei(st.treuId("Test 03"))
