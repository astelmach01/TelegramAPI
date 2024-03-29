
## Telegram API (currently not maintained and not up)

This API manages all of the GET and POST requests you would need with Telegram related services.

#### Install

macOS
```shell
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

Windows
```shell
py -m venv env
.\env\Scripts\activate
pip install -r requirements.txt
```

1. Obtain your API ID and API hash from https://my.telegram.org/ -> API Development Tools.

2. Go to the [Pipedrive Developer Hub](https://app.pipedrive.com/auth/login?return_url=https%3A%2F%2Fapp.pipedrive.com%2Fdeveloper-hub), create an app, name it whatever, and paste the following callback URL.

    https://telegram-crm-plugin.herokuapp.com/auth/pipedrive/callback

3. Hit Save, go to the Oauth and access scopes tab, enable messaging integration, and upload the ```manifest.json``` file. 




## How to use

1) Click this: 
https://telegram-crm-plugin.herokuapp.com/

2) Enter your phone number associated with your telegram account, it should include the country code, so "+1" for the US.

3) Enter the rest of the associated information from telegram and pipedrive.

4) When you submit, you should get an auth code from Telegram to input into the field. (This will happen once twice since I still need to ditch the second client)

5) You will be redirected to an OAuth page that will connect the plugin to Pipedrive, accept it.

6) Enter a random channel id (it doesn't matter), leave ```provider type``` as other, and enter a channel name you'd like.

7) All done, send a message from Telegram to anybody (could be yourself), and refresh the pipedrive page.
