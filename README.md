# wework-desk-finder

Python CLI tool and library to poll and book Wework floors.

## Requirements

- Python 3.10+
- A wework account


## Authentication

While the script uses username/password authentication for convenience, the wework_authentication module also supports the usage of a refresh_token and client_id instead.


## FloorID

Wework uses an incremental integer internally to identify desk floors. Any endpoint involving a floor requires passing its FloorID

To find your desired FloorID, you can use your browser's dev tools and look at the request flow while you brose available floors and days.
Look for these XHR requests:

- Method: GET
- Domain: members.wework.com
- File: 
    - get-floor-details?buildingId=<<building_id>>&floorId=<<floor_id>>&...
    - get-floor-capacity?buildingId=<<building_id>>&floorId=<<floor_id>>&...


## Usage

Book a desk on FloorID 123 for July 23rd 2027, using all default parameters:

```bash
python booker.py -u my_username -fi 123 -d 07/23/27
>Wework password: my_password
```

Skipping the username from the args:

```bash
python booker.py -fi 123 -d 07/23/27
>Wework username: my_username
>Wework password: my_password
```

Book a desk in one of 3 different floors:

```bash
python booker.py -u my_username -fi 123,007,321 -d 07/23/27
>Wework password: my_password
```

Check the availability only every 2 hours:

```bash
python booker.py -u my_username -fi 123 -d 07/23/27 -cd 120
>Wework password: my_password
```

Only start in 3 days 8 hours and 50 minutes:

```bash
python booker.py -u my_username -fi 123 -d 07/23/27 -so 3d8h50m
>Wework password: my_password
```

Write logs to a file instead of stdout (file can be created, but the directory must exist):

```bash
python booker.py -u my_username -fi 123 -d 07/23/27 -o /path/to/wework.logs
>Wework password: my_password
```

Wait 3 to 5 seconds between individual web requests:

```bash
python booker.py -u my_username -fi 123 -d 07/23/27 -rd 3,5
>Wework password: my_password
```


## How it works

#### Authentication:

Wework's GUI login uses Auth0's OAuth scheme with PKCE, which itself is based on RFC 7636.

https://auth0.com/docs/get-started/authentication-and-authorization-flow/authorization-code-flow-with-pkce

https://datatracker.ietf.org/doc/html/rfc7636

wework_authentication.py reproduces the request flow of this authentication, and returns an access_token used by Wework's various endpoints.

#### Wework endpoints:

wework_endpoints.py is configured to call a couple of endpoints that the web frontend would normally use to check for availability and book a floor.

- GET /Workspace/check-available-reservation-dates-single - Used to check if a floor is currently available to book, and if it is not for which reason
- GET /BuildingFloor/get-floor-capacity - If a floor is available, returns the maximum and remaining capacity
- GET common-booking/get-app-upcoming-bookings - Returns a list of the authenticated user's reservations
- POST /Workspace/reserve-workspace - Books a desk of a floor on a given date

