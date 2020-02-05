from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from .forms import FormOne, FormTwo
from .models import Applicant
from django.views import generic

class ApplicantListView(generic.ListView):
    pass

def FormTwoView(request):
    formtwo = FormTwo()
    if request.method == 'POST':
        formtwo = FormTwo(request.POST)

        if formtwo.is_valid():
            experience = formtwo.cleaned_data.get('experience')
            why_aims = formtwo.cleaned_data.get('why_aims')
            # make a model out of all the available applicant data
            form_data = request.session['form_data']
            Applicant_obj = Applicant.objects.create(
                    email = form_data['email'],
                    name = form_data['name'],
                    phone_number = form_data['phone_number'],
                    clubs = form_data['clubs'],
                    city = form_data['city'],
                    address = form_data['address'],
                    experience = experience,
                    why_aims = why_aims,
            )
            Applicant_obj.save()
            return redirect('accepted_view')

    else :
        formtwo = FormTwo()
    
    context = {
        'form' : formtwo,
    }
    return render(request, 'userlogin/formtwo.html', context)

def FormOneView(request):
    formone = FormOne()
    if request.method == 'POST':
        formone = FormOne(request.POST)
        
        if formone.is_valid():
            email = formone.cleaned_data.get('email')
            name = formone.cleaned_data.get('name')
            phone_number = formone.cleaned_data.get('phone_number')
            clubs = formone.cleaned_data.get('clubs')
            city = formone.cleaned_data.get('city')
            address = formone.cleaned_data.get('address')
            print("clubs = ", clubs)
            print("city = ", city)
            print(type(city))
            if clubs == 'Other' or city == 'Other':
                return render(request, 'userlogin/rejected.html')
            else :
                form_data = {
                    'name' : name,
                    'email' : email,
                    'phone_number' : phone_number,
                    'clubs' : clubs,
                    'city' : city,
                    'address' : address,
                }
                request.session['form_data'] = form_data
                return redirect('form_two_view')
                # return render(request, 'userlogin/accepted.html')
    else:
        formone = FormOne()
    
    context = {
        'form' : formone,
    }
    return render(request, 'userlogin/formone.html', context)

def RejectedView(request):
    return render(request, 'userlogin/rejected.html')

def AcceptedView(request):
    return render(request, 'userlogin/accepted.html')


def index(request):
    return render(request, 'userlogin/index.html')

def RegisterView(request):
    form = UserCreationForm(request.POST)
    if form.is_valid():
        form.save()
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=password)
        login(request, user)
        return redirect('index_page')
    return render(request, 'userlogin/register.html', {'form': form})
