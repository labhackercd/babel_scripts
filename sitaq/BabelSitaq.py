import requests
import json
import sys
import time
from datetime import datetime, timedelta
from SitaqExtract import get_discursos_Sitaq_Fast
from decouple import config

# CEP base para representar os estados no cadastro dos deputados no Babel
CEP = {'AC': '69900', 'AL': '57000', 'AP': '68900', 'AM': '69000',
       'BA': '40000', 'CE': '60000', 'DF': '70000', 'ES': '29000',
       'GO': '72800', 'MA': '65000', 'MT': '78000', 'MS': '79000',
       'MG': '30000', 'PA': '66000', 'PB': '58000', 'PR': '80000',
       'PE': '50000', 'PI': '64000', 'RJ': '20000', 'RN': '59000',
       'RS': '90000', 'RO': '78900', 'RR': '69300', 'SC': '88000',
       'SP': '01000', 'SE': '49000', 'TO': '77000'}


# Channel ID para "Sitaq" no Babel
BABEL_API_URL = config('BABEL_API_URL', default='http://localhost:8000/api/v1/')
CHANNEL_ID = config('CHANNEL_ID', default='')
MANIFESTATION_TYPE_ID = config('MANIFESTATION_TYPE_ID', default='')
AUTH_TOKEN = config('AUTH_TOKEN', default='')

##################################################################################
# Função que recupera o perfil de um autor no Babel (ou o grava, se não existir)
##################################################################################


def perfil_autor_discurso_Babel(discurso):

    # Pesquisa o autor do discurso no canal na base do Babel
    p = {'channel__id': CHANNEL_ID, 'id_in_channel': discurso['autor']['id']}
    perfil_babel = requests.get(
        BABEL_API_URL + 'profiles', params=p).json()['results']

    # Cadastra o perfil se ele ainda não existir
    if perfil_babel == []:

        # Busca o autor no Babel
        p = {'name': discurso['autor']['nome']}
        if 'tipo_autor' in discurso['autor']:
            p['author_type'] = discurso['autor']['tipo_autor']
            p['name'] = str.upper(p['name'])
        autor = requests.get(
            BABEL_API_URL + 'authors', params=p).json()['results']

        # Cadastra o autor se ele ainda não existir
        if autor == []:
            p = {'name': p['name'],
                 'author_type': discurso['autor']['tipo_autor']}
            if 'UF' in discurso['autor']:
                p['cep'] = CEP[discurso['autor']['UF']]
            if 'sexo' in discurso['autor']:
                p['gender'] = discurso['autor']['sexo']
            autor = requests.post(BABEL_API_URL + 'authors',
                                  json=p,
                                  headers={
                                      'Authorization': 'Token %s' % AUTH_TOKEN
                                  }).json()

        # Autor encontrado no Babel
        else:
            autor = autor[0]

        # Obtém os atributos do perfil para cadastrá-lo
        p = {'channel_id': CHANNEL_ID, 'id_in_channel': discurso['autor']['id'],
             'author_id': autor['id']}
        attrs = []
        if 'UF' in discurso['autor']:
            attrs.append({'field': 'UF', 'value': discurso['autor']['UF']})
        if 'partido' in discurso['autor']:
            attrs.append({'field': 'partido',
                          'value': discurso['autor']['partido']})
        p['attrs'] = attrs

        # Insere o perfil no Babel
        perfil_babel = requests.post(BABEL_API_URL + 'profiles',
                                     json=p,
                                     headers={
                                         'Authorization': 'Token %s' % AUTH_TOKEN
                                     }).json()

    # Perfil encontrado no Babel
    else:
        perfil_babel = perfil_babel[0]

    return perfil_babel

#################################################################################################
# Função que encontra as ocorrências de um discurso do Sitaq em uma lista de discursos do Babel #
#################################################################################################


def find_discurso_lista_Babel(discurso, listaDiscursosNoBabel):
    ds_babel = []
    for d_babel in listaDiscursosNoBabel:
        if discurso['id'] == d_babel['id_in_channel']:
            ds_babel.append(d_babel)
    return ds_babel


