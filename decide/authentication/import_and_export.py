from os import name
from django.contrib.auth.models import User, Group


# Dado un fichero txt con un nombre de usuario en cada línea, devuelve una lista de usuarios o null si alguno de los usuarios indicados no existen.
def readTxtFile(file):
    list = []
    file_str = file.read().decode('utf-8')
    for line in file_str.split('\n'):
        try:
            # Saltamos líneas en blanco.
            if (line.strip()!=''): 
                u = User.objects.get(username=line.strip())
                list.append(u)
        except:
            print('It does not exist a user with username ' + line.strip()) 
            return None

    return list


# Dado un nombre y una lista de usuarios, devuelve True si crea un nuevo grupo y False si el grupo ya existe. 
def createGroup(name, user_list):
    g, is_created = Group.objects.get_or_create(name=name)
    if (is_created==False):
        return False

    for u in user_list:
        g.user_set.add(u)

    return True
