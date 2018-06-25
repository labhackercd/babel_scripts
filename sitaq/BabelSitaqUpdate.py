from BabelSitaq import put_discursos_Sitaq_Babel

############################################################################################################
# Bloco para chamada do script por linha de comando. O resultado é gravado em arquivo informado na chamada.
############################################################################################################
from datetime import datetime, timedelta
import sys
import time

if __name__ == '__main__':
    days_interval = 7
    if len(sys.argv) != 2:
        print ("Use: " + sys.argv[0] + " <número de dias>")
    else:
        try:
            final_date = datetime.today()
            initial_date = final_date - timedelta(days=int(sys.argv[1]))

            # Processa os discursos em lotes de "days_interval" dias, para evitar sobrecarga nos servidores
            idate = initial_date
            while idate <= final_date:
                put_discursos_Sitaq_Babel(idate.strftime('%d/%m/%Y'), (idate + timedelta(days=days_interval - 1)).strftime('%d/%m/%Y')) if idate + timedelta(days=days_interval - 1) < final_date else put_discursos_Sitaq_Babel(idate.strftime('%d/%m/%Y'), final_date.strftime('%d/%m/%Y'))
                idate = idate + timedelta(days=days_interval)
                if idate <= final_date:
                    time.sleep(10)  # Pára o processo por alguns segundos entre um lote e outro
        except Exception as e:
            arq = open('sitaq_errors.log', 'a')
            arq.write("###### FALHA GENÉRICA:\n" + str(sys.exc_info()[0]))
            arq.close()
            raise e
