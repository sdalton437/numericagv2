#from django.shortcuts import render
from django.shortcuts import render, redirect,get_object_or_404,render_to_response

from statistics import mean, stdev,variance

from ..models import UserRquestSite,UserTransaction,PlotYield,SiteField,dsslookup,UserInputPreference
#from django.db.models import Q

import csv
from django.http import HttpResponse,HttpResponseRedirect
from django.conf import settings as djangoSettings
#from django_pandas.io import read_frame
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required

from ..scripts import UserOperations, OnlineResourcesFinder
from django.contrib.auth import authenticate, login
from django.conf import settings
from django.contrib import messages
from django.db import transaction,IntegrityError

app_name = 'passapp'


def confirmUser(request,id):

    user=UserOperations.userActivation(id)
    if user is not None:
        print('rendering user account confirmation page')
        return render(request, 'registration/confirmation.html')
    else:
        messages.error(request, 'Could not find account with the user, please register here!')
        return render(request, 'registration/registration.html')

def registerUser(request):


    firstname= request.POST.get('firstname', '')
    lastname= request.POST.get('lastname', '')
    email= request.POST.get('email', '')
    password= request.POST.get('password', '')
    passwordconfirm =  request.POST.get('passwordconfirm', '')

    if not passwordconfirm == password:
        messages.error(request,'password does not match with confirm password, please try again ')
        return render(request, 'registration/registration.html')

    print('firstname : '+ firstname)
    print('lastname : '+ lastname)
    print('email : '+ email)

    try:
        user=UserOperations.findUserbyUsername(email)
        if user is not None:
            messages.error(request, "User Email already exist, please try with another email id")
            return render(request, 'registration/registration.html')
    except:
       pass

    user=UserOperations.createUser(firstname,email,lastname,password)

    print("usercreation successfull ")

    #send verification email to cofirm user.
    link= str(request.get_host()) +'/'+ str(user.id)+'/confirmUser'
    print('link: '+ link)
    UserOperations.sendVerificationEmail(user, link)
    # print('host: ' + str(request.get_host()))
    # print('ful path ' + request.get_full_path())
    # print(' raw uri ' + request.get_raw_uri())

    messages.info (request, "Your are successfully registered,please verify your email to login")

    return render(request, 'registration/login.html')

def signup(request):

    return render(request, 'registration/registration.html')

def signin(request):

    return render(request, 'registration/login.html')

def logoutUser(request):

    logout(request)
    try:
        del request.session['username']
        del request.session['userid']
    except KeyError:
        pass
    # Redirect to a success page.
    print('Successfully Logged out')
    messages.info (request, "Your are successfully logged out, login here again !")
    return render(request, 'registration/login.html')

''' verify user credentials '''
def authenticateUser(request):

    if request.method == 'POST':
        print("Start, general Views,  authenticateUser()")
        password = request.POST.get('password','')
        username=request.POST.get('username','')
        print('user: '+username)
        user = authenticate(username=username, password=password)
        if user is not None:
            print('authenticated user : '+username)

            if UserOperations.isUserActive(username) is False:
                messages.error(request, "User email verification pending!, please verify")
                return render(request, 'registration/login.html')

            if not request.POST.get('remember_me', None):
                request.session.set_expiry(0)

            login(request, user)

            request.session['username'] = user.first_name
            request.session['userid'] = user.id
            request.session['isstaff'] = user.is_staff
            request.session['useremail'] = user.email
            print("login is successfull, redirecting to home page")
            request.session.set_expiry(1200)
            return redirect('index')

        else:

            messages.error(request, "Authentication failed, Invalid User, please try again !")
            print('Authentication failed, Invalid User')

    return render(request, 'registration/login.html')

