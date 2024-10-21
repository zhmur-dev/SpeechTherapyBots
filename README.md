# SpeechTherapyBots
Initially developed for mobile app "Privet, Logoped!" within a hackathon, **SpeechTherapyBots** are heavily customizable bots for Telegram and VK interconnected with Django admin panel via universal backend.


## Initial project goals
Create chatbots for Telegram and VK to improve sales, providing users with better support and information, and arrange the workflow of product owner in a more efficient manner.


## Main features
* Bot menu, that is customizable via admin panel for different user roles.
* Info buttons: automatic issue of texts, links and files.
* Possibility to create nested menus.
* Direct contact to administrators.
* Admin features within the bots: answering user questions, blocking users.
* Admin panel with the possibility to answer several questions, and for general administration purposes.


## Achieved goals
* Admin panel with customizable menus for different roles.
* Menu navigation.
* Info buttons: automatic issue of texts and files.
* User questions to administrators.
* Fully international release.
* Admin answering interface (not more than 1 admin at a time).
* Issue of answers to users (currently only in Telegram).
* Subscriptions (Telegram — partially).
* Change user role (currently only in VK).
* Minimal errors logging system.


## Project structure
* `/infra` — Directory with the files for server deploy.
* `/backend` — Main directory with Django project structure.

Settings:
* `/backend/settings.py` — Main settings.
* `/core/localization.py` — Localization literals.


## Stack
* Python 3.11
* Django 4.2
* python-telegram-bot 13.7
* vk_api 11.9
* PostgreSQL 16.3
* gunicorn 23.0


## Installation and startup

