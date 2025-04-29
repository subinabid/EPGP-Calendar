# EPGP-Calendar

The app allows users to subscribe to the program calendar. The schedule is maintained on a googe sheet which is updated periodically.

IIMK's EPGP Program is run in 6 batches - A to F. Each batch follows different professors and schedules. The schedules for each batches are maintained on a google sheet on different tabs. The homapage renders a template which lists all the available calendars. Users can subsccribe the calengar by clicking the link directly on ios / Outlook and using the https link on Android / Google calendar

Data is currently maintained for 17th batch only.

## Google Sheet

The sheet is expected to have differnet tabs for each section and each tab shall have the following columns

- Sec -> Section detail - A to F
- Code -> Format: EPGP-203
- Course Name -> Format: Economic Environment (EE)
- Session -> Serial Number - 1 , 2, 3, etc. Quiz sessions will be 11, 12, 13 etc. Assignments will have sl numbers starting with 71
- Date -> Format: 08-Mar-25
- Time -> Format: 9:00 AM to 11:45 AM (in IST)

## App details

The app is written in Flask.

Data from the sheet is imported in `CSV` format and parsed as a `dict`. Valid rows (Rows with code and session detail) are extracted. This excludes buffers and holidays. Each row is converted to a calendar event. The data is converted to ICS format and returned to the calller.

## Return format

The end point returns ics format. Apple devices and Outlook can use the `webcal` format and Androind devices can use the `https` format.

The following endpints are available for different batches:

- epgp17a
- epgp17b
- epgp17c
- epgp17c
- epgp17e
- epgp17f


### Subscribing to the calendar

Apple / outlook can directly sunscribe to the calendars at click of a button. Google calendar has to use the URL to subscribe to. 
