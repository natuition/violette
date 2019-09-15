To run app:
clone this repository with command in bash/console:

    git clone https://github.com/natuition/violette

or pull updates if repository is already exists:

    git pull

stable code in master branch, but if you want to check another branch:

    git checkout branch_name

then you have to install libraries and dependencies:

    pip3 install -r "requirements.txt"
    
after that checkout local configuration in config/config_local.json.
If not exists - copy file config_local (example).json and rename it to config_local.json.
Open it with any text editor and make sure that all settings is acceptable (pay attention to calibration).

and finally, to run application (each command in different terminal):

    python3 stream_server.py
    python3 web_server.py
