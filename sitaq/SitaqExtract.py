import requests
import json
import re
import sys
from datetime import datetime
from decouple import config


SITAQ_API_URL = config('SITAQ_API_URL', default='')


######################################
# Retira todas tags de um texto HTML #
######################################


def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext


###################################
# Retira os parênteses de um nome #
###################################
def clean_name(raw_name):
    cleanr = re.compile('\(.*?\)')
    cleantext = re.sub(cleanr, '', raw_name)
    return cleantext


############################################################
# Retira o conteúdo entre dois marcadores de um texto HTML #
############################################################
def extract_content(raw_html, mark1, mark2):
    contentr = re.search(mark1 + '.*?' + mark2, raw_html)[0]
    contentr = contentr.split(mark1)[1].rsplit(mark2)[0]
    return clean_html(contentr)


##########################################################################################################
# Retira a apresentação do orador no início da íntegra - vai até o primeiro " -" depois do nome do autor #
##########################################################################################################
def extract_orador_from_content(content, orador):
    extracao = re.search(orador + '.*?$', content, flags=re.IGNORECASE)
    if extracao is not None and extracao.start(0) < 200:
        contentr = extracao[0]
        extracao = re.search(' - .*?$', contentr, flags=re.IGNORECASE)
        if extracao is not None and extracao.start(0) < 200:  # REAVALIAR. Não funciona para pronunciamento
            contentr = extracao[0]                            # encaminhado pelo orador muito grande
            contentr = re.sub(' - ', '', contentr, flags=re.IGNORECASE)
        else:
            contentr = re.sub(orador + '[^a-zA-Z0-9]*', '', contentr, flags=re.IGNORECASE)
    else:
        contentr = content

    # Verifica se o pronunciamento foi encaminhado pelo autor
    encaminhado = re.match('PRONUNCIAMENTO[S]* ENCAMINHADO.*?$', content, flags=re.IGNORECASE)
    if encaminhado is not None:
        # Verifica se ainda há marcação de encaminhado no início da íntegra - content"r"
        encaminhado = re.match('PRONUNCIAMENTO[S]* ENCAMINHADO.*?$', contentr, flags=re.IGNORECASE)
        if encaminhado is not None:
            contentr = encaminhado[0]
            encaminhado = re.search('\) - .*?$', contentr, flags=re.IGNORECASE)
            if encaminhado is not None:
                contentr = encaminhado[0]
                contentr = re.sub('\) - ', '', contentr, flags=re.IGNORECASE)
        contentr = 'PRONUNCIAMENTO ENCAMINHADO PELO ORADOR ' + contentr

    return contentr


######################################################################
# Retira a manifestação do presidente ao final da íntegra, se houver #
######################################################################
def extract_presidente_from_content(content):
    presidr = re.search('O SR\. PRESIDENTE\s*?\(.*?$', content, flags=re.IGNORECASE)
    if presidr is not None:
        contentr = content.rsplit(presidr[0])[0].rstrip()

        # Verifica se há pronunciamento encaminhado pelo autor concatenado ao final do discurso
        encaminhado = re.search('PRONUNCIAMENTO[S]* ENCAMINHADO[S]*.*?$', presidr[0], flags=re.IGNORECASE)
        if encaminhado is not None:
            contentr = contentr + ' ' + encaminhado[0]
#        else:
#            # Verificar se ha pronunciamentos (no plural!) encaminhados pelo autor
#            encaminhado = re.search('PRONUNCIAMENTOS ENCAMINHADOS PELO ORADOR.*?$', presidr[0], flags=re.IGNORECASE)
#            if encaminhado is not None:
#                contentr = contentr + ' ' + encaminhado[0]

    else:
        contentr = content
    return contentr


