# heroku-main
Personal web page and telegram bot hosted in heroku

### Dependencies
- [Dejavu Fonts](https://dejavu-fonts.github.io/)
(You might already have them installed)
- Since it is intended to be hosted on heroku you should check the
[Pipfile](Pipfile)

#### Heroku config vars
- APPNAME > Heroku app name
- BOT_ID > Telegram ID of your bot
- DATABASE_URL > Activate heroku postgresql database
- LINK_KEY > Used to generate tokens to access links with preset role
- MY_ID > ID of your telegram account
- PRIVATE_KEYS > 4 lines containing a password for each role level
- TOKEN > Telegram API token

### Usage
Upload this project to a heroku application

The first time you use it you must run:
`python3 utils/start.py` through heroku run

The program consists of two parts:

- Telegram bot that writes to database. To learn how to use it write ".help"
- Webpage that reads from database and create images

##### Note
This was designed with self-use intention. Feel free to adapt
the code and make it more suitable for your intentions.

Icons made by [Freepik](http://www.freepik.com) from
[www.flaticon.com](https://www.flaticon.com/)
is licensed by [CC 3.0 BY](http://creativecommons.org/licenses/by/3.0/)
