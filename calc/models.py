from django.db import models
from polymorphic.models import PolymorphicModel
from polymorphic.managers import PolymorphicManager
from django.urls import reverse
from django.utils.translation import gettext as _
from polymorphic.managers import PolymorphicManager, PolymorphicQuerySet
from fractions import Fraction
from functools import reduce
import math
from django.db.models import Count



from django.contrib.auth.models import User
def NON_POLYMORPHIC_CASCADE(collector, field, sub_objs, using):
    return models.CASCADE(collector, field, sub_objs.non_polymorphic(), using)

class CascadeDeletePolymorphicQuerySet(PolymorphicQuerySet):
    """
    Patch the QuerySet to call delete on the non_polymorphic QuerySet, avoiding models.deletion.Collector typing problem

    Based on workarounds proposed in: https://github.com/django-polymorphic/django-polymorphic/issues/229
    See also: https://github.com/django-polymorphic/django-polymorphic/issues/34,
              https://github.com/django-polymorphic/django-polymorphic/issues/84
    Related Django ticket: https://code.djangoproject.com/ticket/23076
    """
    def delete(self):
        if not self.polymorphic_disabled:
            return self.non_polymorphic().delete()
        else:
            return super().delete()


class CascadeDeletePolymorphicManager(PolymorphicManager):
    queryset_class = CascadeDeletePolymorphicQuerySet

class Person(PolymorphicModel):
    non_polymorphic = CascadeDeletePolymorphicManager()

    class Meta:
        base_manager_name = 'non_polymorphic'
    """Person Class"""
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )
    sex = models.CharField(max_length=1, choices=GENDER_CHOICES,null=False,blank=True)
    first_name = models.CharField(max_length=200,blank=True)
    last_name = models.CharField(max_length=200,blank=True)
    parents = models.ForeignKey('Marriage',null=True, on_delete=models.SET_NULL, blank=True)

    def add_father(self, father):
        if self.parents and self.parents.male:
            raise _("father already exist")
        else:
            #check for parents
            if self.parents is None:
                self.parents = Marriage.objects.create()

            self.parents.add_male(father)
            self.save()

            return father
    def add_mother(self, mother):
        if self.parents and self.parents.female:
            raise _("Mother already exist")
        else:
            #check for parents
            if self.parents is None:
                self.parents = Marriage.objects.create()

            self.parents.add_female(mother)
            self.save()
            return mother

    def add_husband(self, husband):
        #check for existing marriages
        if self.male_marriages.count() == 0:
            m = Marriage.objects.create()
            m.add_male(husband)
            m.add_female(self)
            return m
        else:
             raise _("Husband already exist")

    def add_wife(self, wife):
        #check for existing marriages
        if self.female_marriages.count() < 4:
            m = Marriage.objects.create()
            m.add_male(self)
            m.add_female(wife)
            return m
        else:
            raise _("Can't have more than 4 wives")

    def add_daughter(self, daughter, mother, father):

        #check if person is a male
        if self.sex == 'M':
            #check for marriages
            if self.male_marriages.count() != 0:
                daughter.parents=Marriage.objects.get(male=self, female=mother)
            else:
                daughter.parents=Marriage.objects.create()
                daughter.parents.add_male(self)
                daughter.parents.add_female(mother)

        elif self.sex == 'F':
            if self.female_marriages.count() != 0:
                daughter.parents=Marriage.objects.get(female=self, male=father)
            else:
                daughter.parents=Marriage.objects.create()
                daughter.parents.add_male(father)
                daughter.parents.add_female(self)

    def add_son(self, son, mother, father):

        #check if person is a male
        if self.sex == 'M':
            #check for marriages
            if self.male_marriages.count() != 0:
                son.parents=Marriage.objects.get(male=self, female=mother)
            else:
                son.parents=Marriage.objects.create()
                son.parents.add_male(self)
                son.parents.add_female(mother)

        elif self.sex == 'F':
            if self.female_marriages.count() != 0:
                son.parents=Marriage.objects.get(female=self, male=father)
            else:
                son.parents=Marriage.objects.create()
                son.parents.add_male(father)
                son.parents.add_female(self)

    def add_brother(self, brother):
        brother.parents=self.parents
        brother.save()

    def add_sister(self, sister):
        sister.parents=self.parents
        sister.save()

    def add_grandFather(self, grandFather):
        if self.parents and self.parents.male:
            self.parents.male.add_father(grandFather)
        self.save()

        return grandFather

    def add_grandMother(self, grandMother):
        pass

    def add_sonOfSon(self, son):
        pass

    def add_daughterOfSon(self, daughter):
        pass

    def add_paternalSister(self, sister):
        pass

    def add_paternalBrother(self, brother):
        pass

    def add_maternalSister(self, sister):
        pass

    def add_maternalBrother(self, brother):
        pass

    def add_sonOfBrother(self, sonOfBrother):
        pass

    def add_sonOfPaternalBrother(self, sonOfPaternalBrother):
        pass

    def add_uncle(self, uncle):
        pass

    def add_paternalUncle(self, uncle):
        pass

    def add_sonOfUncle(self, sonOfUncle):
        pass

    def add_sonOfPaternalUncle(self, sonOfPaternalUncle):
        pass

    def __str__(self):
        return f"{self.first_name} id: {self.id}"

class Marriage(models.Model):
    """Marriage Class"""
    male = models.ForeignKey(Person,null=True, on_delete=models.CASCADE,related_name='male_marriages',blank=True)
    female = models.ForeignKey(Person,null=True, on_delete=models.CASCADE,related_name='female_marriages',blank=True)

    def add_male(self, person):
        self.male = person
        self.save()

    def add_female(self, person):
        self.female = person
        self.save()

    def __str__(self):
        return "id: " + str(self.id) + " " +(self.male.first_name if self.male  else "") + " " + (self.female.first_name if self.female else "")