@login_required()
def index(request):
    print('Start , generalviews, index()')
    # if not request.user.is_authenticated:
    #     print('use os not authenticated, please login')
    #     return redirect((settings.LOGIN_URL, request.path))

    if request.user.is_active == False:
        messages.error(request, "Activatioin pending, check your email and click on link given to activate!")

    ' commented  this, added the voptions manually in the home.html file as plotyield table containing the data is belong to dssservice module'
    # print('fetching basic input values from database')
    # latest_dataset_list = PDataset1.objects.all()
    # #tillTypes=latest_dataset_list.order_by('TillType').distinct('TillType')
    # tillTypes = PDataset1.objects.order_by('TillType').values('TillType').distinct() #PDataset1.objects.order_by('TillType').distinct('TillType')
    # # soilTypes = [] #PDataset1.objects.order_by('SoilType').distinct('SoilType') works only with PostgreSQL
    # soilTypes=PDataset1.objects.order_by('SoilType').values('SoilType').distinct() #MySQL + PostgreSQL
    # prevCrops = PDataset1.objects.order_by('PrevCrop').values('PrevCrop').distinct()#PDataset1.objects.order_by('PrevCrop').distinct('PrevCrop')
    # check if user input preferences are prsent for the user
    # user_preference=UserInputPreference.objects.filter(user=request.user)
    #
    # if not user_preference:
    #     # #user preference not present, fetch values from database and create default preference
    #
    from django.db.models import Max, Min
    dbTrials = PlotYield.objects.all()
    minCHU = dbTrials.aggregate(Min('CHU'))
    maxCHU = dbTrials.aggregate(Max('CHU'))
    minClayRatio = dbTrials.aggregate(Min('ClayRatio'))
    maxClayRAtio = dbTrials.aggregate(Max('ClayRatio'))
    minSOM = dbTrials.aggregate(Min('SOM'))
    maxSOM = dbTrials.aggregate(Max('SOM'))
    minAWDR = dbTrials.aggregate(Min('AWDR'))
    maxAWDR = dbTrials.aggregate(Max('AWDR'))
    maxPrevCrop = dbTrials.aggregate(Max('PrevContribN_int'))
    minPrevCrop = dbTrials.aggregate(Min('PrevContribN_int'))
    minTillType = dbTrials.aggregate(Min('TillType_int'))
    maxTillType = dbTrials.aggregate(Max('TillType_int'))

    #Find parameters of users' last session
    if UserInputPreference.objects.filter(user=request.user).exists():
        userData = UserRquestSite.objects.filter(user_id=request.session['userid']).last()
        userTillage = UserInputPreference.objects.filter(user=request.user, parameter='tillType')[0].numeric

        userTillageConv = UserInputPreference.objects.filter(user=request.user, parameter='tillTypeConvTill')[0].numeric
        userTillageNoTill = UserInputPreference.objects.filter(user=request.user, parameter='tillTypeNoTill')[0].numeric


        userPrevCrop = UserInputPreference.objects.filter(user=request.user, parameter='prevCrop')[0].numeric
        userPrevCropLow = UserInputPreference.objects.filter(user=request.user, parameter='prevCropLow')[0].numeric
        userPrevCropMod = UserInputPreference.objects.filter(user=request.user, parameter='prevCropMod')[0].numeric
        userPrevCropHigh = UserInputPreference.objects.filter(user=request.user, parameter='prevCropHigh')[0].numeric

        clayRatioEntry = UserInputPreference.objects.filter(user=request.user, parameter='clayRatio')[0]
        userClayRatio = clayRatioEntry.numeric
        userClayRatioMax = clayRatioEntry.max
        userClayRatioMin = clayRatioEntry.min

        somEntry = UserInputPreference.objects.filter(user=request.user, parameter='SOM')[0]
        userSOM = somEntry.numeric
        userSOM_MIN = somEntry.min
        userSOM_MAX = somEntry.max

        chuEntry = UserInputPreference.objects.filter(user=request.user, parameter='CHU')[0]
        userCHU = chuEntry.numeric
        userCHU_MAX = chuEntry.max
        userCHU_MIN = chuEntry.min

        awdrEntry = UserInputPreference.objects.filter(user=request.user, parameter='awdr')[0]
        userAWDR = awdrEntry.numeric
        userAWDR_MAX = awdrEntry.max
        userAWDR_MIN = awdrEntry.min
        userQ = UserInputPreference.objects.filter(user=request.user, parameter='q_val')[0].numeric

    else:

        userTillage = "Conventional"
        userTillageConv = 1
        userTillageNoTill = 0

        userPrevCrop = 50
        userPrevCropLow = 0
        userPrevCropMod = 50
        userPrevCropHigh = 100

        userClayRatio = "Clay"
        userClayRatioMax = minClayRatio
        userClayRatioMin = maxClayRAtio
        userSOM = 5
        userSOM_MIN = minSOM
        userSOM_MAX = maxSOM
        userCHU = 750
        userCHU_MAX = maxCHU
        userCHU_MIN = minCHU
        userAWDR = 75
        userAWDR_MAX = maxAWDR
        userAWDR_MIN = minAWDR
        userQ = 2




    print('minCHU', minCHU)
    print('maxCHU', maxCHU)
    print('minClayRatio', minClayRatio)
    print('maxClayRAtio', maxClayRAtio)
    print('minSOM', minSOM)
    print('maxSOM', maxSOM)
    print('minAWDR', minAWDR)
    print('maxAWDR', maxAWDR)
    print('maxPrevCrop', maxPrevCrop)
    print('minPrevCrop', minPrevCrop)
    print('minTillType', minTillType)
    print('maxTillType', maxTillType)
    print('userSOM', userSOM)
    print('userCHU', userCHU)


    # upref= UserInputPreference(user=request.user, parameter='CHU',min=minCHU,max=maxCHU,numeric=None)
    # upref = UserInputPreference(user=request.user, parameter='ClayRatio', min=minClayRatio, max=maxClayRAtio, numeric=None)
    # upref = UserInputPreference(user=request.user, parameter='SOM', min=minSOM, max=maxSOM, numeric=None)
    # upref = UserInputPreference(user=request.user, parameter='awdr', min=minAWDR, max=maxAWDR, numeric=None)

    print('calling online resoruce finder for price and cost')
    cornPrice = OnlineResourcesFinder.getCornPrice()
    print('corn price fetched : ' + str(cornPrice))

    Ncost = OnlineResourcesFinder.getNitrogenCost()
    print('N cost fetched :' + str(Ncost))

    context = {'Ncost': Ncost, 'cornPrice': cornPrice, 'minCHU': minCHU['CHU__min'], 'maxCHU': maxCHU['CHU__max'],
               'minClayRatio': minClayRatio['ClayRatio__min'], 'maxClayRAtio': maxClayRAtio['ClayRatio__max'],
               'minSOM': minSOM['SOM__min'], 'maxSOM': maxSOM['SOM__max'], 'minAWDR': minAWDR['AWDR__min'],
               'maxAWDR': maxAWDR['AWDR__max'],
               'maxPrevCrop': maxPrevCrop['PrevContribN_int__max'], 'minPrevCrop': minPrevCrop['PrevContribN_int__min'],
               'minTillType': minTillType['TillType_int__min'], 'maxTillType': maxTillType['TillType_int__max'],'userTillage': userTillageConv,
               'userTillageConv': userTillageConv,'userTillageNoTill': userTillageNoTill,'userPrevCrop': userPrevCrop,
               'userPrevCropLow': userPrevCropLow,'userPrevCropMod': userPrevCropMod,'userPrevCropHigh': userPrevCropHigh,
               'userClayRatio': userClayRatio, 'userClayRatioMin': userClayRatioMin,'userClayRatioMax': userClayRatioMax,'userSOM': userSOM, 'userSOM_MIN':userSOM_MIN, 'userSOM_MAX':userSOM_MAX, 'userCHU': userCHU,
               'userCHU_MIN': userCHU_MIN,'userCHU_MAX': userCHU_MAX,'userAWDR': userAWDR, 'userAWDR_MIN': userAWDR_MIN, 'userAWDR_MAX': userAWDR_MAX, 'userQ':userQ}

    print('End , generalviews, index()')

    return render(request, 'passapp/home.html', context)


