from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.auth.models import User
# Create your models here.

'''
note: do not run the migrate command, all the changes in models or migrations will be done through the service layer.
 since both the webapp layer and service layer has the same model file. the database will already has the model schema ready by the service layer
 model changes or migrations.
'''

@python_2_unicode_compatible
class PDataset1(models.Model,):
    BDoriginale = models.CharField(max_length=100)
    Champ = models.CharField(max_length=100)
    #REcorded_Year = models.DateTimeField(null=True)
    AWDR = models.FloatField(null=True)

    TillPractice = models.CharField(max_length=100)
    TillType = models.CharField(max_length=100)
    TillTypeChoices = (
        (0, 'No till'),
        (1, 'Conventional'),
    )
    TillType_int = models.IntegerField(null=True, choices=TillTypeChoices)
    PrevCrop = models.CharField(max_length=100)
    PrevContribN = models.IntegerField(null=True)
    PrevContribNChoices = (
        ('Weak', '0 - 25 kg/ha'),
        ('Medium', '25 - 50 kg/ha'),
        ('Strong', '50 -100 kg/ha'),
    )
    PrevContribN_cls = models.CharField(null=True, choices=PrevContribNChoices, max_length=50)
    SoilType = models.CharField(max_length=50)
    SoilTexture_cls = models.CharField(max_length=50)
    Yld0    = models.FloatField(null=True)
    Yld50   = models.FloatField(null=True)
    Yld100  = models.FloatField(null=True)
    Yld150  = models.FloatField(null=True)
    Yld200  = models.FloatField(null=True)
    Ymodel0 = models.FloatField(null=True)
    Ymax = models.FloatField(null=True)
    Nymax = models.FloatField(null=True)
    a = models.FloatField(null=True)
    b = models.FloatField(null=True)
    c = models.FloatField(null=True)
    #pub_date = models.DateTimeField('date published')
    class Meta:
          db_table = 'PaasDataset1'



class UserRquestSite(models.Model):
    user=   models.ForeignKey(User,on_delete=None)
    fertilizer= models.CharField(max_length=100)
    current_crop= models.CharField(max_length=100)
    season =    models.IntegerField()
    soiltype=   models.CharField(max_length=100)
    soiltype_val = models.FloatField(null=True)
    soiltype_min = models.CharField(max_length=100)
    soiltype_max = models.CharField(max_length=100)
    tilltype=   models.CharField(max_length=100)
    tilltype_val = models.FloatField(null=True)
    latitude=   models.CharField(max_length=100)
    longitude=  models.CharField(max_length=100)
    awdr = models.FloatField(null=True)
    awdr_min = models.FloatField(null=True)
    awdr_max = models.FloatField(null=True)
    prev_crop=  models.CharField(max_length=100)
    prev_crop_val = models.FloatField(null=True)
    price_mean= models.FloatField(null=True)
    price_std=  models.FloatField(null=True)
    costmean=   models.FloatField(null=True)
    coststd=    models.FloatField(null=True)
    request_date = models.DateField(auto_now_add=True)
    CHU = models.IntegerField(null=True)
    CHU_min = models.IntegerField(null=True)
    CHU_max = models.IntegerField(null=True)
    SOM = models.FloatField(null=True)
    SOM_min = models.FloatField(null=True)
    SOM_max = models.FloatField(null=True)
    q_val = models.IntegerField(null=True)

    class Meta:
          db_table = 'dssservice_userrquestsite'

class UserInputPreference(models.Model):
    user = models.ForeignKey(User,on_delete=None)
    parameter = models.CharField(null=True,max_length=100)
    min = models.FloatField(null=True)
    max = models.FloatField(null=True)
    numeric =models.CharField(max_length=100)
    class Meta:
          db_table = 'dssservice_userinputpreference'

class UserTransaction(models.Model):

    usersite = models.OneToOneField(
        UserRquestSite,on_delete=None,
        verbose_name="user request site to user trans mapping",
    )
    user = models.ForeignKey(User,on_delete=None)
    #'0:Pending, 1: Completed'
    status = models.IntegerField(null=True,default=0)
    creation_date=models.DateField(auto_now_add=True)
    retry_count=models.IntegerField(null=True, default=0)
    #'Y:Yes,N:No'
    isEmailSent=models.CharField(max_length=1,default='N')
    request_process_time=models.IntegerField(null=True)
    class Meta:
          db_table = 'dssservice_usertransaction'



class SiteField(models.Model):
    Site_Field_Name = models.CharField(null=True, max_length=200)
    Data_Soruce = models.CharField(null=True, max_length=100)
    Province = models.CharField(null=True, max_length=100)
    Region = models.CharField(null=True, max_length=200)
    Town = models.CharField(null=True, max_length=100)
    Site = models.CharField(null=True, max_length=100)
    Field_Number = models.IntegerField(null=True)

    class Meta:
        db_table = 'dssservice_sitefield'



class PlotYield(models.Model):
    SiteFieldId=models.ForeignKey(SiteField,on_delete=None)
    Latitude=models.FloatField(null=True)
    Longitude=models.FloatField(null=True)
    Year=models.IntegerField(null=True)
    SoilType=models.CharField(max_length=100)

    ClayRatio=models.FloatField(null=True)
    SOM=models.FloatField(null=True)

    TillType=models.CharField(null=True,max_length=100)

    # TillTypeChoices=(
    #     (0, 'No till'),
    #     (1, 'Conventional'),
    # )
    TillType_int =models.IntegerField(null=True)

    PrevCrop=models.CharField(null=True,max_length=100)
    PrevContribN_int=models.IntegerField(null=True)

    CHU=models.IntegerField(null=True)
    PPT=models.IntegerField(null=True)
    AWDR=models.FloatField(null=True)
    Nrate=models.IntegerField(null=False)
    Yield=models.FloatField(null=False)
    Source = models.CharField(max_length=150)
    Verified = models.CharField(default='N', max_length=1)

    class Meta:
        db_table = 'dssservice_plotyield'

class dsslookup(models.Model):
    fieldname = models.CharField(null=True,max_length=100)
    key     =   models.CharField(null=True,max_length=100)
    value   =   models.FloatField(null=True)

    def __str__(self):
        return self.fieldname+self.key

    class Meta:
        db_table = 'dssservice_dsslookup'