####################################################################################################
# Função que insere um discurso no Babel (ou o atualiza, se já existir e esta for uma nova versão) #
####################################################################################################
def put_discurso_Babel(discurso, listaDiscursosNoBabel):

    # Busca o discurso no Babel
    # p = {'manifestation_type_id':MANIFESTATION_TYPE_ID, 'id_in_channel':discurso['id']}
    # discursos_babel = requests.get(
    #     BABEL_API_URL + 'manifestations', params=p
    # ).json()['results']

    # Verifica se já há alguma ocorrência do discurso na lista obtida do Babel
    discursos_babel = find_discurso_lista_Babel(discurso, listaDiscursosNoBabel)

    # Inclui o discurso se ele não existir no Babel
    if discursos_babel == []:

        # print("Discurso não existe no Babel: \n" + json.dumps(discurso) + "\n")

        # Obtém o perfil do autor do discurso no Babel. Se não existir, cadastra
        perfil = perfil_autor_discurso_Babel(discurso)

        # Obtém os atributos do discurso para cadastrá-lo
        p = {'manifestation_type_id': MANIFESTATION_TYPE_ID,
             'profile_id': perfil['id'],
             'id_in_channel': discurso['id'],
             'content': discurso['integra'],
             'timestamp': discurso['dtDiscurso'],
             'url': discurso['url']}
        attrs = []
        attrs.append({'field': 'original', 'value': discurso['original']})
        attrs.append({'field': 'dtDiscurso', 'value': discurso['dtDiscurso']})
        attrs.append({'field': 'dtAtualizacao',
                      'value': discurso['dtAtualizacao']})
#        attrs.append({'field':'etapa', 'value':discurso['etapa']})
#        attrs.append({'field':'nuSessao', 'value':discurso['nuSessao']})
#        attrs.append({'field':'nuQuarto', 'value':discurso['nuQuarto']})
#        attrs.append({'field':'nuOrador', 'value':discurso['nuOrador']})
#        attrs.append({'field':'nuInsercao', 'value':discurso['nuInsercao']})
        if 'indexacao' in discurso:
            attrs.append({'field': 'indexacao', 'value': discurso['indexacao']})
        if 'fase' in discurso:
            attrs.append({'field': 'fase', 'value': discurso['fase']})
        p['attrs'] = attrs

        # Insere o discurso no Babel
        discurso_babel = requests.post(BABEL_API_URL + 'manifestations',
                                       json=p,
                                       headers={
                                           'Authorization': 'Token %s' % AUTH_TOKEN
                                       }).json()  # .json()

    # Se o discurso já existir no Babel, verifica se a data de atualização é diferente
    else:

        # Verifica, pela dtAtualizacao, se o discurso já está gravado no Babel com esta versão coletada
        nova_versao = True
        for discurso_babel in discursos_babel:
            for discurso_attr in discurso_babel['attrs']:
                if (discurso_attr['field'] == 'dtAtualizacao' and
                        discurso_attr['value'] == discurso['dtAtualizacao']):
                    nova_versao = False

        # Se for uma versão ainda inexistente, inclui o novo registro
        if nova_versao:

            # print("Nova versão de discurso do Babel: " + discurso['id'])

            max_version = 1
            if discurso_babel['version'] > max_version:
                max_version = discurso_babel['version']

            # Obtém o perfil do autor do discurso no Babel
            perfil = perfil_autor_discurso_Babel(discurso)

            # Obtém os atributos do discurso para cadastrá-lo
            p = {'manifestation_type_id': MANIFESTATION_TYPE_ID,
                 'profile_id': perfil['id'],
                 'id_in_channel': discurso['id'],
                 'content': discurso['integra'],
                 'timestamp': discurso['dtDiscurso'],
                 'url': discurso['url']}
            attrs = []
            attrs.append({'field': 'original', 'value': discurso['original']})
            attrs.append({'field': 'dtDiscurso',
                          'value': discurso['dtDiscurso']})
            attrs.append({'field': 'dtAtualizacao',
                          'value': discurso['dtAtualizacao']})
            if 'indexacao' in discurso:
                attrs.append({'field': 'indexacao',
                              'value': discurso['indexacao']})
            if 'fase' in discurso:
                attrs.append({'field': 'fase', 'value': discurso['fase']})
            p['attrs'] = attrs

            # Grava o novo número de versão da manifestação/discurso
            p['version'] = str(max_version + 1)

            # Insere a nova versão do discurso no Babel
            discurso_babel = requests.post(BABEL_API_URL + 'manifestations',
                                           json=p,
                                           headers={
                                               'Authorization': 'Token %s' % AUTH_TOKEN
                                           }).json()  # .json()
        else:
            discurso_babel = None

    return discurso_babel


