############################################################################################################
# Bloco para chamada do script por linha de comando. O resultado é gravado em arquivo informado na chamada.
############################################################################################################
from datetime import datetime
from SitaqExtract import get_discursos_Sitaq_Fast
import sys
import json
if len(sys.argv) != 4:
    print ("Use: " + sys.argv[0] + " <initial date - DD/MM/YYYY> <final date - DD/MM/YYYY> <destination file>")
else:
    try:
        initial_date = datetime.strptime(sys.argv[1], '%d/%m/%Y').strftime('%d/%m/%Y')
        final_date = datetime.strptime(sys.argv[2], '%d/%m/%Y').strftime('%d/%m/%Y')
        resultado = get_discursos_Sitaq_Fast(initial_date, final_date)
        arq = open(sys.argv[3], 'w')
        arq.write(json.dumps(resultado))
        arq.close()
        print (str(len(resultado)) + " discursos extraídos")
    except Exception as e:
        raise e