##############################################################
# Obtém lista de discursos no Sitaq em um intervalo de tempo #
##############################################################
def get_discursos_Sitaq_Fast(initialDateTime, finalDateTime):
    p = {'siglaAplicacao': 'novoDiscurso',
         'ordenacao': 'data',
         'ordenacaoDir': 'asc',
         'dataInicial': initialDateTime,
         'dataFinal': finalDateTime}
    response = requests.get(SITAQ_API_URL, params=p)
    if len(response.content) == 0:
        raise Exception("No data returned by Sitaq web service")

    qtdPorPagina = json.loads(response.content)["qtdPorPagina"]
    qtdDePaginas = json.loads(response.content)["qtdDePaginas"]
    num_discursos_total = json.loads(response.content)["total"]
    listaDiscursos = []

    for pagina in range(1, qtdDePaginas + 1):
        p = {'siglaAplicacao': 'novoDiscurso', 'ordenacao': 'data',
             'ordenacaoDir': 'asc', 'dataInicial': initialDateTime,
             'dataFinal': finalDateTime, 'pagina': pagina}
        response = requests.get(SITAQ_API_URL, params=p)
        listaDiscursosHTML = json.loads(response.content)["indexProfile"]

        for discursoHTML in listaDiscursosHTML:
            try:
                # Verifica se o discurso tem íntegra e se não foi registrado em sessão solene
                # Nas sessões solenes, o Detaq coloca a ata da reunião onde deveria estar a íntegra
                # do discurso do deputado
                if ((discursoHTML["companyteaser"] is not None) and
                        (re.search("Não Deliberativa Solene", discursoHTML["tipoconteudo"]) is None)):

                    # Captura dados do autor do discurso
                    autor = {}
                    if discursoHTML['tipoautor'] is not None:
                        autor['tipo_autor'] = discursoHTML['tipoautor'].lstrip().rstrip()
                    if discursoHTML['autor'] is not None:
                        autor['nome'] = clean_name(discursoHTML['autor']).lstrip().rstrip().title()
                        if autor['tipo_autor'] is not None and autor['tipo_autor'] == 'Deputado':
                            autor['id'] = autor['tipo_autor'] + ' ' + autor['nome']
                        else:
                            autor['id'] = autor['nome']
                    if discursoHTML['estado'] is not None:
                        autor['UF'] = discursoHTML['estado'].lstrip().rstrip()
                    if discursoHTML['partido'] is not None:
                        autor['partido'] = discursoHTML['partido'].lstrip().rstrip()
                    if discursoHTML['emails'] is not None:
                        autor['sexo'] = discursoHTML['emails'].lstrip().rstrip()

                    # Associa autor ao discurso
                    discurso = {}
                    discurso['autor'] = autor

                    # Obtém informações acessórias para compor a url do discurso:
                    # etapa, sessão, quarto, orador, inserção
                    discurso['etapa'] = extract_content(discursoHTML['url'], "etapa=", "&")
                    discurso['nuSessao'] = extract_content(discursoHTML['url'], "numSessao=", "&")
                    discurso['nuQuarto'] = extract_content(discursoHTML['url'], "numQuarto=", "&")
                    discurso['nuOrador'] = extract_content(discursoHTML['url'], "numOrador=", "&")
                    discurso['nuInsercao'] = extract_content(discursoHTML['url'], "numInsercao=", "$")
                    discurso['url'] = ("http://www.camara.leg.br/internet/sitaqweb/TextoHTML.asp?etapa=" +
                                       discurso['etapa'] + "&nuSessao=" + discurso['nuSessao'] +
                                       "&nuQuarto=" + discurso['nuQuarto'] + "&nuOrador=" +
                                       discurso['nuOrador'] + "&nuInsercao=" + discurso['nuInsercao'])

                    # ID do discurso formado por nu_sessao (generic3) + nu_quarto (generic4) + nu_sequencia (generic5)
                    discurso['id'] = (discurso['nuSessao'] +
                                      " " + discurso['nuQuarto'] +
                                      " " + discurso['nuOrador'] +
                                      " " + discurso['nuInsercao'])

                    # Extrai íntegra do discurso do campo "companyteaser", no <body>
                    discurso['integra'] = extract_content(
                        discursoHTML["companyteaser"], "<body>", "</body>").lstrip().rstrip()
                    discurso['original'] = discurso['integra']
                    discurso['integra'] = extract_orador_from_content(discurso['integra'], autor['nome'])
                    discurso['integra'] = extract_presidente_from_content(discurso['integra'])

                    # Indexação manual de termos feita pelo Departamento de Taquigrafia
                    if discursoHTML['generic14'] is not None:
                        discurso['indexacao'] = discursoHTML['generic14'].lstrip().rstrip()

                    # Fase da sessão em que ocorreu o discurso
                    if discursoHTML['generic10'] is not None:
                        discurso['fase'] = discursoHTML['generic10'].lstrip().rstrip()
                        discurso['url'] = discurso['url'] + "&sgFaseSessao=" + discurso['fase']

                    # Data e hora do discurso
                    if discursoHTML['docdatetime'] is not None:
                        # discurso['dtDiscurso'] = datetime.strptime(
                        #    discursoHTML['docdatetime'].lstrip().rstrip(), '%Y-%m-%dT%H:%M:%SZ')
                        discurso['dtDiscurso'] = str(
                            datetime.strptime(discursoHTML['docdatetime'].lstrip().rstrip(), '%Y-%m-%dT%H:%M:%SZ'))

                        # Acrescenta data e hora na url do discurso
                        discurso['url'] = discurso['url'] + "&Data=" + datetime.strptime(
                            discursoHTML['docdatetime'].lstrip().rstrip(), '%Y-%m-%dT%H:%M:%SZ').strftime("%d/%m/%Y")
                        discurso['url'] = discurso['url'] + "&dtHorarioQuarto=" + datetime.strptime(
                            discursoHTML['docdatetime'].lstrip().rstrip(), '%Y-%m-%dT%H:%M:%SZ').strftime("%H:%M")

                    # Data e hora da última atualização do discurso
                    if discursoHTML['processingtime'] is not None:
                        # discurso['dtAtualizacao'] = datetime.strptime(
                        #     discursoHTML['processingtime'].lstrip().rstrip(), '%Y-%m-%dT%H:%M:%SZ')
                        discurso['dtAtualizacao'] = str(
                            datetime.strptime(discursoHTML['processingtime'].lstrip().rstrip(), '%Y-%m-%dT%H:%M:%SZ'))

                    # Insere o discurso extraído na lista e atualiza a saída padrão com o número processado
                    listaDiscursos.append(discurso)
                    print("Extraindo discursos do Sitaq (" + initialDateTime +
                          " a " + finalDateTime + "): " +
                          str(len(listaDiscursos)) + " / " +
                          str(num_discursos_total), end="\r")

            # Registra exceções em arquivo de erros
            except Exception as e:
                arq = open('sitaq_errors.log', 'a')
                arq.write("###### EXCEÇÃO: " + str(sys.exc_info()[0]))
                arq.write("\n  ## ID do discurso: " + str(discursoHTML['url']) + "\n")
                arq.close()
                # raise e

    print("### " + initialDateTime + " a " + finalDateTime + ": " +
          str(len(listaDiscursos)) + " discursos válidos extraídos do Sitaq" +
          " (de um total de " + str(num_discursos_total) + " encontrados)",
          end="\n")

    return listaDiscursos
