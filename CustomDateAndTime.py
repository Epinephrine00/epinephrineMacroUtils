from __future__ import annotations

class date:
    isLeap = False
    def __init__(self, year:int, month:int, day:int):
        self.year = year
        self.month = month
        self.day = day
        self.dateFormat = "yyyymmdd"
        self.updateLeap()
        self.validateDate()
        
    def updateLeap(self):
        self.isLeap = (self.year%4==0) and (self.year%100!=0)
    
    def __eq__(self, value:object, /) -> bool:
        try:
            if value.year==self.year and value.month==self.month and value.day==self.day:
                return True
        except:
            pass
        return False
    
    def isBefore(self, value:date) -> bool:
        if self.year<value.year:
            return True
        elif self.year>value.year:
            return False
        else:
            if self.month<value.month:
                return True
            elif self.month>value.month:
                return False
            else:
                if self.day<value.day:
                    return True
        return False
    def isAfter(self, value:date) -> bool:
        if self.year<value.year:
            return False
        elif self.year>value.year:
            return True
        else:
            if self.month<value.month:
                return False
            elif self.month>value.month:
                return True
            else:
                if self.day>value.day:
                    return True
        return False
    
    def validateDate(self):
        startYear = self.year
        daybymonth = [31, 28+self.isLeap, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if self.day<0:
            self.month-=1
            self.day += daybymonth[self.month%12]
            self.validateDate()
            return
        elif self.day>daybymonth[self.month%12]:
            self.day-=daybymonth[self.month%12]
            self.month+=1
            self.validateDate()
            return
        
        if not self.month in range(13)[1:]:
            self.year += (self.month-1)//12
            self.month = self.month%12
            self.month = self.month if self.month else 12
    
    def __repr__(self):
        return self.dateFormat.replace('yyyy', '%04d'%self.year).replace('yy', '%02d'%(self.year%100)).replace('mm', '%02d'%self.month).replace('dd', '%02d'%self.day)


class time:
    def __init__(self, hour:int, minute:int, second:int = 0):
        self.hour = hour
        self.minute = minute
        self.second = second
        self.dateFormat = "hhmmss"
        self.validateTime()

    def validateTime(self):
        
        self.minute += self.second//60
        self.second %= 60

        self.hour += self.minute//60
        self.minute  %= 60

        self.hour %= 24

    def __eq__(self, value:object, /) -> bool:
        try:
            if value.hour==self.hour and value.minute==self.minute and value.second==self.second:
                return True
        except:
            pass
        return False
    
    def isBefore(self, value:time) -> bool:
        if self.hour<value.hour:
            return True
        elif self.hour>value.hour:
            return False
        else:
            if self.minute<value.minute:
                return True
            elif self.minute>value.minute:
                return False
            else:
                if self.second<value.second:
                    return True
        return False
    def isAfter(self, value:time) -> bool:
        if self.hour<value.hour:
            return False
        elif self.hour>value.hour:
            return True
        else:
            if self.minute<value.minute:
                return False
            elif self.minute>value.minute:
                return True
            else:
                if self.second>value.second:
                    return True
        return False
    
    def __repr__(self):
        return self.dateFormat.replace('hh', '%02d'%self.hour).replace('mm', '%02d'%self.minute).replace('ss', '%02d'%self.second)

    


if __name__=="__main__":
    d = date(2024, 12, 33)
    d.dateFormat = "yy.mm.dd"
    e = date(2024, 10, 31)

    n = time(11, 3, 23)
    print(e.isAfter(e))
    print(d)

    print(n)
