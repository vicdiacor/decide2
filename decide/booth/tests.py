from django.test import TestCase
from time import sleep
from base.tests import SeleniumBaseTestCase
from store.models import Vote
from voting.models import Voting, Question, QuestionOption
from mixnet.models import Auth
from django.conf import settings
from django.contrib.auth.models import User
from census.models import Census
from django.utils import timezone
from local_settings import BASEURL
from django.contrib.auth.models import User, Group
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


class SeleniumTestCase(SeleniumBaseTestCase):


    def setUp(self):
        
        a = Auth(name='prueba', url=self.live_server_url, me=True)
        a.save()

        q = Question(desc='pregunta SO',type='SO')
        q.save()
        opt1 = QuestionOption(question=q, option='opcion 1',number=1)
        opt1.save()
        opt2 = QuestionOption(question=q, option='opcion 2',number=2)
        opt2.save()


        g1 = Group(name='Grupo 1', pk=100)
        g1.save()


        u1 = User(username='username1Grupo1', pk= 101)
        u1.set_password('password')
        u1.is_active= True
        u1.save()
        u1.groups.set([g1])
        u1.save()

        
        v = Voting(name='Voting SO', question=q, pk= 500, desc="Description")
        v.save()
        v.auths.add(a)
        v.save()


        c = Census(voter_id=u1.id, voting_id=v.id, adscripcion= "awadwadd")
        c.save()

       
        
        return super().setUp()    

    def tearDown(self):
        super().tearDown()
    
        
    def test_booth_single_option_vote(self):

        # Accedemos a la votación antes de que empiece
        
        self.driver.get("{}/booth/{}".format(self.live_server_url,500))
        heading1 = self.driver.find_element_by_tag_name('h1').text
        self.assertEquals(heading1,'Not Found')
    
        # Iniciamos las votaciones
        self.login()
        self.driver.find_element_by_link_text('Votings').click()
      
        self.driver.find_element_by_id('action-toggle').click()
        
        select = Select(self.driver.find_element_by_name('action'))
        select.select_by_visible_text('Start')
        self.driver.find_element_by_class_name('actions').find_element_by_class_name('button').click()
        self.driver.find_element_by_link_text('TERMINAR SESIÓN').click()


        # Intentamos acceder a la votación una vez haya comenzado
        self.driver.get("{}/booth/{}".format(self.live_server_url,500))


        # El usuario se logea
        self.driver.find_element_by_id('username').send_keys('username1Grupo1')
        self.driver.find_element_by_id('password').send_keys('password',Keys.ENTER)
        
        # El usuario selecciona una opción y pulsa en votar

        wait = WebDriverWait(self.driver, 10)

        wait.until(EC.element_to_be_clickable((By.XPATH,"//input[@id='q2']"))).click()
        self.driver.find_element_by_class_name('btn-primary').click()
       
        mensaje_exito= str(wait.until(EC.presence_of_element_located((By.XPATH,"//div[@role='alert']"))).text).strip()
        self.assertEquals(mensaje_exito,'× Conglatulations. Your vote has been sent')
        self.driver.find_element_by_xpath("//button[@class='close']").click()

        # El usuario intenta votar otra vez
        wait.until(EC.element_to_be_clickable((By.XPATH,"//input[@id='q1']"))).click()
        self.driver.find_element_by_class_name('btn-primary').click()
        mensaje_no_autorizado= str(wait.until(EC.presence_of_element_located((By.XPATH,"//div[@role='alert']"))).text).strip()
        self.assertEquals(mensaje_no_autorizado,'× Error: Unauthorized')

        # Comprobamos que se ha creado un único voto correctamnete
        self.login()
        self.driver.find_element_by_link_text('Votes').click()
        votes_sent= self.driver.find_elements_by_link_text('500: 101')
        self.assertEquals(len(votes_sent), 1)
        
        votes_sent[0].click()
        voting_id= self.driver.find_element_by_xpath("//input[@id='id_voting_id']").get_attribute('value')
        voter_id= self.driver.find_element_by_xpath("//input[@id='id_voter_id']").get_attribute('value')
        a_encrypted= self.driver.find_element_by_xpath("//textarea[@id='id_a']").text
        b_encrypted= self.driver.find_element_by_xpath("//textarea[@id='id_b']").text

        self.assertEquals(voting_id,"500")
        self.assertEquals(voter_id,"101")
        self.assertTrue(a_encrypted!="")
        self.assertTrue(b_encrypted!="")