### Telegram bot
#### 1. Bot creation:
- Open [Telegram](https://telegram.org/apps), login into your account, or create a new one.
- Search for [@BotFather](https://telegram.me/BotFather) and choose the bot.

>The official Telegram bot has a blue confirmation icon with a tickmark.

- Push `Start` or type `/start` to activate `BotFather`.

You will get a list of commands to manage your bot.

- Choose or type `/newbot`.
- Give your bot a `name` — users will see this name when communicating.
- Next, pick a `nickname` for your bot so that users are able to find it in Telegram. Nickname must be unique, different from already existing ones and end with `bot`, e.g. `TelegramBot` or `tg_bot`.

>`Name` can be anything you like. It can also be the same as the already existing ones.

- After you pick a suitable name, bot will be created. You will get a link to your bot: `t.me/<bot_nickname>`, and recommendations on how to set up bot avatar, description, list of commands, and - what you need right now - bot `token`.

#### 2. How to obtain a `token` for the already existing bot:
- Go to `@BotFather` and type `/token`. You will see buttons with `nicknames` of already created bots.
- Choose a bot that you need to have token for.
- Copy the `token` you have received from `@BotFather`.

### VK bot
#### 1. VK group set up:
- Go to the main page of your group using administrator account and choose `Management` from the side panel.
- Go to `Settings` -> `API`.
- Pick `Create a key` and provide access for *group management*, *group messages* and *group documents*. You will need this key later.
- When in `Settings` -> `API`, choose `Long Poll API` and turn it on.
- In the same section choose `Event types` and turn on all options under the headers *Messages* and *Users*.
- Exit `Settings` -> `API` in side menu, open the `Messages` section and turn on *Group messages*.
- Go to `Messages` -> `Settings for bot`.
- Turn on *Possibilities of bots* and *Add «Start» button*.

#### 2. Getting data for `.env` file:
- Your VK bot `token` has been created at the previous stage, and is currently stored at `Settings` -> `API` -> `Access keys`. Push the *Show* button to see it.
- VK group `ID` is a sequence of numbers following the group URL: https://vk.com/club`XXXXXX`


### Launching SpeechTherapyBots locally
- Add your Telegram bot `token`, VK bot `token` and VK group `id` to `.env` file located at main project directory. Should such file be missing, create it based on `.env.example`.
- Set variables `SQLITE=True` and `DEBUG=True`.

```
SQLITE=True
DEBUG=True
VK_TOKEN=Your token from VK access keys
VK_GROUP_ID=VK Group ID
TELEGRAM_TOKEN=Your token from BotFather (Telegram)
```

- Go to head directory of `SpeechTherapyBots` and activate virtual environment:

For `MacOS` or `Linux`
```
python3 -m venv venv
source venv/bin/activate
```
For `Windows`
```
python -m venv venv
source venv/Scripts/activate
```
- Upgrade pip package manager:
```
pip install --upgrade pip 
```
- Install requirements:
```
pip install -r requirements.txt
```

- Make sure you have applied all necessary migrations by running the following command from head directory of the project:

For `MacOS` or `Linux`
```
python3 backend/manage.py migrate
```
For `Windows`
```
python backend/manage.py migrate
```
- Use the following command to create an administrator account:

For `MacOS` or `Linux`
```
python3 backend/manage.py createsuperuser
```
For `Windows`
```
python backend/manage.py createsuperuser
```

- Use the following command to launch Telegram bot from the same directory:

For `MacOS` or `Linux`
```
python3 backend/manage.py telegram_bot
```
For `Windows`
```
python backend/manage.py telegram_bot
```
- Use the following command to launch VK bot from the same directory:

For `MacOS` or `Linux`
```
python3 backend/manage.py vk_bot
```
For `Windows`
```
python backend/manage.py vk_bot
```


### Server deploy
>NB: This manual is provided for a debian-based Linux distribution!

#### 1. Make sure that all necessary packages are installed at your server.

```
sudo apt update
sudo apt install git python3 python3-pip python3-venv nano postgresql systemd
```

#### 2. Set up PostgreSQL database.

- Enable `postgresql` system service for automatic launch upon startup of the server.
```
sudo systemctl enable --now postgresql
```

- Create a user that will be the owner of your database.
```
sudo -su postgres createuser <username>
```

- Create your database and set the previously created user as its owner.
```
sudo -su postgres createdb <database_name> -O <username>
```

- Create a password for your user.
```
sudo -u postgres psql -c "ALTER USER <username> PASSWORD '<user_password>';"
```

#### 3. Clone the repository and set up the project for its first start.

- Clone the repository and cd into its main directory.
```
git clone git@github.com:zhmur-dev/SpeechTherapyBots.git
cd SpeechTherapyBots/
```

- Create and fill in an `.env` file based on the example provided in `.env.example`. (`DATABASE_NAME`), (`POSTGRES_USER`) and (`POSTGRES_PASSWORD`) were set up by you previously at Step 2. Don't forget to specify your actual server location in `ALLOWED_HOSTS`.
```
nano .env
```

#### 4. Create and activate virtual environment, install requirements and apply all necessary migrations.
```
cd backend/
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r ../requirements.txt
python3 manage.py collectstatic
python3 manage.py migrate
```

#### 5. Create the first administrator account.
```
python3 manage.py createsuperuser
```

#### 6. Set up infrastructure.
Edit `backend.service`, `telegram-bot.service` and`vk-service` files from `infra` directory and put them to `/etc/systemd/system/` at your server. When editing, specify the absolute path to project directory at your server and correct name of the user at your server that will be used to launch daemons.

```
nano ../infra/backend.service
nano ../infra/telegram-bot.service
nano ../infra/vk-bot.service
sudo cp ../infra/backend.service ../infra/telegram-bot.service ../infra/vk-bot.service /etc/systemd/system
```

#### 7. Enable the created services for automatic launch at server startup.
```
sudo systemctl enable --now backend
sudo systemctl enable --now telegram-bot
sudo systemctl enable --now vk-bot
```

The project is ready for operation at your remote server!


## Authors
* Evgeny [MicroElf](https://github.com/MicroElf) Chernykh - Team Leader
* Alexander [zhmur-dev](https://github.com/zhmur-dev) Zhmurkov - Backend
* Denis [KrDenches](https://github.com/KrDenches) Krokhin - Telegram
* Vsevolod [Vsevolod25](https://github.com/Vsevolod25) Kolupatin - VK