class Calculation(models.Model):
    """Calculation for bequest class"""
    shares = models.IntegerField(default=0)      # LCM for all prescribed shares
    excess = models.BooleanField(default=False)       # if prescribed shares is greater than gcm
    shortage = models.BooleanField(default=False)
    residual_shares = models.IntegerField(default=0)
    correction = models.BooleanField(default=False)  # shares and heirs number division should give no fractions
    shortage_calc = models.BooleanField(default=False)
    shortage_calc_shares = models.IntegerField(default=0)
    shortage_union_shares = models.IntegerField(default=0)
    shares_excess = models.IntegerField(default=0)
    shares_corrected = models.IntegerField(default=0)
    shares_shorted = models.IntegerField(default=0)
    maternal_quote = models.BooleanField(default=False)
    common_quote = models.BooleanField(default=False) # siblings share quote with maternal siblings in case of no remainder

    user = models.ForeignKey(User,on_delete=models.CASCADE,null=True)
    name = models.CharField(max_length=200)

    def add_father(self, father):
        return father.add(calc=self)

    def add_mother(self, mother):
        return mother.add(calc=self)

    def add_husband(self, husband):
        return husband.add(calc=self)

    def add_wife(self, wife):
        return wife.add(calc=self)

    def add_daughter(self, daughter, mother, father):
        return daughter.add(calc=self, mother=mother, father=father)

    def add_son(self, son, mother, father):
        return son.add(calc=self, mother=mother, father=father)

    def add_brother(self, heir):
        heir.add(calc=self)
        heir.save()
        return heir

    def add_sister(self, heir):
        heir.add(calc=self)
        heir.save()
        return heir

    def add_grandFather(self, heir):
        heir.add(calc=self)
        heir.save()
        return heir

    def add_grandMother(self, heir):
        heir.add(calc=self)
        heir.save()
        return heir

    def add_sonOfSon(self, heir):
        heir.add(calc=self)
        heir.save()
        return heir

    def add_daughterOfSon(self, heir):
        heir.add(calc=self)
        heir.save()
        return heir

    def add_paternalSister(self, heir):
        heir.add(calc=self)
        heir.save()
        return heir

    def add_paternalBrother(self, heir):
        heir.add(calc=self)
        heir.save()
        return heir

    def add_maternalSister(self, heir):
        heir.add(calc=self)
        heir.save()
        return heir

    def add_maternalBrother(self, heir):
        heir.add(calc=self)
        heir.save()
        return heir

    def add_sonOfBrother(self, heir):
        heir.add(calc=self)
        heir.save()
        return heir

    def add_sonOfPaternalBrother(self, heir):
        heir.add(calc=self)
        heir.save()
        return heir

    def add_uncle(self, heir):
        heir.add(calc=self)
        heir.save()
        return heir

    def add_paternalUncle(self, heir):
        heir.add(calc=self)
        heir.save()
        return heir

    def add_sonOfUncle(self, heir):
        heir.add(calc=self)
        heir.save()
        return heir

    def add_sonOfPaternalUncle(self, heir):
        heir.add(calc=self)
        heir.save()
        return heir

    def __str__(self):
        return str(self.name)

    def get_quotes(self):
        for heir in self.heir_set.all().order_by('polymorphic_ctype_id'):
            heir.get_quote(self)

    def lcm(self, a, b):
        return abs(a*b) // math.gcd(a, b)

    def lcm_list(self, list):
        return reduce(lambda a, b : self.lcm(a, b), list)

    def has_descendent(self):
        return self.heir_set.instance_of(Son).count() > 0 or self.heir_set.instance_of(Daughter).count() > 0 or self.heir_set.instance_of(SonOfSon).count() > 0 or self.heir_set.instance_of(DaughterOfSon).count() > 0

    def has_male_descendent(self):
        return self.heir_set.instance_of(Son).count() > 0 or self.heir_set.instance_of(SonOfSon).count() > 0

    def has_female_descendent(self):
        return self.heir_set.instance_of(Daughter).count() > 0 or self.heir_set.instance_of(DaughterOfSon).count() > 0

    def has_siblings(self):
        return self.heir_set.instance_of(Brother).count() + self.heir_set.instance_of(PaternalBrother).count() + self.heir_set.instance_of(MaternalBrother).count() + self.heir_set.instance_of(Sister).count() + self.heir_set.instance_of(PaternalSister).count() + self.heir_set.instance_of(MaternalSister).count() > 1

    def has_spouse(self):
        return self.heir_set.instance_of(Wife, Husband).count() > 0

    def has_asaba(self):
        return self.heir_set.filter(asaba=True).count() > 0

    def has_father(self):
        return self.heir_set.instance_of(Father).count() > 0

    def has_grandFather(self):
        return self.heir_set.instance_of(GrandFather).count() > 0

    def has_mohter(self):
        return self.heir_set.instance_of(Mother).count() > 0

    def has_son(self):
        return self.heir_set.instance_of(Son).count() > 0

    def has_brother(self):
        return self.heir_set.instance_of(Brother).count() > 0

    def has_sister(self):
        return self.heir_set.instance_of(Sister).count() > 0

    def has_grandFather(self):
        return self.heir_set.instance_of(GrandFather).count() > 0

    def has_sonOfSon(self):
        return self.heir_set.instance_of(SonOfSon).count() > 0

    def has_paternalBrother(self):
        return self.heir_set.instance_of(PaternalBrother).count() > 0

    def has_sonOfBrother(self):
        return self.heir_set.instance_of(PaternalBrother).count() > 0

    def has_sonOfPaternalBrother(self):
        return self.heir_set.instance_of(SonOfPaternalBrother).count() > 0

    def has_uncle(self):
        return self.heir_set.instance_of(Uncle).count() > 0

    def has_paternalUncle(self):
        return self.heir_set.instance_of(PaternalUncle).count() > 0

    def has_sonOfUncle(self):
        return self.heir_set.instance_of(SonOfUncle).count() > 0

    def has_daughter(self):
        return self.heir_set.instance_of(Daughter).count() > 0

    def has_maternalSister(self):
        return self.heir_set.instance_of(MaternalSister).count() > 0

    def has_maternalBrother(self):
        return self.heir_set.instance_of(MaternalBrother).count() > 0

    def get_father(self):
        return self.heir_set.instance_of(Father).first()

    def get_mother(self):
        return self.heir_set.instance_of(Mother).first()

    def get_husband(self):
        return self.heir_set.instance_of(Husband).first()

    def get_wives(self):
        return self.heir_set.instance_of(Wife)

    def get_spouse(self):
        return self.heir_set.instance_of(Husband,Wife)

    def get_daughters(self):
        return self.heir_set.instance_of(Daughter)

    def get_sons(self):
        return self.heir_set.instance_of(Son)

    def get_brothers(self):
        return self.heir_set.instance_of(Brother)

    def get_sisters(self):
        return self.heir_set.instance_of(Sister)

    def get_grandFather(self):
        return self.heir_set.instance_of(GrandFather).first()

    def get_paternalSisters(self):
        return self.heir_set.instance_of(PaternalSister)

    def get_heirs_no_spouse(self):
        return self.heir_set.not_instance_of(Husband, Wife)

    def get_fractions(self, heirs):
        fractions = set()
        for heir in heirs:
            fractions.add(heir.get_fraction())
        return fractions

    def set_calc_shares(self):
        count = self.heir_set.filter(blocked=False).count()
        #if all are asaba (agnates)
        if self.heir_set.filter(asaba=True).count() == count:
            males = self.heir_set.filter(sex='M',blocked=False).count()
            females = self.heir_set.filter(sex='F',blocked=False).count()
            #if all same gender
            if   males == count or females  == count:
                self.shares = count
            else:
                for heir in self.heir_set.filter(blocked=False):
                    self.shares = males * 2 + females
        else:
            denom_list = []
            fractions_set = self.get_fractions(self.heir_set.filter(blocked=False))
            for fraction in fractions_set:
                denom_list.append(fraction.denominator)
            self.shares = self.lcm_list(denom_list)
        self.save()
        return self.shares
    def get_shares(self):
        shares = 0
        #first get shares without asaba
        for  heir in self.heir_set.filter(correction=False, asaba=False, blocked=False):
            shares = shares + heir.share
        if self.correction == True:
            correction_set = self.heir_set.filter(correction=True, asaba=False).values('polymorphic_ctype_id','share').annotate(total=Count('id'))
            for result in correction_set:
                shares = shares + result["share"]
        #if there is asaba with need for correction
        asaba = self.heir_set.filter(asaba=True, correction=True).first()
        if asaba:
            shares = shares + asaba.share
        else:
            for asaba in self.heir_set.filter(asaba=True, correction=False):
                shares = shares + asaba.share
        if shares > self.shares:
            if self.common_quote == False:
                self.excess = True
                self.shares_excess = shares
                self.save()
                return self.shares_excess
        return shares

    def set_shares(self):
        for heir in self.heir_set.filter(blocked=False):
            heir.set_share(self)

    def set_calc_correction(self):
        if self.correction == True:
            shares = 0
            if self.excess == True:
                shares = self.shares_excess
            elif self.shortage == True:
                shares = self.shares_shorted
            else:
                shares = self.shares
            correction_set = self.heir_set.filter(correction=True).values('polymorphic_ctype_id','quote').annotate(total=Count('id'))
            asaba_set = self.heir_set.filter(asaba=True, correction=True).values('polymorphic_ctype_id','quote').annotate(total=Count('id'))
            if self.common_quote == True:
                heir_share = self.heir_set.filter(correction=True).first().share
                count = self.heir_set.filter(correction=True).count()
                if count % heir_share == 0:
                    self.shares_corrected = math.gcd(count, heir_share) * shares
                else:
                    self.shares_corrected = count * shares
            elif correction_set.count() == 1:
                heir_share = self.heir_set.filter(correction=True).first().share
                count = self.heir_set.filter(correction=True).count()
                if count % heir_share == 0:
                    self.shares_corrected = math.gcd(count, heir_share) * shares
                else:
                    self.shares_corrected = count * shares
            elif asaba_set.count() == 2:
                factors = set()
                correction_set_without_asaba = self.heir_set.filter(correction=True, asaba=False).values('polymorphic_ctype_id','quote').annotate(total=Count('id'))
                males = self.heir_set.filter(asaba=True, sex='M').count()
                females = self.heir_set.filter(asaba=True, sex='F').count()
                asaba_count = males * 2 + females
                asaba_share = self.heir_set.filter(asaba=True).first().share
                if asaba_share != 0:
                    if asaba_share % asaba_count == 0:
                        factors.add(math.gcd(asaba_count, asaba_share))
                    else:
                        factors.add(asaba_count)
                for result in correction_set_without_asaba:
                    heir_share = Fraction(result["quote"]).limit_denominator().numerator
                    count = result["total"]
                    if heir_share != 0:
                        if heir_share % count == 0:
                            factors.add(math.gcd(count, heir_share))
                        else:
                            factors.add(count)
                self.shares_corrected = self.lcm_list(factors) * shares
            else:
                factors = set()
                for result in correction_set:
                    heir_share = Fraction(result["quote"]).limit_denominator().numerator
                    count = result["total"]
                    if heir_share != 0:
                        if heir_share % count == 0:
                            factors.add(math.gcd(count, heir_share))
                        else:
                            factors.add(count)
                self.shares_corrected = self.lcm_list(factors) * shares


            self.save()
            return self.shares_corrected

    def get_corrected_shares(self):
        if self.correction == True and self.shares_corrected != 0:
            shares = 0
            for  heir in self.heir_set.filter(blocked=False):
                shares = shares + heir.get_corrected_share(self)
            return shares

    def set_calc_shortage(self):
        shares = self.get_shares()
        if self.shares > shares:
            self.shortage = True
            remainder = self.shares - shares
            if self.has_father() or self.has_grandFather() == True :
                self.shares_shorted = self.shares
            elif self.has_spouse() == False:
                self.shares_shorted = shares
            elif self.has_spouse() == True:
                spouse = self.get_spouse().first()
                self.shares_shorted = spouse.get_fraction().denominator
            self.save()
    def set_asaba_quotes(self):
        #check for asaba exclude father with quote
        asaba = self.heir_set.filter(asaba=True).exclude(quote__gt=0)
        if asaba:
            #check for residual_shares
            if self.residual_shares > 0 or self.common_quote == True:
                for heir in asaba:
                    heir.set_asaba_quote(self)

    def set_amounts(self):
        for heir in self.heir_set.filter(blocked=False):
            heir.set_amount(self)

    def set_asaba_shares(self):
        if self.residual_shares > 0 or self.common_quote == True:
            for heir in self.heir_set.filter(blocked=False):
                heir.set_asaba_share(self)

    def set_remainder(self):
        if self.common_quote == False:
            shares = self.get_shares()
            self.residual_shares=  self.shares - shares
            return self.residual_shares

    def set_calc_excess(self):
        shares = self.get_shares()
        if shares > self.shares and self.common_quote == False:
            self.excess = True
            self.shares_excess = shares
            self.save()

    def set_shortage_shares(self):
        if self.shortage == True:
            #check for Father
            if self.has_father():
                father = self.get_father()
                remainder = self.shares - self.get_shares()
                father.shorted_share = father.share + remainder
                father.save()
                heirs = self.heir_set.not_instance_of(Father)
                for heir in heirs:
                    heir.shorted_share = heir.share
                    heir.save()
            #check for Grandfather
            elif self.has_grandFather():
                grandfather = self.get_grandFather()
                remainder = self.shares - self.get_shares()
                grandfather.shorted_share = grandfather.share + remainder
                grandfather.save()
                heirs = self.heir_set.not_instance_of(GrandFather)
                for heir in heirs:
                    heir.shorted_share = heir.share
                    heir.save()
            else:
                spouse_set =  self.get_spouse()
                for spouse in spouse_set:
                    spouse.shorted_share = spouse.get_fraction().numerator
                    spouse.save()
                for heir in self.heir_set.not_instance_of(Husband,Wife):
                    heir.set_shortage_share(self)

    def set_shortage_calc_shares(self):
        if self.shortage_calc == True:
            denom_list = []
            heirs = self.get_heirs_no_spouse()
            fractions_set = self.get_fractions(heirs)
            for fraction in fractions_set:
                denom_list.append(fraction.denominator)
            self.shortage_calc_shares = self.lcm_list(denom_list)
            self.save()

    def set_shortage_calc_share(self):
        if self.shortage_calc == True:
            heirs = self.get_heirs_no_spouse()
            for heir in heirs:
                heir.set_shortage_calc_share(self)

    def set_shortage_union_shares(self):
        if self.shortage_calc == True:
            heirs = self.get_heirs_no_spouse()
            shorted_shares = 0
            remainder = heirs.first().shorted_share
            for heir in heirs:
                shorted_shares = shorted_shares + heir.shortage_calc_share
            if shorted_shares % remainder == 0:
                self.shortage_union_shares = self.shortage_calc_shares
            else:
                self.shortage_union_shares = shorted_shares * self.shares_shorted
            self.save()
    def set_shortage_union_share(self):
        if self.shortage_calc == True:
            spouse_set =  self.get_spouse()
            multiplier = self.shortage_union_shares // self.shares_shorted
            for spouse in spouse_set:
                spouse.shortage_union_share = spouse.shorted_share * multiplier
                spouse.save()
            heirs = self.get_heirs_no_spouse()
            for heir in heirs:
                heir.set_shortage_union_share(self)

    def check_common_quote(self):
        # check for common_quote
        if self.heir_set.instance_of(MaternalSister, MaternalBrother).filter(quote__gt=0).count() > 1 and self.heir_set.instance_of(Brother).filter(asaba=True).count() >= 1 and self.heir_set.instance_of(Husband).filter(quote__gt=1/4) and self.heir_set.instance_of(Mother).filter(quote__gt=0) :
            self.common_quote = True
            self.save()

    def clear(self):
        self.shares = 0
        self.excess = False
        self.shortage = False
        self.residual_shares = 0
        self.correction = False
        self.shortage_calc = False
        self.shortage_calc_shares = 0
        self.shortage_union_shares = 0
        self.shares_excess = 0
        self.shares_corrected = 0
        self.shares_shorted = 0
        self.maternal_quote  = False
        self.common_quote = False
        for heir in self.heir_set.all():
            heir.clear()
        self.save()

    def compute(self):
        self.clear()
        self.get_quotes()
        self.check_common_quote()
        self.set_calc_shares()
        self.set_shares()
        self.set_remainder()
        self.set_asaba_quotes()
        self.set_asaba_shares()
        self.get_shares()
        self.set_calc_excess()
        self.set_calc_shortage()
        self.set_shortage_shares()
        if self.shortage_calc:
            self.set_shortage_calc_shares()
            self.set_shortage_calc_share()
            self.set_shortage_union_shares()
            self.set_shortage_union_share()
        self.set_calc_correction()
        self.get_corrected_shares()
        self.set_amounts()
        self.save()

    def get_absolute_url(self):
        return reverse('calc:detail', args=[self.id])
