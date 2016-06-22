#|/bin/bash

if [ "$1" == "-h" ]; then
	echo "Usage: ./webinject0.sh <Host> <Nom Schedule> <Descripcio> <Data> <Pass>
	Crea un nou schedule al Cachet. Com que de moment no es pot fer per API REST, ho feim per HTTP.
	Data de la forma: DD/MM/YYYY HH:MM."
	exit 0;
fi
cd "${0%/*}"
host=$1
nom=$2
desc=`echo $3|iconv -f latin1 -t utf-8//translit`
data=$4
pass=$5

echo "<testcases repeat=\"0\">
<case
    id=\"1\"
    description1=\"short description\"
    description2=\"long description\"
    method=\"get\"
    url=\"$host/auth/login\"
    parseresponse='_token\" value=\"|\">|escape'

    verifyresponsecode=\"200\"
    logrequest=\"yes\"
    logresponse=\"yes\"
/>
<case
    id=\"2\"
    description1=\"short description\"
    description2=\"long description\"
    method=\"post\"
    url=\"$host/auth/login\"
    postbody=\"login=joan.arbona@uib.es&password=$pass&_token={PARSEDRESULT}\"
    verifyresponsecode=\"302\"
    logrequest=\"yes\"
    logresponse=\"yes\"
/>
<case
    id=\"3\"
    description1=\"short description\"
    description2=\"long description\"
    method=\"post\"
    url=\"$host/dashboard/schedule/add\"
    postbody=\"_token={PARSEDRESULT}&incident[visible]=1&incident[name]=$nom&incident[message]=$desc&incident[scheduled_at]=$data\"
    verifyresponsecode=\"302\"
    logrequest=\"yes\"
    logresponse=\"yes\"
/>
</testcases>" > update_schedules_cachethq.xml

./webinject.pl update_schedules_cachethq.xml


