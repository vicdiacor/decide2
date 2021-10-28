from locust import HttpUser, task

class locust_test(HttpUser):
    @task
    def load_test(self):
        self.client.get('/admin')
        self.client.get('/mixnet')
        self.client.get('/voting')