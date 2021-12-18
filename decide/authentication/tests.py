from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.test import APITestCase

from http import HTTPStatus

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from base import mods
from base.tests import SeleniumBaseTestCase
from selenium.webdriver.common.by import By
from django.contrib import auth


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
        
    def test_selenium_correct_registration_and_login(self):
        self.driver.get(f"{self.live_server_url}/authentication/registrarse/")
        self.driver.find_element(By.ID, "id_username").send_keys("testuser")
        self.driver.find_element(By.ID, "id_first_name").send_keys("test")
        self.driver.find_element(By.ID, "id_last_name").send_keys("prueba")
        self.driver.find_element(By.ID, "id_email").send_keys("prueba@gmail.com")
        self.driver.find_element(By.ID, "id_password1").send_keys("decide1234")
        self.driver.find_element(By.ID, "id_password2").send_keys("decide1234")
        self.driver.find_element_by_xpath('//button["Registrarse"]').click()
        
        user = User.objects.get(username='testuser')
        self.assertTrue(user.is_authenticated)
        
        self.driver.find_element(By.XPATH, '//a["Cerrar sesión"]')
        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated)
        
        self.driver.get(f"{self.live_server_url}/authentication/iniciar_sesion/")
        self.driver.find_element(By.ID, "id_username").send_keys("testuser")
        self.driver.find_element(By.ID, "id_password").send_keys("decide1234")
        self.driver.find_element_by_xpath('//button["Inicie sesión"]').click()
        
        user = User.objects.get(username='testuser')
        self.assertTrue(user.is_authenticated)
        
        
    def test_selenium_different_passwords(self):
        self.driver.get(f"{self.live_server_url}/authentication/registrarse/")
        self.driver.find_element(By.ID, "id_username").send_keys("testuser")
        self.driver.find_element(By.ID, "id_first_name").send_keys("test")
        self.driver.find_element(By.ID, "id_last_name").send_keys("prueba")
        self.driver.find_element(By.ID, "id_email").send_keys("prueba@gmail.com")
        self.driver.find_element(By.ID, "id_password1").send_keys("decide1234")
        self.driver.find_element(By.ID, "id_password2").send_keys("decide1235")
        self.driver.find_element_by_xpath('//button["Registrarse"]').click()
        
        self.driver.find_element_by_xpath('//p["Los dos campos de contraseña no coinciden."]')
        
    def test_selenium_username_already_exists(self):
        self.driver.get(f"{self.live_server_url}/authentication/registrarse/")
        self.driver.find_element(By.ID, "id_username").send_keys("testuser")
        self.driver.find_element(By.ID, "id_first_name").send_keys("test")
        self.driver.find_element(By.ID, "id_last_name").send_keys("prueba")
        self.driver.find_element(By.ID, "id_email").send_keys("prueba@gmail.com")
        self.driver.find_element(By.ID, "id_password1").send_keys("decide1234")
        self.driver.find_element(By.ID, "id_password2").send_keys("decide1234")
        self.driver.find_element_by_xpath('//button["Registrarse"]').click()
        
        user = User.objects.get(username='testuser')
        self.assertTrue(user.is_authenticated)
        
        self.driver.find_element(By.XPATH, '//a["Cerrar sesión"]')
        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated)
        
        self.driver.get(f"{self.live_server_url}/authentication/registrarse/")
        self.driver.find_element(By.ID, "id_username").send_keys("testuser")
        self.driver.find_element(By.ID, "id_first_name").send_keys("test")
        self.driver.find_element(By.ID, "id_last_name").send_keys("prueba")
        self.driver.find_element(By.ID, "id_email").send_keys("prueba1@gmail.com")
        self.driver.find_element(By.ID, "id_password1").send_keys("decide1234")
        self.driver.find_element(By.ID, "id_password2").send_keys("decide1234")
        self.driver.find_element_by_xpath('//button["Registrarse"]').click()
        
        self.driver.find_element_by_xpath('//p["Ya existe un usuario con este nombre."]')  
        
class IniciarSesionTestCase(TestCase):
    
    def setUp(self):
        
        self.credentials = {
            'username': 'testuser',
            'password': 'decide1234'}
        User.objects.create_user(**self.credentials)
        
    def tearDown(self):
        self.client = None
        
    def test_get_form(self):
        response = self.client.get("/authentication/iniciar_sesion/")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "<h2>Inicie sesión en DECIDE</h2>", html=True)
    
    def test_post_form(self):
        response = self.client.post("/authentication/iniciar_sesion/", data={"username": "testuser", "password": "decide1234"})
        
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response["Location"], "/")

        user = User.objects.get(username='testuser')
        self.assertTrue(user.is_authenticated)
        
    def test_post_incorrect_form(self):
        #Mal usuario
        response = self.client.post("/authentication/iniciar_sesion/", data={"username": "testuser_error", "password": "decide1234"})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Por favor, introduzca un nombre de usuario y clave correctos. Observe que ambos campos pueden ser sensibles a mayúsculas.", html=True)
        
        #Mala contraseña
        response = self.client.post("/authentication/iniciar_sesion/", data={"username": "testuser_error", "password": "decide1234"})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Por favor, introduzca un nombre de usuario y clave correctos. Observe que ambos campos pueden ser sensibles a mayúsculas.", html=True)
        
        #Campos vacíos
        response = self.client.post("/authentication/iniciar_sesion/", data={"username": "", "password": ""})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "<h2>Inicie sesión en DECIDE</h2>", html=True)
        

