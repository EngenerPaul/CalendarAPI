import datetime


С_morning_time = datetime.time(hour=8)  # start of business hours
С_morning_time_markup = datetime.time(hour=10)  # until that time the salary is high
C_evening_time_markup = datetime.time(hour=22)  # after that time the salary is high
C_evening_time = datetime.time(hour=23)  # end of business hours

C_salary_common = 1000  # min salary
C_salary_high = 1300  # salary for morning and evening hours

C_timedelta = datetime.timedelta(hours=3)  # students need to book lessons in advance
C_datedelta = datetime.timedelta(days=7)  # unable to sign up for lessons too early

C_lesson_threshold = 5  # >= this value a lesson cost will be higher
