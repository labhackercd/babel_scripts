# Does a one-way sync from câmara dados abertos to babel

from decouple import config
import json
import requests

BABEL_API_URL = config('BABEL_API_URL',
                       default='http://localhost:8000/api/v1/')
CHANNEL_ID = config('CHANNEL_ID',
                    default=2)
AUTH_TOKEN = config('AUTH_TOKEN', default='')

# CEP base para representar os estados no cadastro dos deputados no Babel
CEP = {'AC': '69900', 'AL': '57000', 'AP': '68900', 'AM': '69000',
       'BA': '40000', 'CE': '60000', 'DF': '70000', 'ES': '29000', 'GO': '72800',
       'MA': '65000', 'MT': '78000', 'MS': '79000', 'MG': '30000', 'PA': '66000',
       'PB': '58000', 'PR': '80000', 'PE': '50000', 'PI': '64000', 'RJ': '20000',
       'RN': '59000', 'RS': '90000', 'RO': '78900', 'RR': '69300', 'SC': '88000',
       'SP': '01000', 'SE': '49000', 'TO': '77000'}

nextUrl = 'https://dadosabertos.camara.leg.br/api/v2/deputados?ordenarPor=nome&itens=15'

while True:
    ret = requests.get(
        nextUrl,
        headers={'accept': 'application/json'}
    )
    deputados = json.loads(ret.content)

    for deputado in deputados['dados']:

        # Verificar se tem profile no Babel
        ret = requests.get(BABEL_API_URL + 'profiles',
                           params={
                               'id_in_channel': str(deputado['id']),
                               'channel__id': CHANNEL_ID})
        p = json.loads(ret.content)
        count = p['count']

        author_data = {
            'author_type': "Deputado",
            'birthdate': None,
            'cep': CEP[deputado['siglaUf']],
            'gender': None,
            'name': deputado['nome'],
        }

        profile_data = {
            'author_id': None,
            'channel_id': CHANNEL_ID,
            'url': deputado['uri'],
            'id_in_channel': deputado['id'],
            'is_reference': True,
            'attrs': [
                {'field': 'nome', 'value': deputado['nome']},
                {'field': 'siglaPartido', 'value': deputado['siglaPartido']},
                {'field': 'uriPartido', 'value': deputado['uriPartido']},
                {'field': 'siglaUF', 'value': deputado['siglaUf']},
                {'field': 'idLegislatura', 'value': deputado['idLegislatura']},
                {'field': 'urlFoto', 'value': deputado['urlFoto']},
            ],
        }

        if p['count']:
            # Se sim atualizar profile
            # Pegar IDs
            profile_id = p['results'][0]['id']
            author_id = p['results'][0]['author'].rsplit('/', 1)[-1]

            profile_data['author_id'] = author_id

            ret = requests.put(
                BABEL_API_URL + 'profiles/%s' % (profile_id,),
                json=profile_data,
                headers={
                    'Authorization': 'Token %s' % AUTH_TOKEN
                })

            if ret.status_code == 201:  # 201 == created
                print ("Atualizado profile de", deputado['nome'])
            else:
                print(ret.status_code, ret.content)
                break

            ret = requests.put(
                BABEL_API_URL + 'authors/%s' % (author_id,),
                json=author_data,
                headers={
                    'Authorization': 'Token %s' % AUTH_TOKEN
                })
            if ret.status_code == 201:  # 201 == created
                print ("Atualizado author de", deputado['nome'])
            else:
                print(ret.status_code, ret.content)
                break
        else:
            # Se não criar author + profile

            # Primeiro criar o author
            ret = requests.post(
                BABEL_API_URL + 'authors',
                json=author_data,
                headers={
                    'Authorization': 'Token %s' % AUTH_TOKEN
                })
            if ret.status_code == 201:  # 201 == created
                print ("Criado author para", deputado['nome'])
            else:
                print(ret.status_code, ret.content)
                break

            autor = json.loads(ret.content)

            profile_data['author_id'] = autor['id']

            ret = requests.post(
                BABEL_API_URL + 'profiles',
                json=profile_data,
                headers={
                    'Authorization': 'Token %s' % AUTH_TOKEN
                })
            if ret.status_code == 201:  # 201 == created
                print ("Criado profile para", deputado['nome'])
            else:
                print(ret.status_code, ret.content)
                break
    # Next page
    nextUrl = None
    for link in deputados['links']:
        if link['rel'] == 'next':
            nextUrl = link['href']

    if not nextUrl:
        break
