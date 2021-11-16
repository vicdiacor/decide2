from os import name
import time
import random
import itertools
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.test import APITestCase

from base import mods
from base.tests import BaseTestCase
from census.models import Census
from mixnet.mixcrypt import ElGamal
from mixnet.mixcrypt import MixCrypt
from mixnet.models import Auth
from voting.models import Voting, Question, QuestionOption
from base.tests import SeleniumBaseTestCase
import re
from selenium.webdriver.support.ui import Select

class VotingTestCase(BaseTestCase):

    def setUp(self):
        # Crea un grupo con dos usuarios y otro con un usuario para probar el funcionamiento de los grupos en las votaciones
        g1 = Group(name='Grupo 1', pk=100)
        g1.save()

        g2 = Group(name='Grupo 2', pk=101)
        g2.save()

        u1 = User(username='username1Grupo1', password='password')
        u1.save()
        u1.groups.set([g1])
        u1.save()

        u2 = User(username='username2Grupo1', password='password')
        u2.save()
        u2.groups.set([g1])
        u2.save()

        u3 = User(username='username3Grupo2', password='password')
        u3.save()
        u3.groups.set([g2])
        u3.save()

        super().setUp()

    def tearDown(self):
        super().tearDown()

    def encrypt_msg(self, msg, v, bits=settings.KEYBITS):
        pk = v.pub_key
        p, g, y = (pk.p, pk.g, pk.y)
        k = MixCrypt(bits=bits)
        k.k = ElGamal.construct((p, g, y))
        return k.encrypt(msg)

    def create_voting(self):
        q = Question(desc='test question')
        q.save()
        for i in range(5):
            opt = QuestionOption(question=q, option='option {}'.format(i+1))
            opt.save()
        v = Voting(name='test voting', question=q)
        v.save()

        a, _ = Auth.objects.get_or_create(url=settings.BASEURL,
                                          defaults={'me': True, 'name': 'test auth'})
        a.save()
        v.auths.add(a)

        return v
    
    def create_voting_one_question_two_options(self):
        q = Question(desc='test question')
        q.save()
        opt1 = QuestionOption(question=q, option='option 1')
        opt1.save()
        opt2 = QuestionOption(question=q, option='option 2')
        opt2.save()
        v = Voting(name='test voting', question=q)
        v.save()

        a, _ = Auth.objects.get_or_create(url=settings.BASEURL,
                                          defaults={'me': True, 'name': 'test auth'})
        a.save()
        v.auths.add(a)

        return v
    
    def test_create_voting_one_question_two_options(self):
        v = self.create_voting_one_question_two_options()
        self.assertEquals(v.question.options.all()[0].option, 'option 1')

    def create_voters(self, v):
        for i in range(100):
            u, _ = User.objects.get_or_create(username='testvoter{}'.format(i))
            u.is_active = True
            u.save()
            c = Census(voter_id=u.id, voting_id=v.id)
            c.save()

    def get_or_create_user(self, pk):
        user, _ = User.objects.get_or_create(pk=pk)
        user.username = 'user{}'.format(pk)
        user.set_password('qwerty')
        user.save()
        return user

    def store_votes(self, v):
        voters = list(Census.objects.filter(voting_id=v.id))
        voter = voters.pop()

        clear = {}
        for opt in v.question.options.all():
            clear[opt.number] = 0
            for i in range(random.randint(0, 5)):
                a, b = self.encrypt_msg(opt.number, v)
                data = {
                    'voting': v.id,
                    'voter': voter.voter_id,
                    'vote': { 'a': a, 'b': b },
                }
                clear[opt.number] += 1
                user = self.get_or_create_user(voter.voter_id)
                self.login(user=user.username)
                voter = voters.pop()
                mods.post('store', json=data)
        return clear

    def test_complete_voting(self):
        v = self.create_voting()
        self.create_voters(v)

        v.create_pubkey()
        v.start_date = timezone.now()
        v.save()

        clear = self.store_votes(v)

        self.login()  # set token
        v.tally_votes(self.token)

        tally = v.tally
        tally.sort()
        tally = {k: len(list(x)) for k, x in itertools.groupby(tally)}

        for q in v.question.options.all():
            self.assertEqual(tally.get(q.number, 0), clear.get(q.number, 0))

        for q in v.postproc:
            self.assertEqual(tally.get(q["number"], 0), q["votes"])

    def test_create_voting_from_api(self):
        data = {'name': 'Example'}
        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 401)

        # login with user no admin
        self.login(user='noadmin')
        response = mods.post('voting', params=data, response=True)
        self.assertEqual(response.status_code, 403)

        # login with user admin
        self.login()
        response = mods.post('voting', params=data, response=True)
        self.assertEqual(response.status_code, 400)

        data = {
            'name': 'Example',
            'desc': 'Description example',
            'question': 'I want a ',
            'question_opt': ['cat', 'dog', 'horse'],
        }

        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 201)

    def test_update_voting(self):
        voting = self.create_voting()

        data = {'action': 'start'}
        #response = self.client.post('/voting/{}/'.format(voting.pk), data, format='json')
        #self.assertEqual(response.status_code, 401)

        # login with user no admin
        self.login(user='noadmin')
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 403)

        # login with user admin
        self.login()
        data = {'action': 'bad'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)

        # STATUS VOTING: not started
        for action in ['stop', 'tally']:
            data = {'action': action}
            response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json(), 'Voting is not started')

        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Voting started')

        # STATUS VOTING: started
        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already started')

        data = {'action': 'tally'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting is not stopped')

        data = {'action': 'stop'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Voting stopped')

        # STATUS VOTING: stopped
        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already started')

        data = {'action': 'stop'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already stopped')

        data = {'action': 'tally'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Voting tallied')

        # STATUS VOTING: tallied
        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already started')

        data = {'action': 'stop'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already stopped')

        data = {'action': 'tally'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already tallied')
    
    def test_create_voting_api(self):
        self.login()
        data = {
            'name': 'vot_test',
            'desc': 'desc_test',
            'question': 'quest_test',
            'question_opt': ['1', '2']
        }

        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 201)

        voting = Voting.objects.get(name='vot_test')
        self.assertEqual(voting.desc, 'desc_test')


    def test_create_voting_api_with_group(self):
        self.login()

        #formato incorrecto para groups
        data = {
            'name': 'vot_test2',
            'desc': 'desc_test2',
            'question': 'quest_test',
            'question_opt': ['1', '2'],
            'groups': 'prueba'
        }

        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 400)

        #intento crear votacion con grupo que no existe
        data = {
            'name': 'vot_test2',
            'desc': 'desc_test2',
            'question': 'quest_test',
            'question_opt': ['1', '2'],
            'groups': '145646'
        }

        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 400)

        #formato correcto para groups
        data = {
            'name': 'vot_test2',
            'desc': 'desc_test2',
            'question': 'quest_test',
            'question_opt': ['1', '2'],
            'groups': '100,101'
        }

        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 201)

        voting = Voting.objects.get(name='vot_test2')
        self.assertEqual(voting.desc, 'desc_test2')

        numUsersInCensus = Census.objects.filter(voting_id=voting.pk).count()
        self.assertEqual(numUsersInCensus, 3)

        

class SeleniumTestCase(SeleniumBaseTestCase):    

    def setUp(self):
        a = Auth(name='prueba', url='http://localhost:8000', me=True)
        a.save()

        q = Question(desc='pregunta de prueba')
        q.save()
        opt1 = QuestionOption(question=q, option='opcion 1')
        opt1.save()
        opt2 = QuestionOption(question=q, option='opcion 2')
        opt2.save()

        g1 = Group(name='Grupo 1', pk=100)
        g1.save()

        g2 = Group(name='Grupo 2', pk=101)
        g2.save()

        u1 = User(username='username1Grupo1', password='password')
        u1.save()
        u1.groups.set([g1])
        u1.save()

        u2 = User(username='username2Grupo1', password='password')
        u2.save()
        u2.groups.set([g1])
        u2.save()

        u3 = User(username='username3Grupo2', password='password')
        u3.save()
        u3.groups.set([g2])
        u3.save()

        return super().setUp()

    def test_create_question(self):
        self.login()
        self.driver.find_element_by_link_text('Questions').click()
        self.driver.find_element_by_class_name('object-tools').click()
        self.driver.find_element_by_id('id_desc').send_keys('Descripción de prueba')
        self.driver.find_element_by_id('id_options-0-number').send_keys('1')
        self.driver.find_element_by_id('id_options-0-option').send_keys('Opción 1')
        self.driver.find_element_by_id('id_options-1-number').send_keys('2')
        self.driver.find_element_by_id('id_options-1-option').send_keys('Opción 2')
        self.driver.find_element_by_name('_save').click()
        
        # Checks if it is stored in the database
        self.driver.find_element_by_link_text('Descripción de prueba').click()

        self.assertTrue(re.fullmatch(f'{self.live_server_url}/admin/voting/question/\\d*?/change/', self.driver.current_url))


    def test_create_voting_correct(self):
        self.login()
        self.driver.find_element_by_link_text('Votings').click()
        self.driver.find_element_by_class_name('object-tools').click()
        self.driver.find_element_by_id('id_name').send_keys('Votacion de prueba')
        self.driver.find_element_by_id('id_desc').send_keys('prueba')

        select = Select(self.driver.find_element_by_id('id_question'))
        select.select_by_visible_text('pregunta de prueba')

        self.driver.find_element_by_id('id_groups').send_keys('100,101')

        select = Select(self.driver.find_element_by_id('id_auths'))
        select.select_by_visible_text('http://localhost:8000')

        self.driver.find_element_by_name('_save').click()        
        
        # Checks if it is stored in the database
        self.driver.find_element_by_link_text('Votacion de prueba').click()

        self.assertTrue(re.fullmatch(f'{self.live_server_url}/admin/voting/voting/\\d*?/change/', self.driver.current_url))
        
        # Comprueba que hay usuarios en el censo de dicha votacion
        self.driver.get(f'{self.live_server_url}/admin/census/census/')
        self.driver.find_element_by_tag_name(name='tr')

    
    # Varios casos incorrectos
    def test_create_voting_incorrect(self):
        self.login()

        #formato incorrecto para los grupos
        self.driver.find_element_by_link_text('Votings').click()
        self.driver.find_element_by_class_name('object-tools').click()
        self.driver.find_element_by_id('id_name').send_keys('Votacion de prueba')
        self.driver.find_element_by_id('id_desc').send_keys('prueba')

        select = Select(self.driver.find_element_by_id('id_question'))
        select.select_by_visible_text('pregunta de prueba')

        self.driver.find_element_by_id('id_groups').send_keys('prueba')

        select = Select(self.driver.find_element_by_id('id_auths'))
        select.select_by_visible_text('http://localhost:8000')

        self.driver.find_element_by_name('_save').click()        
        
        self.driver.find_element_by_class_name('errornote')

        # compruebo con grupo que no existe
        self.driver.find_element_by_id('id_groups').send_keys('14367')
        self.driver.find_element_by_name('_save').click()        
        
        self.driver.find_element_by_class_name('errornote')



