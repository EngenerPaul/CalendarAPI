import datetime


С_morning_time = datetime.time(hour=8)  # start of business hours
С_morning_time_markup = datetime.time(hour=10)  # until that time the salary is high
C_evening_time_markup = datetime.time(hour=21)  # after that time the salary is high
C_evening_time = datetime.time(hour=23)  # end of business hours

C_salary_common = 700  # min salary
C_salary_high = 1000  # salary for morning and evening hours
C_salary_max = C_salary_common * 10 - 1  # to avoid mistakes

C_timedelta = datetime.timedelta(hours=6)  # students need to book lessons in advance
C_datedelta = datetime.timedelta(days=10)  # unable to sign up for lessons too early