class Deceased(Person):
    """Deceased class"""
    estate = models.IntegerField()
    calc = models.ForeignKey(Calculation, on_delete=NON_POLYMORPHIC_CASCADE,null=True)
    def get_absolute_url(self):
        return reverse('calc:detail', args=[self.calc.id])
class Heir(Person):
    """Heir class"""
    quote = models.DecimalField(max_digits=11, decimal_places=10, default=0)  #prescribed share
    shared_quote = models.BooleanField(default=False)    #prescribed share is shared with other heir like 2 daughters
    share = models.IntegerField(default=0)
    corrected_share = models.IntegerField(default=0)
    shorted_share = models.IntegerField(default=0)
    amount = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    asaba = models.BooleanField(default=False)           #agnate or residuary
    blocked = models.BooleanField(default=False)         # restricted from inheritance
    quote_reason = models.CharField(max_length=255, default="")
    correction = models.BooleanField(default=False)
    shortage_calc = models.BooleanField(default = False)
    shortage_calc_share = models.IntegerField(default=0)
    shortage_union_share = models.IntegerField(default=0)
    abstract = True
    calc = models.ForeignKey(Calculation, on_delete=NON_POLYMORPHIC_CASCADE,null=True)
    def get_absolute_url(self):
        return reverse('calc:detail', args=[self.calc.id])
    def __str__(self):
        return (self.first_name if self.first_name else " ")
    def get_quote(self, calc):
        pass
    def set_share(self, calc):
        if self.quote != 0 and self.asaba == False:
            share = calc.shares * self.get_fraction().numerator // self.get_fraction().denominator
            if self.shared_quote == True:
                if calc.maternal_quote == True:
                    if calc.common_quote == True:
                        count = calc.heir_set.instance_of(MaternalSister, MaternalBrother, Sister, Brother).count()
                    else:
                        count = calc.heir_set.instance_of(MaternalSister, MaternalBrother).count()
                elif calc.common_quote == True:
                        count = calc.heir_set.instance_of(MaternalSister, MaternalBrother, Sister, Brother).count()

                else:
                    count = calc.heir_set.filter(polymorphic_ctype_id=self.polymorphic_ctype_id).count()
                if share % count == 0:
                    self.share = share // count
                    self.save()
                else:
                    self.correction=True
                    calc.correction=True
                    self.share = share
                    self.save()
                    calc.save()
            else:
                self.share=share
                self.save()
            return self.share
        else:
            return 0
    def set_shortage_share(self, calc):
        if calc.shortage == True:
            if calc.has_spouse():
                spouse = calc.get_spouse().first()
                remainder = calc.shares_shorted - spouse.shorted_share
                shorted_types = calc.heir_set.not_instance_of(Husband, Wife).values('polymorphic_ctype_id','share').annotate(total=Count('id'))
                if shorted_types.count() == 1:
                    if self.shared_quote == True:
                        count = calc.heir_set.filter(polymorphic_ctype_id=self.polymorphic_ctype_id).count()
                        if remainder % count == 0:
                            self.shorted_share = remainder // count
                        else:
                            self.correction=True
                            calc.correction=True
                            self.shorted_share = remainder
                            calc.save()
                    else :
                        self.shorted_share = remainder
                elif shorted_types.count() > 1:
                    self.shorted_share = remainder
                    self.shortage_calc = True
                    calc.shortage_calc = True
                    calc.save()
            else:
                self.shorted_share = self.share
        self.save()
        return self.shorted_share
    def set_shortage_calc_share(self, calc):
        if self.shortage_calc == True:
            share = calc.shortage_calc_shares * self.get_fraction().numerator // self.get_fraction().denominator
            if self.shared_quote == True:
                count = calc.heir_set.filter(polymorphic_ctype_id=self.polymorphic_ctype_id).count()
                if share % count == 0:
                    self.shortage_calc_share = share // count
                    self.save()
                else:
                    self.correction=True
                    calc.correction=True
                    self.share = share
                    self.save()
                    calc.save()
            else:
                self.shortage_calc_share=share
                self.save()
            return self.shortage_calc_share
    def set_shortage_union_share(self, calc):
            self.shortage_union_share = self.shortage_calc_share * self.shorted_share
            self.save()

    def set_asaba_share(self,calc):
        if self.asaba == True:
            if calc.common_quote == True:
                share = calc.shares * self.get_fraction().numerator // self.get_fraction().denominator
                count = calc.heir_set.instance_of(MaternalSister, MaternalBrother, Sister, Brother).count()
                if share % count == 0:
                    self.share = share // count
                    self.save()
                else:
                    self.correction=True
                    calc.correction=True
                    self.share = share
                    self.save()
                    calc.save()
            else:
                shares = calc.shares
                remainder = calc.residual_shares
                asaba_count = calc.heir_set.filter(asaba=True).count()
                if asaba_count == 1:
                    self.share = remainder
                else:
                    #check for correction
                    males = calc.heir_set.filter(asaba=True, sex='M').count()
                    females = calc.heir_set.filter(asaba=True, sex='F').count()
                    if males == asaba_count or females == asaba_count:
                        if remainder % asaba_count == 0:
                            self.share = remainder // asaba_count
                        else:
                            self.share = remainder
                            self.correction = True
                            calc.correction = True
                            calc.save()
                    elif remainder % (males*2+females) == 0:
                        if self.sex == "M":
                            self.share = remainder // (2 * males + females) * 2
                        else:
                            self.share = remainder // (2 * males + females)
                    else:
                        self.share= remainder
                        self.correction = True
                        calc.correction = True
                        calc.save()
                self.save()
            return self.share

    def set_asaba_quote(self, calc):
        remainder = calc.residual_shares
        shares =  calc.shares
        if remainder > 0 and shares > 0:
            if self.quote == 0:
                quote = remainder / calc.shares
                self.quote = quote
                self.save()
            else:
                quote = (remainder + self.share )/calc.shares
                self.quote = quote
                self.save()
        elif calc.common_quote == True:
            self.quote = 1/3
            self.quote_reason = _("Asaba with maternal siblings share 1/3")
            self.shared_quote = True
            self.save()

    def get_corrected_share(self, calc):
        correction_set = calc.heir_set.filter(correction=True).values('polymorphic_ctype_id','quote').annotate(total=Count('id'))
        asaba_set = calc.heir_set.filter(asaba=True).values('polymorphic_ctype_id','quote').annotate(total=Count('id'))
        if calc.correction==True and calc.shares_corrected != 0:
            if calc.excess == True:
                multiplier = calc.shares_corrected // calc.shares_excess
                share = self.share
            elif calc.shortage == True:
                multiplier = calc.shares_corrected // calc.shares_shorted
                share = self.shorted_share
            else:
                multiplier = calc.shares_corrected // calc.shares
                share = self.share
            if calc.common_quote == True:
                self.corrected_share = share
            elif correction_set.count() == 1:
                if self.shared_quote == True:
                    self.corrected_share = share
                else:
                    self.corrected_share = share * multiplier
            elif self.asaba == True and asaba_set.count() == 2 :
                males = calc.heir_set.filter(asaba=True, sex='M').count()
                females = calc.heir_set.filter(asaba=True, sex='F').count()
                asaba_count = calc.heir_set.filter(asaba=True).count()

                if self.sex == "M":
                    self.corrected_share = share * multiplier // (2 * males + females) * 2
                else:
                    self.corrected_share = share * multiplier // (2 * males + females)
            else :
                count = calc.heir_set.filter(polymorphic_ctype_id=self.polymorphic_ctype_id).count()
                if self.shared_quote == True:
                    self.corrected_share = share * multiplier // count
                else:
                    self.corrected_share = share * multiplier

            self.save()
            return self.corrected_share

    def set_amount(self, calc):
        estate = calc.deceased_set.first().estate
        amount = 0
        if calc.correction == False:
            if calc.excess == True:
                amount = estate / calc.shares_excess * self.share
            elif calc.shortage == True:
                if calc.shortage_calc == True:
                    amount = estate / calc.shortage_union_shares * self.shortage_union_share
                else:
                    amount = estate / calc.shares_shorted * self.shorted_share
            else:
                amount = estate / calc.shares * self.share
        else:
            amount = estate / calc.shares_corrected * self.corrected_share
        self.amount = amount
        self.save()
    def get_fraction(self):
        return Fraction(self.quote).limit_denominator()
    def clear(self):
        self.quote = 0
        self.shared_quote = False
        self.share = 0
        self.corrected_share = 0
        self.shorted_share = 0
        self.amount = 0
        self.asaba = False
        self.blocked = False
        self.quote_reason = ""
        self.correction = False
        self.shortage_calc = False
        self.shortage_calc_share  = 0
        self.shortage_union_share  = 0
        self.save()

