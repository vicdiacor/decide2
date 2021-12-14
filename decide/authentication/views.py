from django.shortcuts import render, redirect
from decide import settings

from django.contrib.auth.forms import AuthenticationForm

from authentication.forms import SignUpForm
from django.contrib.auth import login, authenticate, logout

def registro(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(request, username=username, password=raw_password)
            login(request, user)

            return redirect(inicio)
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form, 'STATIC_URL':settings.STATIC_URL})    

def inicio(request):
    return render(request, 'inicio.html', {'STATIC_URL':settings.STATIC_URL})

def cerrar_sesion(request):
    logout(request)
    return render(request, 'inicio.html', {'STATIC_URL':settings.STATIC_URL})

def iniciar_sesion(request):
    if request.method == "POST":
        form = AuthenticationForm(request.POST)
        if form.is_valid():
            username=form.cleaned_data.get('username')
            password=form.cleaned_data.get('password1')
            user=authenticate(request, username,password)
            if user is not None:
                login(request, user)
                return redirect(inicio)
    
    else:
        form=AuthenticationForm()
    return render(request, 'signin.html', {'form': form, 'STATIC_URL':settings.STATIC_URL})    

# class GetUserView(APIView):
#     def post(self, request):
#         key = request.data.get('token', '')
#         tk = get_object_or_404(Token, key=key)
#         return Response(UserSerializer(tk.user, many=False).data)


# class LogoutView(APIView):
#     def post(self, request):
#         key = request.data.get('token', '')
#         try:
#             tk = Token.objects.get(key=key)
#             tk.delete()
#         except ObjectDoesNotExist:
#             pass

#         return Response({})


# class RegisterView(APIView):
#     def post(self, request):
#         key = request.data.get('token', '')
#         tk = get_object_or_404(Token, key=key)
#         if not tk.user.is_superuser:
#             return Response({}, status=HTTP_401_UNAUTHORIZED)

#         username = request.data.get('username', '')
#         pwd = request.data.get('password', '')
#         if not username or not pwd:
#             return Response({}, status=HTTP_400_BAD_REQUEST)

#         try:
#             user = User(username=username)
#             user.set_password(pwd)
#             user.save()
#             token, _ = Token.objects.get_or_create(user=user)
#         except IntegrityError:
#             return Response({}, status=HTTP_400_BAD_REQUEST)
#         return Response({'user_pk': user.pk, 'token': token.key}, HTTP_201_CREATED)
