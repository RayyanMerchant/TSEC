from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from .forms import FormOne, FormTwo, DecisionForm, AttendanceForm
from .models import Applicant, Absent, School
from django.views import generic
from django.contrib import messages
from . whatsapp import func
import smtplib, ssl, time
from geopy.geocoders import Nominatim
import random, math

def MessageView(request):
    schools = School.objects.all()
    for school in schools:
        queryset = Applicant.objects.filter(school=school).order_by('clubs')
        message = ""
        for cur in queryset:
            if cur.score < 1:
                continue
            if not Absent.objects.filter(email=cur.email):
                message += cur.clubs + "  " + cur.name + "  " + cur.phone_number + "\n"
            else:
                message += "----------------------------------------"
        
        """
        here we are assuming the whatsapp group to have the same name as the school name
        """
        if message:
            func('Test', message)
    
    
    return redirect('dashboard')

def calc_dist(lat1, lon1, lat2, lon2):
    lat1 = math.radians(lat1)
    lon1 = math.radians(lat1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)
    
    phi1 = lat1
    phi2 = lat2
    delta_phi = lat2 - lat1
    delta_lambda = lon2 - lon1

    a = (math.sin(delta_phi/2) * math.sin(delta_phi/2)) + (math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2) * math.sin(delta_lambda/2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    R = 6371
    dist = R  * c
    return dist

def SchoolSelectionView(request, pk):
    try:
        applicant = Applicant.objects.get(pk=pk)
    except Applicant.DoesNotExist:
        raise Http404('Applicant does not exist')

    address = applicant.address
    geolocator = Nominatim(user_agent="specify_your_app_name_here")
    cur_location = geolocator.geocode(address)
    
    user_x = cur_location.latitude
    user_y = cur_location.longitude   
    schools = School.objects.all()
    city = ['Diamond Jubilee', 'Christ Church', 'Don Bosco', 'St.Peters', 'Campion', 'St.Marys']
    a = [19.0760,18.5204,17.6805,18.7557,17.9307, 19.9975]
    b = [72.8777,73.8567,74.0183,73.4091,73.6477, 73.7898]
    mn = 10 ** 18
    closest = 0
    dist = mn
    for i in range(6):
        cur = calc_dist(user_x, user_y, a[i], b[i])
        if cur < mn:
            mn = cur
            closest = i
            dist = mn
    
    queryset = School.objects.filter(name=city[closest])
    applicant.school = queryset[0]
    applicant.save()
    print("queryset[0] = ", queryset[0])
    print("city[closest] = ", city[closest])
    context = {
        'user_x' : user_x,
        'user_y' : user_y,
        'closest' : city[closest],
        'dist' : dist,
    }
    return render(request, 'userlogin/school_selection.html', context)

def DisplayAbsentView(request):
    schools = School.objects.all()
    dic = {}
    for school in schools:
        cnt = Absent.objects.filter(school=school).count()
        
        if cnt > 0:
            dic[school.name] = cnt
            print(school.name)
            print(cnt)
    
    context = {
        'queryset' : dic,
    }
    return render(request, 'userlogin/absent.html', context)

def AttendanceView(request):
    attendance_form = AttendanceForm()

    if request.method == 'POST':
        attendance_form = AttendanceForm(request.POST)
        if attendance_form.is_valid():
            email = attendance_form.cleaned_data.get('email')
            applicant_obj = Applicant.objects.filter(email=email)
            absent_obj = Absent(name=applicant_obj[0].name, email=applicant_obj[0].email, school=applicant_obj[0].school)
            absent_obj.save()
            attendance_form = AttendanceForm()
            messages.success(request, "Your response has been recorded")

    else:
        attendance_form = AttendanceForm()

    context = {
        'form' : attendance_form,
    }
    return render(request, 'userlogin/attendance.html', context)


def ApplicantListView(request):
    queryset = Applicant.objects.filter(score=-1)
    context = {
        'applicant_list' : queryset,
        'title' : 'Applicant List',
    }
    return render(request, 'userlogin/applicant_list.html', context)  


def PhoneInterviewView(request):
    queryset = Applicant.objects.filter(score=0)
    context = {
        'applicant_list' : queryset,
        'title' : 'Phone Interview List',
    }
    return render(request, 'userlogin/applicant_list.html', context)    


def FinalSelectedView(request):
    queryset = Applicant.objects.filter(score=1)
    context = {
        'applicant_list' : queryset,
        'title' : 'Final List/ School Selection',
    }
    return render(request, 'userlogin/applicant_list.html', context)

def ApplicantDetailView(request, pk):
    try:
        applicant = Applicant.objects.get(pk=pk)
    except Applicant.DoesNotExist:
        raise Http404('Applicant does not exist')
    decision_form = DecisionForm()
    
    if request.method == 'POST' :
        decision_form = DecisionForm(request.POST)
        if decision_form.is_valid():
            decision = decision_form.cleaned_data.get('decision')
            print('decision = ', decision)

            redirect_url = ""
            success_message = "generic congrats message"
            if applicant.score == -1:
                redirect_url = 'applicant_list_view'
                success_message = "Congratulations!!! You have passed the first stage. We will contact you about the phone interview timings soon"
            elif applicant.score == 0:
                redirect_url = 'phone_interview_view'
                success_message = "Congratulations!!! You have cleared the phone interview and are selected. We will contact you about the school selection procedure soon"
            elif applicant.score == 1:
                redirect_url = 'final_selected_view'

            print('redirect_url = ', redirect_url)
            if decision == 'Accept':
                applicant.score += 1
                applicant.save()
                # send accepted email
                sendymaily(success_message, applicant.email)

            else :
                applicant.score = -2
                applicant.save()
                failure = "Sorry to infrom you but your application has been rejected. Please consider applying again later"
                #send rejected email
                sendymaily(failure, applicant.email)

            return redirect(redirect_url)
    else:
        decision_form = DecisionForm()

    context = {
        'applicant': applicant,
        'form' : decision_form
    }
    return render(request, 'userlogin/applicant_detail.html', context)



def sendymaily(message, receiver):
    sender = 'sauravjoshi2362000@gmail.com'
    password = 'maxverstappen@33'  
    port = 465

    recieve = receiver
    context = ssl.create_default_context()
    print("Starting to send")
    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(sender, password)
        server.sendmail(sender, recieve, message)

    print("sent email!")


def testing(request):
    
    queryset = School.objects.all()

    context = {
        'queryset' : queryset,
    }
    return render(request, "userlogin/testing.html", context)


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

def dashboard(request):
    return render(request, 'userlogin/dashboard.html')

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