@transaction.atomic
@login_required()
def saveUserRequest(request):

    print('start, general view, saveUserRequest() ')
    if request.user.is_active == False:
        return  HttpResponseRedirect('/')

    fertilizer=request.POST.get('fertilizer', '')
    currentcrop=request.POST.get('currentcrop', '')
    season=request.POST.get('season', '')
    clayRatio = request.POST.get('soilType', '')
    clayRatioMin = request.POST.get('soilTypeMin', '')
    clayRatioMax = request.POST.get('soilTypeMax', '')
    tillTypeVal = request.POST.get('tillType', '')
    tillTypeNoTill = request.POST.get('tillTypeNoTill', '')
    tillTypeConvTill = request.POST.get('tillTypeConvTill', '')
    SOM = request.POST.get('som', '')
    SOMMin = request.POST.get('somMin', '')
    SOMMax = request.POST.get('somMax', '')
    latitude = request.POST.get('latitude', '')
    longitude = request.POST.get('longitude', '')
    climate = request.POST.get('climate', '')
    climateMin = request.POST.get('climateMin', '')
    climateMax = request.POST.get('climateMax', '')

    prevCropVal = request.POST.get('prevCrop', '')
    prevCropLow = request.POST.get('prevCropLow', '')
    prevCropMod = request.POST.get('prevCropMod', '')
    prevCropHigh = request.POST.get('prevCropHigh', '')
    CHU= request.POST.get('chu', '')
    CHUMin = request.POST.get('chuMin', '')
    CHUMax = request.POST.get('chuMax', '')
    q = request.POST.get('qVal', '')
    print((request.POST.get('meanprice', '').strip()))
    meanprice = float(request.POST.get('meanprice', '').strip())
    stdprice = float(request.POST.get('stdprice', '').strip())
    meancost = float(request.POST.get('meancost', ''))
    stdcost = float(request.POST.get('stdcost', ''))

    print("=============user specified paramters: =============")

    print("currentcrop :" + str(currentcrop))
    print("season :" + str(season))
    print("soilType :" + str(clayRatio))
    print("soilTypeMin :" + str(clayRatioMin))
    print("soilTypeMax :" + str(clayRatioMax))
    print("tillType :" + str(tillTypeVal))
    print("tillType (No Till):" + str(tillTypeNoTill))
    print("tillType (Conventional Till):" + str(tillTypeConvTill))
    print("latitude :" + str(latitude))
    print("longitude :" + str(longitude))
    print("climate :" + str(climate))
    print("climate min:" + str(climateMin))
    print("climate max:" + str(climateMax))
    print("prevCrop :" + str(prevCropVal))
    print("prevCrop Low:" + str(prevCropLow))
    print("prevCrop Moderate:" + str(prevCropMod))
    print("prevCrop High:" + str(prevCropHigh))
    print("meanprice :" + str(meanprice))
    print("stdprice :" + str(stdprice))
    print("meancost :" + str(meancost))
    print("stdcost :" + str(stdcost))
    print("SOM :" , SOM)
    print("SOM Min:", SOMMin)
    print("SOM Max:", SOMMax)

    print("CHU :", CHU)
    print("CHU min:", CHUMin)
    print("CHU max:", CHUMax)

    awdr= None
    chu=None
    som=None
    #split the categorical variables to take a concrete values, if other is psecified then take from other
    # textbox for respective attribute

    if clayRatio=='other':
        clayRatio=float(request.POST['soilTypeValue'])
    else:
        clayRatio = float(clayRatio)

    if climate=='other':

        awdr=float(request.POST['climateValue'])

    else:

        awdr = float(climate)

    if CHU=='other':
        chu= float(request.POST['chuValue'])
    else:

        chu=float(CHU);

    if SOM=='other':
        som = float(request.POST['somValue'])
    else:

        som = float(SOM);

    print('concreate values ' )

    print("chu :", chu)
    print("awdr :", awdr)
    print("som :", som)

    #Get key values for till, clay ratio, and prev crop. Key value is custom if user declared their own value
    if dsslookup.objects.filter(fieldname='till_type', value=tillTypeVal).exists():
        tillTypelookup = dsslookup.objects.filter(fieldname='till_type', value=tillTypeVal)[0].key
    else:
        tillTypelookup = "Custom"

    if dsslookup.objects.filter(fieldname='soil_type_clay_ratio', value=clayRatio).exists():
        clayratiolookup = dsslookup.objects.filter(fieldname='soil_type_clay_ratio', value=clayRatio)[0].key
    else:
        clayratiolookup = "Custom"

    if dsslookup.objects.filter(fieldname='prev_crop_N_contrib', value=prevCropVal).exists():
        prevCropLookup = dsslookup.objects.filter(fieldname='prev_crop_N_contrib', value=prevCropVal)[0].key
    else:
        prevCropLookup = "Custom"



    #Create dict of user settings
    userSettings = []
    userSettings.append(
        {'name':'fertilizer','value': fertilizer}
    )
    userSettings.append(
        {'name':'currentcrop','value': currentcrop}
    )
    userSettings.append(
        {'name':'season','value':season}
    )
    userSettings.append(
        {'name': 'latitude', 'value': latitude}
    )
    userSettings.append(
        {'name': 'longitude', 'value': longitude}
    )
    userSettings.append(
        {'name': 'clayRatio', 'value': clayRatio, 'min':clayRatioMin,'max':clayRatioMax}
    )
    userSettings.append(
        {'name': 'tillType', 'value': tillTypeVal}
    )
    userSettings.append(
        {'name': 'tillTypeNoTill', 'value': tillTypeNoTill}
    )
    userSettings.append(
        {'name': 'tillTypeConvTill', 'value': tillTypeConvTill}
    )
    userSettings.append(
        {'name': 'SOM', 'value': SOM, 'min': SOMMin, 'max': SOMMax}
    )
    userSettings.append(
        {'name': 'awdr', 'value': climate, 'min': climateMin, 'max': climateMax}
    )
    userSettings.append(
        {'name': 'CHU', 'value': CHU, 'min': CHUMin, 'max': CHUMax}
    )
    userSettings.append(
        {'name': 'prevCrop', 'value': prevCropVal}
    )
    userSettings.append(
        {'name': 'prevCropLow', 'value': prevCropLow}
    )
    userSettings.append(
        {'name': 'prevCropMod', 'value': prevCropMod}
    )
    userSettings.append(
        {'name': 'prevCropHigh', 'value': prevCropHigh}
    )
    userSettings.append(
        {'name': 'q_val', 'value': q}
    )

    #Add values from session to userinputpreferences
    for x in userSettings:
        if(UserInputPreference.objects.filter(user=request.user,parameter=x['name']).count() != 0):
            if'min' in x and 'max' in x:
                obj = UserInputPreference.objects.get(user=request.user,parameter=x['name'])
                obj.numeric = x['value']
                obj.min = x['min']
                obj.max = x['max']
                obj.save()
            else:
                obj = UserInputPreference.objects.get(user=request.user, parameter=x['name'])
                obj.numeric = x['value']
                obj.save()
        else:
            if 'min' in x and 'max' in x:
                userPref = UserInputPreference(user=request.user,parameter=x['name'],numeric=x['value'],min=x['min'],max=x['max'])
                userPref.save()
            else:
                userPref = UserInputPreference(user=request.user, parameter=x['name'], numeric=x['value'])
                userPref.save()

    # Store user request in user trans request
    ur = UserRquestSite(user=request.user, fertilizer=fertilizer, current_crop=currentcrop, season=season,
                        soiltype=clayratiolookup, soiltype_val=clayRatio,soiltype_min=clayRatioMin, soiltype_max=clayRatioMax,
                        tilltype=tillTypelookup, tilltype_val=tillTypeVal,
                        latitude=latitude, longitude=longitude, awdr=awdr, awdr_min=climateMin, awdr_max=climateMax,
                        prev_crop=prevCropLookup,prev_crop_val=prevCropVal, CHU=chu, CHU_min=CHUMin, CHU_max=CHUMax, SOM=som, SOM_min=SOMMin, SOM_max=SOMMax,
                        price_mean=meanprice, price_std=stdprice, costmean=meancost, coststd=stdcost,q_val = q)
    ur.save()

    print('user site request has been saved successfully, id', ur.id)

    #create entry in user transaction model, to proces request
    utrans=UserTransaction(usersite=ur,user=request.user)
    utrans.save()
    print('user trnsaction request has been saved successfully, id',utrans.id)
    messages.info(request,'Your request will be processed as soon as possible.You should receive an e-mail message acknowledging your request and another message with results.'\
                'Due to the heavy computation, this might take several minutes.')

    # send email of notificaton
    UserOperations.sendEmailNotification( request.user.username)

    print('End, general view, saveUserRequest() ')

    # redirect to notify about  processing started for request.
    return render(request,'passapp/notification.html')