class Father(Heir):
    """Father class"""
    def add(self, calc):
        calc.deceased_set.first().add_father(father=self)
    def get_quote(self, calc):
        if calc.has_male_descendent():
            self.quote = 1/6
            self.quote_reason = _("father gets 1/6 prescribed share because of male descendant")
        elif calc.has_female_descendent():
            self.quote = 1/6
            #self.asaba = True
            self.quote_reason = _("father gets 1/6 plus remainder because of female descendant")
        else:
            self.asaba = True
            self.quote_reason = _("father gets the remainder because there is no descendant")
        self.save()
        return self.quote


class Mother(Heir):
    """Mother class"""
    def add(self, calc):
        calc.deceased_set.first().add_mother(mother=self)

    def get_quote(self, calc):
        if calc.has_descendent():
            self.quote = 1/6
            self.quote_reason = _("mother gets 1/6 because of descendant")
        elif calc.has_siblings():
            self.quote = 1/6
            self.quote_reason = _("mother gets 1/6 because of siblings")
        elif calc.has_spouse() and calc.has_father():
            if calc.deceased_set.first().sex == 'M':
                self.quote = 1/4
                self.quote_reason = _("mother gets 1/3 of the remainder which is 1/4.")
            else:
                self.quote = 1/6
                self.quote_reason = _("mother gets 1/3 of the remainder which is 1/6")
        else:
            self.quote = 1/3
            self.quote_reason = _("mother gets 1/3 because no descendant or siblings")
        self.save()
        return self.quote



