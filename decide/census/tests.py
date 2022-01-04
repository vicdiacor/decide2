import random
from django.contrib.auth.models import User, UserManager, Group
from django.test import TestCase, Client

from rest_framework.test import APIClient

from .models import Census, ParentGroup, Request
from base import mods
from base.tests import BaseTestCase
import logging as log
from base.tests import SeleniumBaseTestCase
import re
from selenium.webdriver.support.ui import Select
from mixnet.models import Auth


class CensusTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.census = Census(voting_id=1, voter_id=1)
        self.census.save()

    def tearDown(self):
        super().tearDown()
        self.census = None

    def test_check_vote_permissions(self):
        response = self.client.get(
            '/census/{}/?voter_id={}'.format(1, 2), format='json')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), 'Invalid voter')

        response = self.client.get(
            '/census/{}/?voter_id={}'.format(1, 1), format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Valid voter')

    def test_list_voting(self):
        response = self.client.get(
            '/census/?voting_id={}'.format(1), format='json')
        self.assertEqual(response.status_code, 401)

        self.login(user='noadmin')
        response = self.client.get(
            '/census/?voting_id={}'.format(1), format='json')
        self.assertEqual(response.status_code, 403)

        self.login()
        response = self.client.get(
            '/census/?voting_id={}'.format(1), format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'voters': [1]})

    def test_add_new_voters_conflict(self):
        data = {'voting_id': 1, 'voters': [1]}
        response = self.client.post('/census/', data, format='json')
        self.assertEqual(response.status_code, 401)

        self.login(user='noadmin')
        response = self.client.post('/census/', data, format='json')
        self.assertEqual(response.status_code, 403)

        self.login()
        response = self.client.post('/census/', data, format='json')
        self.assertEqual(response.status_code, 409)

    def test_add_new_voters(self):
        data = {'voting_id': 2, 'voters': [1, 2, 3, 4]}
        response = self.client.post('/census/', data, format='json')
        self.assertEqual(response.status_code, 401)

        self.login(user='noadmin')
        response = self.client.post('/census/', data, format='json')
        self.assertEqual(response.status_code, 403)

        self.login()
        response = self.client.post('/census/', data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(data.get('voters')), Census.objects.count() - 1)

    def test_destroy_voter(self):
        data = {'voters': [1]}
        response = self.client.delete(
            '/census/{}/'.format(1), data, format='json')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(0, Census.objects.count())


class ParentGroupTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.group = ParentGroup(name='test_group', isPublic=True)
        self.group.save()

    def tearDown(self):
        super().tearDown()
        self.group = None

    def test_list_groups(self):
        response = self.client.get('/admin/census/parentgroup/')
        self.assertEqual(response.status_code, 302)

    def test_create_group(self):

        self.login()
        data = {'name': 'test_group', 'isPublic': True}
        response = self.client.post('/admin/census/parentgroup/add/', data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual('test_group', ParentGroup.objects.get(
            name='test_group').name)

    # def test_delete_group(self):

    #     self.login()
    #     response = self.client.post('/admin/census/parentgroup/{}/delete/'.format(self.group.id))
    #     print(response)
    #     self.assertEqual(response.status_code, 302)
    #     self.assertEqual(0, ParentGroup.objects.count())


class GroupOperationsTestCases(BaseTestCase):

    def setUp(self):
        super().setUp()

        user1 = User(username='user1')
        user1.set_password('user1')
        user1.save()

        user2 = User(username='user2')
        user2.set_password('user2')
        user2.save()

        user3 = User(username='user3')
        user3.set_password('user3')
        user3.save()

        user4 = User(username='user4')
        user4.set_password('user4')
        user4.save()

        group1 = ParentGroup.objects.create(name='group1')
        group1.user_set.set([user1, user2, user3])

        group2 = ParentGroup.objects.create(name='group2')
        group2.user_set.set([user1, user2, user4])

        group3 = ParentGroup.objects.create(name='group3')

        self.groups = [group1, group2]
        self.users = [user1, user2, user3, user4]

    def tearDown(self):
        super().tearDown()

    def test_group_operation_wrong_name(self):
        data = {'groups': ['group1', 'group2'], 'is_public': True}

        self.login(user='user1', password='user1')
        response = self.client.post('/census/union', data, format='json')
        self.assertEqual(response.status_code, 400)

        data = {'name': '', 'groups': ['group1', 'group2'], 'is_public': True}

        self.login(user='user1', password='user1')
        response = self.client.post(
            '/census/intersection', data, format='json')
        self.assertEqual(response.status_code, 400)

        data = {'name': 2, 'groups': ['group1', 'group2'], 'is_public': True}

        self.login(user='user1', password='user1')
        response = self.client.post('/census/difference', data, format='json')
        self.assertEqual(response.status_code, 400)

        data = {'name': '  ', 'groups': [
            'group1', 'group2'], 'is_public': True}

        self.login(user='user1', password='user1')
        response = self.client.post('/census/union', data, format='json')
        self.assertEqual(response.status_code, 400)

    def test_group_operation_name_already_exist(self):
        data = {'name': 'group1', 'groups': ['group1', 'group2'], 'is_public': True}

        self.login(user='user1', password='user1')
        response = self.client.post('/census/union', data, format='json')
        self.assertEqual(response.status_code, 409)

    def test_group_operation_groups(self):
        data = {'name': 'test', 'is_public': True}

        self.login(user='user1', password='user1')
        response = self.client.post(
            '/census/intersection', data, format='json')
        self.assertEqual(response.status_code, 400)

        data = {'name': 'test', 'groups': 'group1','is_public': True}

        self.login(user='user1', password='user1')
        response = self.client.post(
            '/census/intersection', data, format='json')
        self.assertEqual(response.status_code, 400)

        data = {'name': 'test', 'groups': ['group1', 2],'is_public': True}

        self.login(user='user1', password='user1')
        response = self.client.post(
            '/census/intersection', data, format='json')
        self.assertEqual(response.status_code, 400)

        data = {'name': 'test', 'groups': ['group1'],'is_public': True}

        self.login(user='user1', password='user1')
        response = self.client.post(
            '/census/intersection', data, format='json')
        self.assertEqual(response.status_code, 400)

    def test_group_operation_wrong_public(self):
        data = {'name': 'test', 'groups': ['group1', 'group2']}

        self.login(user='user1', password='user1')
        response = self.client.post(
            '/census/intersection', data, format='json')
        self.assertEqual(response.status_code, 400)

        data = {'name': 'test', 'groups': ['group1', 'group2'],'is_public': 'True'}

        self.login(user='user1', password='user1')
        response = self.client.post(
            '/census/intersection', data, format='json')
        self.assertEqual(response.status_code, 400)

    def test_group_operation_without_being_member(self):
        data = {'name': 'test', 'groups': ['group1', 'group2', 'group3'],'is_public': True}

        self.login(user='user1', password='user1')
        response = self.client.post(
            '/census/intersection', data, format='json')
        self.assertEqual(response.status_code, 401)

        data = {'name': 'test', 'groups': ['group1', 'group2', 'ula'],'is_public': True}

        self.login(user='user1', password='user1')
        response = self.client.post(
            '/census/intersection', data, format='json')
        self.assertEqual(response.status_code, 400)

    def test_group_union(self):
        data = {'name': 'union', 'groups': [
            'group1', 'group2'], 'is_public': True}

        response = self.client.post('/census/union', data, format='json')
        self.assertEqual(response.status_code, 401)

        self.login(user='user1', password='user1')
        response = self.client.post('/census/union', data, format='json')
        self.assertEqual(response.status_code, 201)

        union = Group.objects.get(name='union')
        self.assertEqual(len(union.user_set.all()), len(self.users))

    def test_group_intersection(self):
        data = {'name': 'intersection',
                'groups': ['group1', 'group2'], 'is_public': False}

        response = self.client.post(
            '/census/intersection', data, format='json')
        self.assertEqual(response.status_code, 401)

        self.login(user='user1', password='user1')
        response = self.client.post(
            '/census/intersection', data, format='json')
        self.assertEqual(response.status_code, 201)

        intersection = Group.objects.get(name='intersection')
        self.assertEqual(len(intersection.user_set.all()), 2)

    def test_group_difference(self):
        data = {'name': 'difference', 'groups': [
            'group1', 'group2'], 'is_public': True}

        response = self.client.post('/census/difference', data, format='json')
        self.assertEqual(response.status_code, 401)

        self.login(user='user1', password='user1')
        response = self.client.post('/census/difference', data, format='json')
        self.assertEqual(response.status_code, 201)

        difference = Group.objects.get(name='difference')
        self.assertEquals(len(difference.user_set.all()), 1)

class PositiveRequestSeleniumTestCase(SeleniumBaseTestCase):    

    def setUp(self):

        u1 = User(username='username1Grupo1', password='password')
        u1.save()

        pg1 = ParentGroup(name='Grupo 1', pk=100, isPublic=False)
        pg1.save()

        rq1 = Request(voter_id=u1.pk, group_id=100)
        rq1.save()

        rq2 = Request(voter_id=u1.pk, group_id=100)
        rq2.save()

        rq3 = Request(voter_id=u1.pk, group_id=100)
        rq3.save()

        return super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_accept_private_request(self):
        self.login()
        self.driver.get(f'{self.live_server_url}/admin/census/request/')
        self.driver.find_element_by_css_selector(".row1 .action-select").click()
        dropdown = self.driver.find_element_by_name("action")
        dropdown.find_element_by_xpath("//option[. = 'Accept']").click()
        self.driver.find_element_by_name("index").click()
        self.assertEquals(self.driver.find_element_by_css_selector(".row1 .field-request_status").text, "ACCEPTED")
        
    def test_accept_private_request_check_delete_others(self):
        self.login()
        self.driver.get(f'{self.live_server_url}/admin/census/request/')
        self.driver.find_element_by_css_selector(".row1 .action-select").click()
        dropdown = self.driver.find_element_by_name("action")
        dropdown.find_element_by_xpath("//option[. = 'Accept']").click()
        self.driver.find_element_by_name("index").click()
        rows = self.driver.find_elements_by_xpath("//table/tbody/tr")
        self.assertEquals(len(rows), 1)

    def test_reject_private_request(self):
        self.login()
        self.driver.get(f'{self.live_server_url}/admin/census/request/')
        self.driver.find_element_by_css_selector(".row1 .action-select").click()
        dropdown = self.driver.find_element_by_name("action")
        dropdown.find_element_by_xpath("//option[. = 'Reject']").click()
        self.driver.find_element_by_name("index").click()
        self.assertEquals(self.driver.find_element_by_css_selector(".row1 .field-request_status").text, "REJECTED")
        
    def test_reject_private_request_check_delete_others(self):
        self.login()
        self.driver.get(f'{self.live_server_url}/admin/census/request/')
        self.driver.find_element_by_css_selector(".row1 .action-select").click()
        dropdown = self.driver.find_element_by_name("action")
        dropdown.find_element_by_xpath("//option[. = 'Reject']").click()
        self.driver.find_element_by_name("index").click()
        rows = self.driver.find_elements_by_xpath("//table/tbody/tr")
        self.assertEquals(len(rows), 1)
        
        
class NegativeRequestSeleniumTestCase(SeleniumBaseTestCase):    

    def setUp(self):

        u1 = User(username='username1Grupo1', password='password')
        u1.save()

        pg1 = ParentGroup(name='Grupo 1', pk=100, isPublic=True)
        pg1.save()

        rq1 = Request(voter_id=u1.pk, group_id=100)
        rq1.save()

        return super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_accept_private_request(self):
        self.login()
        self.driver.get(f'{self.live_server_url}/admin/census/request/')
        self.driver.find_element_by_css_selector(".row1 .action-select").click()
        dropdown = self.driver.find_element_by_name("action")
        dropdown.find_element_by_xpath("//option[. = 'Accept']").click()
        self.driver.find_element_by_name("index").click()
        self.assertEquals(self.driver.find_element_by_css_selector(".row1 .field-request_status").text, "PENDING")
        
    def test_reject_private_request(self):
        self.login()
        self.driver.get(f'{self.live_server_url}/admin/census/request/')
        self.driver.find_element_by_css_selector(".row1 .action-select").click()
        dropdown = self.driver.find_element_by_name("action")
        dropdown.find_element_by_xpath("//option[. = 'Reject']").click()
        self.driver.find_element_by_name("index").click()
        self.assertEquals(self.driver.find_element_by_css_selector(".row1 .field-request_status").text, "PENDING")