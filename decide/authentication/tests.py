from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.test import APITestCase

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from selenium.webdriver.chrome import options

from base import mods
from base.tests import SeleniumBaseTestCase
from selenium.webdriver.common.by import By
from django.contrib.auth.models import User, Group
from selenium.webdriver.support.ui import Select
import os
import time
import openpyxl


class AuthTestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()
        mods.mock_query(self.client)
        u = User(username='voter1')
        u.set_password('123')
        u.save()

        u2 = User(username='admin')
        u2.set_password('admin')
        u2.is_superuser = True
        u2.save()

    def tearDown(self):
        self.client = None

    def test_login(self):
        data = {'username': 'voter1', 'password': '123'}
        response = self.client.post('/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)

        token = response.json()
        self.assertTrue(token.get('token'))

    def test_login_fail(self):
        data = {'username': 'voter1', 'password': '321'}
        response = self.client.post('/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 400)

    def test_getuser(self):
        data = {'username': 'voter1', 'password': '123'}
        response = self.client.post('/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)
        token = response.json()

        response = self.client.post('/authentication/getuser/', token, format='json')
        self.assertEqual(response.status_code, 200)

        user = response.json()
        self.assertEqual(user['id'], 1)
        self.assertEqual(user['username'], 'voter1')

    def test_getuser_invented_token(self):
        token = {'token': 'invented'}
        response = self.client.post('/authentication/getuser/', token, format='json')
        self.assertEqual(response.status_code, 404)

    def test_getuser_invalid_token(self):
        data = {'username': 'voter1', 'password': '123'}
        response = self.client.post('/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Token.objects.filter(user__username='voter1').count(), 1)

        token = response.json()
        self.assertTrue(token.get('token'))

        response = self.client.post('/authentication/logout/', token, format='json')
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/authentication/getuser/', token, format='json')
        self.assertEqual(response.status_code, 404)

    def test_logout(self):
        data = {'username': 'voter1', 'password': '123'}
        response = self.client.post('/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Token.objects.filter(user__username='voter1').count(), 1)

        token = response.json()
        self.assertTrue(token.get('token'))

        response = self.client.post('/authentication/logout/', token, format='json')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Token.objects.filter(user__username='voter1').count(), 0)

    def test_register_bad_permissions(self):
        data = {'username': 'voter1', 'password': '123'}
        response = self.client.post('/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)
        token = response.json()

        token.update({'username': 'user1'})
        response = self.client.post('/authentication/register/', token, format='json')
        self.assertEqual(response.status_code, 401)

    def test_register_bad_request(self):
        data = {'username': 'admin', 'password': 'admin'}
        response = self.client.post('/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)
        token = response.json()

        token.update({'username': 'user1'})
        response = self.client.post('/authentication/register/', token, format='json')
        self.assertEqual(response.status_code, 400)

    def test_register_user_already_exist(self):
        data = {'username': 'admin', 'password': 'admin'}
        response = self.client.post('/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)
        token = response.json()

        token.update(data)
        response = self.client.post('/authentication/register/', token, format='json')
        self.assertEqual(response.status_code, 400)

    def test_register(self):
        data = {'username': 'admin', 'password': 'admin'}
        response = self.client.post('/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)
        token = response.json()

        token.update({'username': 'user1', 'password': 'pwd1'})
        response = self.client.post('/authentication/register/', token, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            sorted(list(response.json().keys())),
            ['token', 'user_pk']
        )

class SeleniumTestCase(SeleniumBaseTestCase):

    def setUp(self):
        g1 = Group(name='Grupo 1', pk=100)
        g1.save()

        u1 = User(username='username1', password='password')
        u1.save()
        u1.groups.set([g1])
        u1.save()

        u2 = User(username='username2', password='password')
        u2.save()
        u2.groups.set([g1])
        u2.save()

        u3 = User(username='username3', password='password')
        u3.save()
        u3.groups.set([g1])
        u3.save()

        u4 = User(username='username4', password='password')
        u4.save()
        u4.groups.set([g1])
        u4.save()


        u5 = User(username='username5', password='password')
        u5.save()
        u5.groups.set([g1])
        u5.save()

        return super().setUp()



    def test_simpleCorrectLogin(self):
        self.login()
        #In case of a correct loging, a element with id 'user-tools' is shown in the upper right part
        self.assertTrue(len(self.driver.find_elements_by_id('user-tools'))==1)

    def test_incorrect_login(self):        
        self.login('notanuser', 'notapassword')

        self.assertFalse(len(self.driver.find_elements_by_id('user-tools'))==1)
    
    def test_selenium_extension(self):
        self.driver.get(f"{self.live_server_url}/admin/login/?next=/admin/")
        self.driver.set_window_size(909, 1016)
        self.driver.find_element(By.ID, "id_username").send_keys("admin")
        self.driver.find_element(By.ID, "id_password").send_keys("qwerty")
        self.driver.find_element(By.CSS_SELECTOR, ".submit-row > input").click()
        
        self.assertEquals(self.driver.current_url, f'{self.live_server_url}/admin/')
        self.driver.close()


    def test_import_group(self):
        self.driver.get(f"{self.live_server_url}/authentication/groups/import/")
        self.driver.find_element_by_id('id_name').send_keys('Grupo 2')
        self.driver.find_element_by_id('id_file').send_keys(os.getcwd() + "/authentication/files/testfiles/testgroup1.txt")
        self.driver.find_element_by_xpath("//input[@value='Importar']").click()

        self.driver.find_element_by_class_name('success')

        self.driver.find_element_by_id('id_name').send_keys('Grupo 3')
        self.driver.find_element_by_id('id_file').send_keys(os.getcwd() + "/authentication/files/testfiles/testgroup1.xlsx")
        self.driver.find_element_by_xpath("//input[@value='Importar']").click()

        self.driver.find_element_by_class_name('success')

        # Comprueba que existen 3 grupos (setUp + 2 grupos creados)
        self.login()
        self.driver.get(f"{self.live_server_url}/admin/auth/group/")
        self.assertEquals(len(self.driver.find_elements_by_class_name(name='field-__str__')), 3)


    # Prueba si se introduce un nombre de grupo ya existente
    def test_import_wrong_group_name(self):
        self.driver.get(f"{self.live_server_url}/authentication/groups/import/")
        self.driver.find_element_by_id('id_name').send_keys('Grupo 1')
        self.driver.find_element_by_id('id_file').send_keys(os.getcwd() + "/authentication/files/testfiles/testgroup1.txt")
        self.driver.find_element_by_xpath("//input[@value='Importar']").click()

        # Comprueba que aparece un mensaje de error
        self.driver.find_element_by_class_name('error')


    # Prueba si se introduce un fichero con un username que no existe
    def test_import_wrong_username(self):
        self.driver.get(f"{self.live_server_url}/authentication/groups/import/")
        self.driver.find_element_by_id('id_name').send_keys('Grupo 2')
        self.driver.find_element_by_id('id_file').send_keys(os.getcwd() + "/authentication/files/testfiles/testgroup2.txt")
        self.driver.find_element_by_xpath("//input[@value='Importar']").click()

        # Comprueba que aparece un mensaje de error
        self.driver.find_element_by_class_name('error')



    def test_export_group(self):
        self.driver.get(f"{self.live_server_url}/authentication/groups/export/")
        select = Select(self.driver.find_element_by_id('id_group'))
        select.select_by_visible_text('Grupo 1')
        self.driver.find_element_by_xpath("//input[@value='Exportar']").click()

        # Espero a que termine la descarga
        time.sleep(3)
        # Obtenemos la ruta de descarga
        #download_file_path = os.path.join(os.path.expanduser('~'), 'Descargas/export_group.xlsx') 
        # Compruebo si el fichero existe
        self.assertEquals(os.path.exists('export_group.xlsx'), True)

        # Compruebo si todos los usuarios del grupo están
        workbook = openpyxl.load_workbook('export_group.xlsx')
        sheet = workbook.active

        # Lee el excel y almacena en username_list los nombres de usuario
        usernames = ['username1', 'username2', 'username3', 'username4', 'username5']
        max_row = sheet.max_row
        for i in range(1, max_row+ 1):
            cell = sheet.cell(row = i, column = 1)
            self.assertEquals(cell.value in usernames, True)

        # Eliminamos el fichero descargado
        os.remove("export_group.xlsx") 