class Husband(Heir):
    """Husbnad class"""
    def add(self, calc):
        calc.deceased_set.first().add_husband(husband=self)

    def get_quote(self, calc):
        if calc.has_descendent():
            self.quote = 1/4
            self.quote_reason = _("husband gets 1/4 becuase of descendant")
        else:
            self.quote = 1/2
            self.quote_reason = _("husband gets 1/2 becuase there is no descendant")
        self.save()
        return self.quote

class Wife(Heir):
    """Wife class"""
    def add(self, calc):
        calc.deceased_set.first().add_wife(wife=self)

    def get_quote(self, calc):
        if calc.heir_set.instance_of(Wife).count() == 1:
            if calc.has_descendent():
                self.quote = 1/8
                self.quote_reason = _("wife gets 1/8 becuase of descendant")
            else:
                self.quote = 1/4
                self.quote_reason = _("wife gets 1/4 becuase there is no descendant")
        else:
            if calc.has_descendent():
                self.quote = 1/8
                self.quote_reason = _("wives share the qoute of 1/8 becuase of descendant")
            else:
                self.quote = 1/4
                self.quote_reason = _("wives share the quote of 1/4 becuase there is no descendant")
            self.shared_quote = True
        self.save()
        return self.quote

class Daughter(Heir):
    """Daughter Class"""
    def add(self, calc, mother, father):
        calc.deceased_set.first().add_daughter(daughter=self, mother=mother, father=father)

    def get_quote(self, calc):
        if calc.has_son():
            self.asaba = True
            self.quote_reason = _("Daughter/s with Son/s share the residuary. The son will receive a share of two daughters.")
            if calc.heir_set.instance_of(Daughter).count() > 1:
                self.shared_quote = True
        elif calc.heir_set.instance_of(Daughter).count() == 1:
            self.quote = 1/2
            self.quote_reason = _("Daughter gets 1/2 when she has no other sibling/s")
        else:
            self.quote = 2/3
            self.shared_quote = True
            self.quote_reason = _("Daughters share the quote of 2/3 when there is no son/s")
        self.save()
        return self.quote

class Son(Heir):
    """Son Class"""
    def add(self, calc, mother, father):
        calc.deceased_set.first().add_son(son=self, mother=mother, father=father)

    def get_quote(self, calc):
        if calc.heir_set.instance_of(Son).count() > 1:
            self.shared_quote = True
        self.asaba =  True
        self.quote_reason = _("Son/s share the remainder or all amount if no other heir exist")
        self.save()
        return self.quote

class Brother(Heir):
    """Brother Class"""
    def add(self, calc):
        calc.deceased_set.first().add_brother(brother=self)

    def get_quote(self, calc):
        brothers = calc.heir_set.instance_of(Brother)
        if brothers.count() > 1:
            self.shared_quote = True
        if calc.has_male_descendent():
            self.blocked = True
            self.quote_reason = _("Bother/s are blocked by male descendant")
        elif calc.has_father():
            self.blocked = True
            self.quote_reason = _("Brother/s are blocked by father")
        elif calc.has_grandFather():
            self.blocked = True
            self.quote_reason = _("Brother/s are blocked by grandfather")
        else:
            self.asaba =  True
            self.quote_reason = _("Brother/s share the remainder or all amount if no other heir exist")
        self.save()
        return self.quote

