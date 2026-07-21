1. AuhZ, AuthN, RBAC (Customer, Cleaner, Manager)
2. Booking Life cycle (submitted -> assigned -> in-progress -> completed/cancelled)
3. Customer Picks a date, hours, address, apartment size
4. Offices Recurring booking.
5. Manager assigns Cleaners manually based on cleaner_id
6. Cleaners can view their scheduled task via /tasks (notification)
7. Cleaners clicks Job done button to indicate the job is done, and how much money was collected. sets the Booking to (completed)
8. Manager is able to see how much money was collected by cleaners, sees who is assigned to which. assign roles to accounts signed in (Customer, Cleaner)
9.  Structured logging
10. Measure before/after
11. Tests with testcontainers
12. Docker compose the project