class CerrarSesionTestCase(TestCase):
    
    def setUp(self):
        
        self.credentials = {
            'username': 'testuser',
            'password': 'decide1234'}
        User.objects.create_user(**self.credentials)
        
    def tearDown(self):
        self.client = None
        
    def test_cerrar_sesion(self):
        
        response = self.client.post("/authentication/iniciar_sesion/", data={"username": "testuser", "password": "decide1234"})
        
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response["Location"], "/")

        user = User.objects.get(username='testuser')
        self.assertTrue(user.is_authenticated)

        response = self.client.get("/authentication/cerrar_sesion/")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        
        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated)        
        
class RegistrarUsuarioTestCase(TestCase):
    
    def tearDown(self):
        self.client = None
        
    def test_good_registration(self):
        username_t="testuser"
        password_t="decide1234"
        try:
            user = User.objects.get(username="testuser")
            exists=True
        except User.DoesNotExist:
            exists=False
        
        self.assertFalse(exists)       
        
        response=self.client.get("/authentication/registrarse/")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        
        response=self.client.post("/authentication/registrarse/", data={"username": "testuser", "first_name": "testuser", "last_name": "testuser","email": "testuser@example.com","password1": "decide1234", "password2": "decide1234"})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response["Location"], "/")
        
        user = User.objects.get(username='testuser')
        self.assertTrue(user.is_authenticated)
        
    def test_wrong_registration(self):
        
        username_t="testuser"
        password_t="decide1234"
        try:
            user = User.objects.get(username="testuser")
            exists=True
        except User.DoesNotExist:
            exists=False
        
        self.assertFalse(exists)          
        
        #Campos vacíos
        response=self.client.post("/authentication/registrarse/", data={"username": "", "first_name": "", "last_name": "","email": "","password1": "", "password2": ""})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        
        #Solo username
        response=self.client.post("/authentication/registrarse/", data={"username": "testuser", "first_name": "", "last_name": "","email": "","password1": "", "password2": ""})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "<h2>Formulario de registro en DECIDE</h2>", html=True)
        
        #Solo username y first_name
        response=self.client.post("/authentication/registrarse/", data={"username": "testuser", "first_name": "testuser", "last_name": "","email": "","password1": "", "password2": ""})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "<h2>Formulario de registro en DECIDE</h2>", html=True)
        
        #Solo username, first_name y last_name
        response=self.client.post("/authentication/registrarse/", data={"username": "testuser", "first_name": "testuser", "last_name": "testuser","email": "","password1": "", "password2": ""})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "<h2>Formulario de registro en DECIDE</h2>", html=True)
       
        #Solo username, first_name, last_name y email
        response=self.client.post("/authentication/registrarse/", data={"username": "testuser", "first_name": "testuser", "last_name": "testuser","email": "","password1": "", "password2": ""})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "<h2>Formulario de registro en DECIDE</h2>", html=True)
        
        #Sin password2
        response=self.client.post("/authentication/registrarse/", data={"username": "testuser", "first_name": "testuser", "last_name": "testuser","email": "prueba@gmail.com","password1": "decide1234", "password2": ""})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "<h2>Formulario de registro en DECIDE</h2>", html=True)
        
        #Sin password2 --> Mirar en internet como comprobar error de form
        response=self.client.post("/authentication/registrarse/", data={"username": "testuser", "first_name": "testuser", "last_name": "testuser","email": "prueba@gmail.com","password1": "decide1234", "password2": "decide1235"})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "<h2>Formulario de registro en DECIDE</h2>", html=True)
        
        #Mal email
        response=self.client.post("/authentication/registrarse/", data={"username": "testuser", "first_name": "testuser", "last_name": "testuser","email": "prueba","password1": "decide1234", "password2": "decide1234"})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "<h2>Formulario de registro en DECIDE</h2>", html=True)
        
        #Usuario ya registrado --> Mirar en internet como comprobar error de form
        response=self.client.post("/authentication/registrarse/", data={"username": "testuser", "first_name": "testuser", "last_name": "testuser","email": "testuser@example.com","password1": "decide1234", "password2": "decide1234"})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response["Location"], "/")
        
        user = User.objects.get(username='testuser')
        self.assertTrue(user.is_authenticated)
        
        response=self.client.post("/authentication/registrarse/", data={"username": "testuser", "first_name": "testuser", "last_name": "testuser","email": "prueba@gmail.com","password1": "decide1234", "password2": "decide1234"})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "<h2>Formulario de registro en DECIDE</h2>", html=True)