class Sister(Heir):
    """Sister Class"""
    def add(self, calc):
        calc.deceased_set.first().add_sister(sister=self)

    def get_quote(self, calc):
        sisters = calc.heir_set.instance_of(Sister)
        if sisters.count() > 1:
            self.shared_quote = True
        if calc.has_male_descendent():
            self.blocked = True
            self.quote_reason = _("Sister/s are blocked by male descendant")
        elif calc.has_father():
            self.blocked = True
            self.quote_reason = _("Sister/s are blocked by father")
        elif calc.has_grandFather():
            self.blocked = True
            self.quote_reason = _("Sister/s are blocked by grandfather")
        elif calc.has_brother():
            self.asaba = True
            self.quote_reason = _("Sister/s with borther/s share the remainder or all the amount if no other heir exist. The brother will receive a share of two sisters")
        elif calc.has_female_descendent():
            self.asaba = True
            self.quote_reason = _("Sister/s with female descendant share the remainder")
        else:
            if sisters.count() == 1:
                self.quote = 1/2
                self.quote_reason = _("Sister gets half when no father or son. ")
            else:
                self.quote = 2/3
                self.quote_reason = _("Sisters share 2/3 when no father or son.")
        self.save()
        return self.quote

class GrandFather(Heir):
    """GrandFather Class"""
    def add(self, calc):
        calc.deceased_set.first().add_grandFather(grandFather=self)

    def get_quote(self, calc):
        if calc.has_father():
            self.blocked = True
            self.quote_reason = _("Grandfather is blocked by father")
        elif calc.has_male_descendent():
            self.quote = 1/6
            self.quote_reason = _("Grandfather gets 1/6 prescribed share because of male descendant")
        elif calc.has_female_descendent():
            self.quote = 1/6
            #self.asaba = True
            self.quote_reason = _("Grandfather gets 1/6 plus remainder because of female descendant")
        else:
            self.asaba = True
            self.quote_reason = _("Grandfather gets the remainder because there is no descendant")
        self.save()
        return self.quote

class GrandMother(Heir):
    """GrandMother class"""
    def add(self, calc):
        calc.deceased_set.first().add_grandMother(grandMother=self)

    def get_quote(self, calc):
        if calc.has_mohter():
            self.blocked = True
            self.quote_reason = _("Grandmother is blocked by mother")
        else:
            grandmothers = calc.heir_set.instance_of(GrandMother)
            if grandmothers.count() > 1:
                self.shared_quote = True
            self.quote = 1/6
            self.quote_reason = _("Grandmother gets 1/6 if no mother")
        self.save()
        return self.quote

class SonOfSon(Heir):
    """SonOfSon class"""
    def add(self, calc):
        calc.deceased_set.first().add_sonOfSon(son=self)

    def get_quote(self, calc):
        if calc.has_son():
            self.blocked = True
            self.quote_reason = _("Son of son is blocked by Son")
        else:
            if calc.heir_set.instance_of(SonOfSon).count() > 1:
                self.shared_quote = True
            self.asaba = True
            self.quote_reason = _("Son of son share the remainder or all amount if no other heir exist")
        self.save()
        return self.quote

class DaughterOfSon(Heir):
    """DaughterOfSon Class"""
    def add(self, calc, ):
        calc.deceased_set.first().add_daughterOfSon(daughter=self)

    def get_quote(self, calc):
        daughtersOfSon = calc.heir_set.instance_of(DaughterOfSon)
        if daughtersOfSon.count() > 1:
            self.shared_quote = True
        if calc.has_son():
            self.blocked = True
            self.quote_reason = _("Daughter of son is blocked by son")
        elif calc.has_sonOfSon():
            self.asaba = True
            self.quote_reason = _("Daughter/s of son with Son/s of son share the residuary. The son of son will receive a share of two daughters of son.")
        elif calc.has_daughter():
            daughters = calc.heir_set.instance_of(Daughter)
            if daughters.count()==1:
                self.quote = 1/6
                self.quote_reason = _("Daughter of son get 1/6, with daughter")
            else:
                self.blocked = True
                self.quote_reason = _("Daughter/s of son are blocked by daugters")
        elif daughtersOfSon.count() == 1:
            self.quote = 1/2
            self.quote_reason = _("Daughter of son gets 1/2 when she has no other sibling/s")
        else:
            self.quote = 2/3
            self.quote_reason = _("Daughters of son share the quote of 2/3 when there is no son/s of son")
        self.save()
        return self.quote


class PaternalSister(Heir):
    """PaternalSister Class"""
    def add(self, calc):
        calc.deceased_set.first().add_paternalSister(sister=self)

    def get_quote(self, calc):
        paternalSisters = calc.heir_set.instance_of(PaternalSister)
        if paternalSisters.count() > 1:
            self.shared_quote = True
        if calc.has_male_descendent():
            self.blocked = True
            self.quote_reason = _("Paternal sister/s are blocked by male descendant")
        elif calc.has_father():
            self.blocked = True
            self.quote_reason = _("Paternal sister/s are blocked by father")
        elif calc.has_grandFather():
            self.blocked = True
            self.quote_reason = _("Paternal sister/s are blocked by grandfather")
        elif calc.has_brother():
            self.blocked = True
            self.quote_reason = _("Paternal sister/s are blocked by borther/s")
        elif calc.has_paternalBrother():
            self.asaba = True
            self.quote_reason = _("Paternal sister/s with paternal half borther/s share the remainder or all the amount if no other heir exist. The brother will receive a share of two sisters")
        elif calc.has_sister():
            sisters= calc.heir_set.instance_of(Sister)
            if sisters.count()==1:
                self.quote = 1/6
                self.quote_reason = _("Paternal sister/s get 1/6 with sister")
            else:
                self.blocked = True
                self.quote_reason = _("Paternal sisters/s are blocked by sisters")
        elif calc.has_female_descendent():
            self.asaba = True
            self.quote_reason = _("Paternal sister/s with female descendant share the remainder")
        elif paternalSisters.count() == 1:
            self.quote = 1/2
            self.quote_reason = _("Paternal sister gets half when no father or son. ")
        else:
            self.quote = 2/3
            self.quote_reason = _("Paternal sisters share 2/3 when no father or son.")
        self.save()
        return self.quote

class PaternalBrother(Heir):
    """PaternalBrother Class"""
    def add(self, calc):
        calc.deceased_set.first().add_paternalBrother(brother=self)

    def get_quote(self, calc):
        paternalBrothers = calc.heir_set.instance_of(PaternalBrother)
        if paternalBrothers.count() > 1:
            self.shared_quote = True
        if calc.has_male_descendent():
            self.blocked = True
            self.quote_reason = _("Paternal brother/s are blocked by male descendant")
        elif calc.has_father():
            self.blocked = True
            self.quote_reason = _("Paternal brother/s are blocked by father")
        elif calc.has_grandFather():
            self.blocked = True
            self.quote_reason = _("Paternal brother/s are blocked by grandfather")
        elif calc.has_brother():
            self.blocked = True
            self.quote_reason = _("Paternal brother/s are blocked by brothers")
        elif calc.has_sister():
            asaba = calc.get_sisters().filter(asaba=True)
            if asaba:
                self.blocked = True
                self.quote_reason = _("Paternal brother/s are blocked by sisters")
            else:
                self.asaba = True
                self.quote_reason = _("Paternal brother/s share the remainder or all amount if no other heir exist")
        else:
            self.asaba =  True
            self.quote_reason = _("Paternal brother/s share the remainder or all amount if no other heir exist")
        self.save()
        return self.quote