#########################################################
# Obtém os discursos registrados no Babel de um período #
#########################################################
def get_discursos_Sitaq_Babel(initialDateTime, finalDateTime):

    # Obtém os discursos registrados no Babel no período
    p = {'manifestation_type__id': MANIFESTATION_TYPE_ID,
         'ordering': 'id',
         'timestamp__gte': datetime.strptime(
             initialDateTime, '%d/%m/%Y').strftime('%Y-%m-%d'),
         'timestamp__lt': (
             datetime.strptime(finalDateTime, '%d/%m/%Y') + timedelta(days=1)
         ).strftime('%Y-%m-%d')}

    # Obtém os discursos registrados no Babel
    listaDiscursosNoBabel = []
    resp = requests.get(BABEL_API_URL + 'manifestations', params=p).json()
    for discurso_babel in resp['results']:
        listaDiscursosNoBabel.append(discurso_babel)

    # Como a resposta do web service é paginada, percorre as páginas seguintes, enquanto houver
    while resp['next'] is not None:
        resp = requests.get(resp['next']).json()
        for discurso_babel in resp['results']:
            listaDiscursosNoBabel.append(discurso_babel)
        print("Recuperando discursos no Babel no período (" +
              initialDateTime + " a " + finalDateTime + "): " +
              str(len(listaDiscursosNoBabel)), end="\r")

    print("### " + initialDateTime + " a " + finalDateTime + ": " +
          str(len(listaDiscursosNoBabel)) + " discursos encontrados no Babel")

    return listaDiscursosNoBabel


#######################################################
# Insere no Babel os discursos do Sitaq de um período #
#######################################################
def put_discursos_Sitaq_Babel(initialDateTime, finalDateTime):
    try:
        # Obtém os discursos no Sitaq para um período
        listaDiscursos = get_discursos_Sitaq_Fast(
            initialDateTime, finalDateTime)

        # Obtém os discursos registrados no Babel para o mesmo período
        listaDiscursosNoBabel = get_discursos_Sitaq_Babel(
            initialDateTime, finalDateTime)

    except Exception as e:
        arq = open('sitaq_errors.log', 'a')
        arq.write("###### FALHA NO ACESSO AO WEBSERVICE DE DISCURSOS:\n" +
                  str(sys.exc_info()[0]) + "\n")
        arq.close()
        raise e
    num_discursos = 0
    num_discursos_incluidos = 0
    for discurso in listaDiscursos:
        try:
            discurso_babel = put_discurso_Babel(discurso, listaDiscursosNoBabel)
            if discurso_babel is not None:
                num_discursos_incluidos = num_discursos_incluidos + 1
            num_discursos = num_discursos + 1
            print("Incluindo/atualizando discursos no Babel (" +
                  initialDateTime + " a " + finalDateTime + "):" +
                  str(num_discursos) + " / " +
                  str(len(listaDiscursos)), end="\r")

        except Exception as e:
            arq = open('sitaq_errors.log', 'a')
            arq.write("###### FALHA NO REGISTRO DE UM DISCURSO:\n" +
                      str(sys.exc_info()[0]) + "\n")
            arq.write(json.dumps(discurso))
            arq.close()
            raise(e)
    print("### " + initialDateTime + " a " + finalDateTime + ": " +
          str(num_discursos_incluidos) +
          " discursos incluídos/atualizados de um total de " +
          str(len(listaDiscursos)) + " extraídos do Sitaq", end="\n")
    return num_discursos

############################################################################################
#  Bloco para chamada do script por linha de comando. O resultado é gravado no Babel via API.
############################################################################################


if __name__ == '__main__':
    days_interval = 7
    if len(sys.argv) != 3:
        print ("Use: " + sys.argv[0] + " <initial date - DD/MM/YYYY> <final date - DD/MM/YYYY>")
    else:
        try:
            initial_date = datetime.strptime(sys.argv[1], '%d/%m/%Y')  # .strftime('%d/%m/%Y')
            final_date = datetime.strptime(sys.argv[2], '%d/%m/%Y')  # .strftime('%d/%m/%Y')

            # Processa os discursos em lotes de "days_interval" dias, para evitar sobrecarga nos servidores
            idate = initial_date
            while idate <= final_date:
                put_discursos_Sitaq_Babel(idate.strftime('%d/%m/%Y'), (idate + timedelta(days=days_interval - 1)).strftime('%d/%m/%Y')) if idate + timedelta(days=days_interval - 1) < final_date else put_discursos_Sitaq_Babel(idate.strftime('%d/%m/%Y'), final_date.strftime('%d/%m/%Y'))
                idate = idate + timedelta(days=days_interval)
                if idate <= final_date:
                    time.sleep(5)  # Pára o processo por alguns segundos entre um lote e outro
        except Exception as e:
            arq = open('sitaq_errors.log', 'a')
            arq.write("###### FALHA GENÉRICA:\n" + str(sys.exc_info()[0]))
            arq.close()
            raise e
