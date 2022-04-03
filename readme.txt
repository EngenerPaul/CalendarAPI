This is a special calendar for teacher's work.
Here every student can sign up for a lesson on a specific date and time.
Any user can see schedule but only registered user can sign up for the lesson.
The app homepage: https://calendarapi-kpa.herokuapp.com/
The developed API can be used in a application for use by the admin and any user.

Additionally developed an application to check work of all requests. Git: https://github.com/EngenerPaul/CalendarAPI-requests/

API:
1)
    Descriptions: registration
    path: api/registration
    HTTP method: POST
    Permission: AllowAny
    Parameter content type: JSON
    Body: username, first_name, password, phone, relation (choice: Telegram, WhatsApp, Both)
    Response: username, first_name, password, phone, relation, id

2)
    Descriptions: get JWT token
    path: auth/jwt/create
    HTTP method: POST
    Permission: AllowAny
    Parameter content type: JSON
    Body: username, password
    Response: refresh, access

3)
    Descriptions: delete user
    path: api/delete-user/{pk}/
    HTTP method: DELETE
    Permission: IsAdminUser

4)
    Descriptions: get list of students
    path: api/get-users
    HTTP method: GET
    Permission: IsAdminUser
    Parameter content type: JSON
    Body:
    Response: list of students dictionary: id, username, password, first_name, is_staff, details. Details is dictionary: phone, telegram, whatsapp.

5)
    Descriptions: get a list of all future lessons
    path: api/get-relevant-lessons
    HTTP method: GET
    Permission: AllowAny
    Parameter content type: JSON
    Body: username, password
    Response: list of lessons: id, student, theme, salary, time, date

6)
    Descriptions: get a list of own lessons by student
    path: api/set-my-lessons
    HTTP method: GET
    Permission: IsAuthenticated
    Parameter content type: JSON
    Response: list of lessons: id, student, theme, salary, time, date

7)
    Descriptions: create a new lesson by student
    path: api/set-my-lessons
    HTTP method: POST
    Permission: IsAuthenticated
    Parameter content type: JSON
    Body: theme, salary, time, date
    Response: id, student, theme, salary, time, date

8)
    Descriptions: update the whole own lesson by student
    path: api/set-my-lessons/{id}/
    HTTP method: PUT
    Permission: IsAuthenticated
    Parameter content type: JSON
    Body: theme, salary, time, date
    Response: id, student, theme, salary, time, date

9)
    Descriptions: update the own lesson by student
    path: api/set-my-lessons/{id}/
    HTTP method: PATCH
    Permission: IsAuthenticated
    Parameter content type: JSON
    Body: any of theme, salary, time, date
    Response: id, student, theme, salary, time, date

10)
    Descriptions: delete the own lesson by student
    path: api/set-my-lessons/{id}/
    HTTP method: DELETE
    Permission: IsAuthenticated
    Parameter content type: JSON

11)
    Descriptions: get a list of all future lessons
    path: api/all-relevant-lessons
    HTTP method: GET
    Permission: IsAdminUser
    Response: list of all future lessons: id, student, theme, salary, time, date

12)
    Descriptions: get all lessons by admin
    path: api/all-lessons
    HTTP method: GET
    Permission: IsAdminUser
    Response: list of all lessons: id, student, theme, salary, time, date

13)
    Descriptions: create a new lesson by admin for the sudent
    path: api/all-lessons
    HTTP method: POST
    Permission: IsAdminUser
    Parameter content type: JSON
    Body: student, theme, salary, time, date
    Response: id, student, theme, salary, time, date

14)
    Descriptions: update the whole student's lesson by admin
    path: api/all-lessons/{id}/
    HTTP method: PUT
    Permission: IsAdminUser
    Parameter content type: JSON
    Body: theme, salary, time, date
    Response: id, student, theme, salary, time, date

15)
    Descriptions: update the student's lesson by admin
    path: api/all-lessons/{id}/
    HTTP method: PATCH
    Permission: IsAdminUser
    Parameter content type: JSON
    Body: any of student, theme, salary, time, date
    Response: id, student, theme, salary, time, date

16)
    Descriptions: delete the student's lesson by admin
    path: api/all-lessons/{id}/
    HTTP method: DELETE
    Permission: IsAdminUser
    Parameter content type: JSON