class MaternalSister(Heir):
    """MaternalSister Class"""
    def add(self, calc):
        calc.deceased_set.first().add_maternalSister(sister=self)

    def get_quote(self, calc):
        maternalSisters = calc.heir_set.instance_of(MaternalSister)
        if maternalSisters.count() > 1:
            self.shared_quote = True
        if calc.has_descendent():
            self.blocked = True
            self.quote_reason = _("Maternal sister/s are blocked by descendant")
        elif calc.has_father():
            self.blocked = True
            self.quote_reason = _("Maternal sister/s are blocked by father")
        elif calc.has_grandFather():
            self.blocked = True
            self.quote_reason = _("Maternal sister/s are blocked by grandfather")
        elif calc.has_maternalBrother():
            calc.maternal_quote = True
            calc.save()
            self.shared_quote = True
            self.quote = 1/3
            self.quote_reason = _("Maternal sister/s with maternal brother/s share 1/3")
        elif maternalSisters.count() == 1:
            self.quote =  1/6
            self.quote_reason = _("Maternal sister get 1/6")
        else:
            self.quote = 1/3
            self.quote_reason = _("Maternal sisters share 1/3")
        self.save()
        return self.quote

class MaternalBrother(Heir):
    """MaternalBrother Class"""
    def add(self, calc):
        calc.deceased_set.first().add_maternalBrother(brother=self)

    def get_quote(self, calc):
        MaternalBrothers = calc.heir_set.instance_of(MaternalBrother)
        if MaternalBrothers.count() > 1:
            self.shared_quote = True
        if calc.has_descendent():
            self.blocked = True
            self.quote_reason = _("Maternal brother/s are blocked by descendant")
        elif calc.has_father():
            self.blocked = True
            self.quote_reason = _("Maternal brother/s are blocked by father")
        elif calc.has_grandFather():
            self.blocked = True
            self.quote_reason = _("Maternal brother/s are blocked by grandfather")
        elif calc.has_maternalSister():
            calc.maternal_quote = True
            calc.save()
            self.shared_quote = True
            self.quote = 1/3
            self.quote_reason = _("Maternal brother/s with maternal sister/s share 1/3")
        elif MaternalBrothers.count() == 1:
            self.quote =  1/6
            self.quote_reason = _("Maternal brother get 1/6")
        else:
            self.quote = 1/3
            self.quote_reason = _("Maternal brothers share 1/3")
        self.save()
        return self.quote

class SonOfBrother(Heir):
    """Son of Brother class"""
    def add(self, calc):
        calc.deceased_set.first().add_sonOfBrother(sonOfBrother=self)

    def get_quote(self, calc):
        sonsOfBrother = calc.heir_set.instance_of(SonOfBrother)
        if sonsOfBrother.count() > 1:
            self.shared_quote = True
        if calc.has_male_descendent():
            self.blocked = True
            self.quote_reason = _("Son/s of Brother are blocked by male descendant")
        elif calc.has_father():
            self.blocked = True
            self.quote_reason = _("Son/s of Brother are blocked by father")
        elif calc.has_grandFather():
            self.blocked = True
            self.quote_reason = _("Son/s of Brother are blocked by grandfather")
        elif calc.has_brother():
            self.blocked = True
            self.quote_reason = _("Son/s of Brother are blocked by brother/s")
        elif calc.get_sisters().filter(asaba=True):
            self.blocked = True
            self.quote_reason = _("Son/s of Brother are blocked by sisters")
        elif calc.has_paternalBrother():
            self.blocked = True
            self.quote_reason = _("Son/s of Brother are blocked by paternal brother/s")
        elif calc.get_paternalSisters().filter(asaba=True):
            self.blocked = True
            self.quote_reason = _("Son/s of Brother are blocked by paternal sister/s")
        else:
            self.asaba =  True
            self.quote_reason = _("Son/s of Brother share the remainder or all amount if no other heir exist")
        self.save()
        return self.quote

class SonOfPaternalBrother(Heir):
    """Son of Paternal Brother class"""
    def add(self, calc):
        calc.deceased_set.first().add_sonOfPaternalBrother(sonOfPaternalBrother=self)

    def get_quote(self, calc):
        sonsOfPaternalBrother = calc.heir_set.instance_of(SonOfPaternalBrother)
        if sonsOfPaternalBrother.count() > 1:
            self.shared_quote = True
        if calc.has_male_descendent():
            self.blocked = True
            self.quote_reason = _("Son/s of Paternal Brother are blocked by male descendant")
        elif calc.has_father():
            self.blocked = True
            self.quote_reason = _("Son/s of Paternal Brother are blocked by father")
        elif calc.has_grandFather():
            self.blocked = True
            self.quote_reason = _("Son/s of Paternal Brother are blocked by grandfather")
        elif calc.has_brother():
            self.blocked = True
            self.quote_reason = _("Son/s of Paternal Brother are blocked by brother/s")
        elif calc.get_sisters().filter(asaba=True):
            self.blocked = True
            self.quote_reason = _("Son/s of Paternal Brother are blocked by sisters")
        elif calc.has_paternalBrother():
            self.blocked = True
            self.quote_reason = _("Son/s of Paternal Brother are blocked by paternal brother/s")
        elif calc.get_paternalSisters().filter(asaba=True):
            self.blocked = True
            self.quote_reason = _("Son/s of Paternal Brother are blocked by paternal sister/s")
        elif calc.has_sonOfBrother():
            self.blocked = True
            self.quote_reason = _("Son/s of Paternal Brother are blocked by sons of brother")
        else:
            self.asaba =  True
            self.quote_reason = _("Son/s of Paternal Brother share the remainder or all amount if no other heir exist")
        self.save()
        return self.quote

class Uncle(Heir):
    """Uncle class"""
    def add(self, calc):
        calc.deceased_set.first().add_uncle(uncle=self)

    def get_quote(self, calc):
        uncles = calc.heir_set.instance_of(Uncle)
        if uncles.count() > 1:
            self.shared_quote = True
        if calc.has_male_descendent():
            self.blocked = True
            self.quote_reason = _("Uncle/s are blocked by male descendant")
        elif calc.has_father():
            self.blocked = True
            self.quote_reason = _("Uncle/s are blocked by father")
        elif calc.has_grandFather():
            self.blocked = True
            self.quote_reason = _("Uncle/s are blocked by grandfather")
        elif calc.has_brother():
            self.blocked = True
            self.quote_reason = _("Uncle/s are blocked by brother/s")
        elif calc.get_sisters().filter(asaba=True):
            self.blocked = True
            self.quote_reason = _("Uncle/s are blocked by sisters")
        elif calc.has_paternalBrother():
            self.blocked = True
            self.quote_reason = _("Uncle/s are blocked by paternal brother/s")
        elif calc.get_paternalSisters().filter(asaba=True):
            self.blocked = True
            self.quote_reason = _("Uncle/s are blocked by paternal sister/s")
        elif calc.has_sonOfBrother():
            self.blocked = True
            self.quote_reason = _("Uncle/s are blocked by sons of brother")
        elif calc.has_sonOfPaternalBrother():
            self.blocked = True
            self.quote_reason = _("Uncle/s are blocked by sons of paternal brother")
        else:
            self.asaba =  True
            self.quote_reason = _("Uncle/s share the remainder or all amount if no other heir exist")
        self.save()
        return self.quote

