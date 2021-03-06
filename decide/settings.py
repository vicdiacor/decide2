import django_heroku
ALLOWED_HOSTS = ["*"]

# Modules in use, commented modules that you won't use
MODULES = [
    'authentication',
    'base',
    'booth',
    'census',
    'mixnet',
    'postproc',
    'store',
    'visualizer',
    'voting',
]

APIS = {
    'authentication': 'https://egc-part-chullo-decide.herokuapp.com/',
    'base': 'https://egc-part-chullo-decide.herokuapp.com/',
    'booth': 'https://egc-part-chullo-decide.herokuapp.com/',
    'census': 'https://egc-part-chullo-decide.herokuapp.com/',
    'mixnet': 'https://egc-part-chullo-decide.herokuapp.com/',
    'postproc': 'https://egc-part-chullo-decide.herokuapp.com/',
    'store': 'https://egc-part-chullo-decide.herokuapp.com/',
    'visualizer': 'https://egc-part-chullo-decide.herokuapp.com/',
    'voting': 'https://egc-part-chullo-decide.herokuapp.com/',
}

BASEURL =  'https://egc-part-chullo-decide.herokuapp.com/'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'decidedb',
        'USER': 'decide1',
        'HOST': 'localhost',
        'PASSWORD': 'decide1',
        'PORT': '5432',
    }
}

# number of bits for the key, all auths should use the same number of bits
KEYBITS = 256

django_heroku.settings(locals())