def aboutusview(request):

    return render(request, 'passapp/aboutus.html')

def descriptionview (request):

    return render(request, 'passapp/description.html')




def downlaodCSV(request):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="dbTrialsNumericAg.csv"'

    writer = csv.writer(response)
    trailList = PlotYield.objects.all()
    with open(djangoSettings.STATIC_ROOT+'/datafiles/dbTrialsNumericAg.csv', newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')

        for row in spamreader:
            #print(', '.join(row))
            writer.writerow(row)

    return response

@login_required()
def addtrails(request):
    print('in addtrails view')
    return render(request, 'passapp/addtrails.html')


@login_required()
def submittrails(request):

    print('in submittrails view')
    if request.method == 'POST':
        if request.is_ajax():
            import json
            # user filled values, hold in variable
            fertilizer = request.POST['fertilizer']
            currentcrop = request.POST['currentcrop']
            season = int(request.POST['season'])
            soilType = request.POST['soilType']
            tillType = request.POST['tillType']
            SOM = request.POST['som']
            latitude = request.POST['latitude']
            longitude = request.POST['longitude']
            climate = request.POST['climate']
            prevCrop = request.POST['prevCrop']
            CHU= (request.POST['chu'])
            Nrate = int(request.POST['nrate'])
            yld = float(request.POST['yield'])
            sitename = request.POST['sitename']

            latitude = None if latitude == '' else float(latitude)
            longitude = None if longitude == '' else float(longitude)
            #som = None if som == '' else float(som)
            sitename = None if sitename == '' else sitename

            # province=request.POST.get('province', '')
            # city=request.POST.get('city', '')
            # region=request.POST.get('region', '')
            # fieldnumber=int(request.POST.get('fieldnumber', ''))


            print('user submitted values are :')

            print("currentcrop :" + str(currentcrop))
            print("season :", season)
            print("soilType :" + str(soilType))
            print("tillType :" + str(tillType))
            print("som :", SOM)
            print("chu :", CHU)
            print("latitude :", latitude)
            print("longitude :", longitude)
            print("sitename :", sitename)
            print("climate :", climate)
            print("prevCrop :" + str(prevCrop))
            print("Nrate :", Nrate)
            print("yield :", yld)

            # check for outliers/rules
            if Nrate < 0 or Nrate > 350:
                # messages.error(request, "Fertilizer rate should not be negative and maximum up to 350 kg/ha, please verify")
                message = 'Error!, the fertilizer rate should not be negative and maximum up to 350 kg/ha. Please correct the input'
                return HttpResponse(message)

            if yld < 0 or yld > 30:
                # messages.error(request, "Yield should not be negative and maximum up to 30 t/ha, please verify")
                message = 'Error!, the yield value should not be negative and maximum up to 30 t/ha. Please correct the input'
                return HttpResponse(message)

            # source =useremail
            source = request.session['useremail']

            awdr, chu, som = None,None,None
            if climate == 'other':
                awdr = float(request.POST['awdrother'])
            else:


                awdr = float(climate)

            if CHU == 'other':
                chu = float(request.POST['chuother'])
            else:


                chu = float(CHU);

            if SOM == 'other':
                som = float(request.POST['somother'])
            else:

                som = float(SOM);

            print('descrete values ')
            print("chu :", chu)
            print("awdr :", awdr)
            print("som :", som)

            tillTypelookup = int(dsslookup.objects.filter(fieldname='till_type', key=tillType)[0].value)
            clayratiolookup = float(dsslookup.objects.filter(fieldname='soil_type_clay_ratio', key=soilType)[0].value)
            prevCropNcontribLookup = int(
                dsslookup.objects.filter(fieldname='prev_crop_N_contrib', key=prevCrop)[0].value)

            print("source ", source)

            print("tillTypelookup ", tillTypelookup)
            print("clayratiolookup ", clayratiolookup)
            print("prevCropNcontribLookup ", prevCropNcontribLookup)

            # if admin privilage, verified = Y, for user by default verified is = N
            # if request.session['isstaff']:
            #     verified = 'Y'
            # else:
            #     verified = 'N'
            #default verified as N
            verified = 'N'
            # check here if user has existing trail with same parameters, then it should be considered as duplicate and prevent from adding it.
            trailList = PlotYield.objects.filter(Latitude=latitude, Longitude=longitude,Year=season,
                                                 SoilType=soilType, ClayRatio=clayratiolookup, TillType=tillType,
                                                 SOM=som,
                                                 TillType_int=tillTypelookup, PrevCrop=prevCrop, CHU=chu,
                                                 PrevContribN_int=prevCropNcontribLookup,
                                                 AWDR=awdr, Nrate=Nrate, Yield=yld, Source=source)

            if (trailList.count() > 0):

                if sitename is not None and sitename is not '':

                    siteList = SiteField.objects.filter(Site_Field_Name=sitename)
                    if siteList.count() > 0:

                        filterTrail = trailList.filter(SiteFieldId=siteList.last())
                        if filterTrail.count() > 0:
                            message = 'Error!, a trail already exist with the inputed details under your account. Please change any of the input field to treat as a new trial and submit again'
                            return HttpResponse(message)
                else:

                    message = 'Error!, a trail already exist with the inputed details under your account. Please change any of the input field to treat as a new trial and submit again'
                    return HttpResponse(message)
                # if latitude is not None and longitude is not None:
                #
                #     filterTrail = trailList.filter(Latitude=latitude, Longitude=longitude)
                #     if filterTrail.count() > 0:
                #
                #         message = 'Error!, a trail already exist with the inputed details under your account. Please change any of the input field to treat as a new trial and submit again'
                #         return HttpResponse(message)



            print("verified ", verified)

            sitefield = SiteField(Site_Field_Name=sitename)
            sitefield.save()
            print('SiteField is successfully inserted id ', sitefield.id)
            try:

                print('inserting plot/trial now ')
                plot = PlotYield(SiteFieldId=sitefield, Latitude=latitude, Longitude=longitude, Year=season,
                                 SoilType=soilType, ClayRatio=clayratiolookup, TillType=tillType, SOM=som,
                                 TillType_int=tillTypelookup, PrevCrop=prevCrop,CHU=chu,
                                 PrevContribN_int=prevCropNcontribLookup,
                                 AWDR=awdr, Nrate=Nrate, Yield=yld, Source=source, Verified=verified)
                plot.save()
                print("PlotYield is successfully inserted id", plot.id)

                #messages.success(request,'your farm trail has been successfully submitted, your efforts are appreciated, Thank you!')
                message =  'The data have been successfully submitted. Thank you for your submission'
                return HttpResponse(message)
            except Exception as ex:
                print('Could not insert user trail into database, ', ex)
                messages.error(request, 'oops!, there was some exception, please try again ...')
                transaction.rollback()
                # raise Exception ('oops!, there was some exception, please try again ...')

        return render(request, 'passapp/addtrails.html')