class PaternalUncle(Heir):
    """Paternal Uncle class"""
    def add(self, calc):
        calc.deceased_set.first().add_paternalUncle(uncle=self)

    def get_quote(self, calc):
        paternalUncles = calc.heir_set.instance_of(PaternalUncle)
        if paternalUncles.count() > 1:
            self.shared_quote = True
        if calc.has_male_descendent():
            self.blocked = True
            self.quote_reason = _("Paternal Uncle/s are blocked by male descendant")
        elif calc.has_father():
            self.blocked = True
            self.quote_reason = _("Paternal Uncle/s are blocked by father")
        elif calc.has_grandFather():
            self.blocked = True
            self.quote_reason = _("Paternal Uncle/s are blocked by grandfather")
        elif calc.has_brother():
            self.blocked = True
            self.quote_reason = _("Paternal Uncle/s are blocked by brother/s")
        elif calc.get_sisters().filter(asaba=True):
            self.blocked = True
            self.quote_reason = _("Paternal Uncle/s are blocked by sisters")
        elif calc.has_paternalBrother():
            self.blocked = True
            self.quote_reason = _("Paternal Uncle/s are blocked by paternal brother/s")
        elif calc.get_paternalSisters().filter(asaba=True):
            self.blocked = True
            self.quote_reason = _("Paternal Uncle/s are blocked by paternal sister/s")
        elif calc.has_sonOfBrother():
            self.blocked = True
            self.quote_reason = _("Paternal Uncle/s are blocked by sons of brother")
        elif calc.has_sonOfPaternalBrother():
            self.blocked = True
            self.quote_reason = _("Paternal Uncle/s are blocked by sons of paternal brother")
        elif calc.has_uncle():
            self.blocked = True
            self.quote_reason = _("Paternal Uncle/s are blocked by uncle/s")
        else:
            self.asaba =  True
            self.quote_reason = _("Paternal Uncle/s share the remainder or all amount if no other heir exist")
        self.save()
        return self.quote

class SonOfUncle(Heir):
    """Son of Uncle class"""
    def add(self, calc):
        calc.deceased_set.first().add_sonOfUncle(sonOfUncle=self)

    def get_quote(self, calc):
        sonsOfUncle = calc.heir_set.instance_of(SonOfUncle)
        if sonsOfUncle.count() > 1:
            self.shared_quote = True
        if calc.has_male_descendent():
            self.blocked = True
            self.quote_reason = _("Son/s of uncle are blocked by male descendant")
        elif calc.has_father():
            self.blocked = True
            self.quote_reason = _("Son/s of Uncle/s are blocked by father")
        elif calc.has_grandFather():
            self.blocked = True
            self.quote_reason = _("Son/s of Uncle/s are blocked by grandfather")
        elif calc.has_brother():
            self.blocked = True
            self.quote_reason = _("Son/s of Uncle/s are blocked by brother/s")
        elif calc.get_sisters().filter(asaba=True):
            self.blocked = True
            self.quote_reason = _("Son/s of Uncle/s are blocked by sisters")
        elif calc.has_paternalBrother():
            self.blocked = True
            self.quote_reason = _("Son/s of Uncle/s are blocked by paternal brother/s")
        elif calc.get_paternalSisters().filter(asaba=True):
            self.blocked = True
            self.quote_reason = _("Son/s of Uncle/s are blocked by paternal sister/s")
        elif calc.has_sonOfBrother():
            self.blocked = True
            self.quote_reason = _("Son/s of Uncle/s are blocked by sons of brother")
        elif calc.has_sonOfPaternalBrother():
            self.blocked = True
            self.quote_reason = _("Son/s of Uncle/s are blocked by sons of paternal brother")
        elif calc.has_uncle():
            self.blocked = True
            self.quote_reason = _("Son/s of Uncle/s are blocked by uncle/s")
        elif calc.has_paternalUncle():
            self.blocked = True
            self.quote_reason = _("Son/s of Uncle/s are blocked by paternal uncle/s")
        else:
            self.asaba =  True
            self.quote_reason = _("Son/s of Uncle/s share the remainder or all amount if no other heir exist")
        self.save()
        return self.quote

class SonOfPaternalUncle(Heir):
    """Son of Paternal Uncle class"""
    def add(self, calc):
        calc.deceased_set.first().add_sonOfPaternalUncle(sonOfPaternalUncle=self)

    def get_quote(self, calc):
        sonsOfPaternalUncle = calc.heir_set.instance_of(SonOfPaternalUncle)
        if sonsOfPaternalUncle.count() > 1:
            self.shared_quote = True
        if calc.has_male_descendent():
            self.blocked = True
            self.quote_reason = _("Son/s of paternal uncle are blocked by male descendant")
        elif calc.has_father():
            self.blocked = True
            self.quote_reason = _("Son/s of paternal Uncle/s are blocked by father")
        elif calc.has_grandFather():
            self.blocked = True
            self.quote_reason = _("Son/s of paternal Uncle/s are blocked by grandfather")
        elif calc.has_brother():
            self.blocked = True
            self.quote_reason = _("Son/s of paternal Uncle/s are blocked by brother/s")
        elif calc.get_sisters().filter(asaba=True):
            self.blocked = True
            self.quote_reason = _("Son/s of paternal Uncle/s are blocked by sisters")
        elif calc.has_paternalBrother():
            self.blocked = True
            self.quote_reason = _("Son/s of paternal Uncle/s are blocked by paternal brother/s")
        elif calc.get_paternalSisters().filter(asaba=True):
            self.blocked = True
            self.quote_reason = _("Son/s of paternal Uncle/s are blocked by paternal sister/s")
        elif calc.has_sonOfBrother():
            self.blocked = True
            self.quote_reason = _("Son/s of paternal Uncle/s are blocked by sons of brother")
        elif calc.has_sonOfPaternalBrother():
            self.blocked = True
            self.quote_reason = _("Son/s of paternal Uncle/s are blocked by sons of paternal brother")
        elif calc.has_uncle():
            self.blocked = True
            self.quote_reason = _("Son/s of paternal Uncle/s are blocked by uncle/s")
        elif calc.has_paternalUncle():
            self.blocked = True
            self.quote_reason = _("Son/s of paternal Uncle/s are blocked by paternal uncle/s")
        elif calc.has_sonOfUncle():
            self.blocked = True
            self.quote_reason = _("Son/s of paternal Uncle/s are blocked by son/s of uncle/s")
        else:
            self.asaba =  True
            self.quote_reason = _("Son/s of paternal Uncle/s share the remainder or all amount if no other heir exist")
        self.save()
        return self.quote
