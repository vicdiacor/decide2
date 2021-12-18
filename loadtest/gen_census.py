import json
import requests
import os


HOST = "http://localhost:8000"
USER = "decide1"
PASS = "decide1234"

def login(user=USER, password=PASS):
    data = {'username': user, 'password': password}
    response = requests.post(HOST + '/authentication/login/', data=data)
    token = response.json()
    return token


def create_voters(filename):
    """
    Create voters with requests library from filename.json, where key are
    usernames and values are the passwords.
    """
    with open(filename) as f:
        voters = json.loads(f.read())

    token = login()

    voters_pk = []
    invalid_voters = []
    for username, pwd in voters.items():
        token.update({'username': username, 'password': pwd})
        response = requests.post(HOST + '/authentication/register/', data=token)
        if response.status_code == 201:
            voters_pk.append({'id': response.json().get('user_pk'), 'username': username, 'pass': pwd})
        else:
            invalid_voters.append(username)
    return voters_pk, invalid_voters


def add_census(voters, voting_pk):
    """
    Add to census all voters_pk in the voting_pk.
    """
    token = login()

    data2 = {'voters': [v['id'] for v in voters], 'voting_id': voting_pk}
    auth = {'Authorization': 'Token ' + token.get('token')}
    response = requests.post(HOST + '/census/', json=data2, headers=auth)
    print(response.text)

def create_voting() -> int:
    token = login()
    data = {
            'name': 'Votación para estadísticas',
            'desc': 'Esta votación se crea de prueba para poder ver las estadísticas de manera más fácil',
            'question': 'Animal preferido',
            'question_opt': ['Gato', 'Perro', 'Hamster', 'Conejo', 'Carpincho', 'Jirafa']
        }
    auth = {'Authorization': 'Token ' + token.get('token')}
    response = requests.post(HOST + '/voting/', json=data, headers=auth)
    print(response.status_code)
    voting_id = json.loads(response.text)['id']

    data = {'action': 'start'}
    response = requests.put(f'{HOST}/voting/{voting_id}/', json=data, headers=auth)
    print(response.status_code)

    return voting_id

def vote(filename):
    voters, invalids = create_voters(filename)
    if len(invalids) > 0:
        raise Exception('Borra los usuarios existentes antes de empezar')

    voting_id = create_voting()

    add_census(voters, voting_id)
    
    print('Votaciones: ')
    for voter in voters:
        id_, username, pwd = voter['id'], voter['username'], voter['pass']
        token = login(username, pwd)
        auth = {'Authorization': 'Token ' + token.get('token')}
        data = {
                "voting": voting_id,
                "voter": id_,
                "vote": {'Gato': 0, 'Perro': 0, 'Hamster': 1, 'Conejo': 0, 'Carpincho': 0, 'Jirafa': 0}
            }
        response = requests.post(HOST + '/store/', json=data, headers=auth)
        print(response.status_code)
    
    token = login()
    auth = {'Authorization': 'Token ' + token.get('token')}
    data = {'action': 'stop'}
    response = requests.put(f'{HOST}/voting/{voting_id}/', json=data, headers=auth)
    print(response.status_code)

    data = {'action': 'tally'}
    response = requests.put(f'{HOST}/voting/{voting_id}/', json=data, headers=auth)
    print(response.status_code)
    print(f'Ve a {HOST}/visualizer/{voting_id} para ver los resultados.')

current_path = '/'.join(__file__.split('/')[:-1])
vote(current_path + '/voters.json')
# print(create_voting())
# voters, invalids = create_voters(current_path + '/voters.json')
# add_census(voters, create_voting())
# print("Create voters with pk={0} \nInvalid usernames={1}".format(voters, invalids))
