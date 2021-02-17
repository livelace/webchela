import os
from importlib.util import find_spec
from os.path import dirname, join, isdir

# ----------------------------------------------------------------------------------------------------------------------

APP_NAME = "webchela"
APP_VERSION = "v1.5.0"

BASE_DIR = dirname(find_spec("webchela").loader.path)

DEFAULT_LOG_FORMAT = "%(asctime)s %(name)s %(levelname)s %(message)s"
DEFAULT_LOG_LEVEL = "INFO"

DEFAULT_SHM_SIZE = 1 * 1024 * 1024 * 1024  # 1GB

DEFAULT_KEEP_TEMP = False

# ----------------------------------------------------------------------------------------------------------------------
# Chrome settings.
CHROME_DRIVER_PATH = "/usr/bin/chromedriver"
CHROME_EXTENSIONS_DIR = "/tmp"
CHROME_PATH = "/usr/bin/google-chrome-stable"
CHROME_PROFILES_DIR = "/tmp/webchela/profiles/chrome"

# Firefox settings.
FIREFOX_DRIVER_PATH = "/usr/bin/geckodriver"
FIREFOX_EXTENSIONS_DIR = "/tmp"
FIREFOX_LOG_FILE = "/tmp/geckodriver.log"
FIREFOX_PATH = "/usr/lib64/firefox/firefox"
FIREFOX_PROFILES_DIR = "/tmp/webchela/profiles/firefox"
FIREFOX_GECKODRIVER_WRAPPER = os.path.join(BASE_DIR, "core", "script", "geckodriver.sh")

webchela_extensions = find_spec("webchela-extensions")
if webchela_extensions:
    cd = join(dirname(webchela_extensions.loader.path), "chrome")
    fd = join(dirname(webchela_extensions.loader.path), "firefox")

    if isdir(cd):
        CHROME_EXTENSIONS_DIR = cd

    if isdir(fd):
        FIREFOX_EXTENSIONS_DIR = fd

TAB_HOP_DELAY = 1  # delay between tab "hopping" (for page status checking).

# ----------------------------------------------------------------------------------------------------------------------

# Server.
DEFAULT_SERVER_LISTEN = "0.0.0.0:50051"
DEFAULT_SERVER_WORKERS = 1

# Client.
DEFAULT_CLIENT_BATCH_SIZE = 100
DEFAULT_BROWSER_ARGUMENT = []
DEFAULT_BROWSER_EXTENSION = ["bypass-paywalls-1.7.6.xpi", "ublock-origin-1.30.6.xpi"]
DEFAULT_BROWSER_GEOMETRY = "1024x768"
DEFAULT_BROWSER_INSTANCE = 1
DEFAULT_BROWSER_INSTANCE_TAB = 5
DEFAULT_BROWSER_PAGE_SIZE = 10 * 1024 * 1024    # 10MB.
DEFAULT_BROWSER_PAGE_TIMEOUT = 20               # seconds.
DEFAULT_BROWSER_SCRIPT_TIMEOUT = 20             # seconds.
DEFAULT_BROWSER_TYPE = "firefox"
DEFAULT_BROWSER_PROXY = ""
DEFAULT_BROWSER_RETRY_CODES = []                # list of status codes which will trigger page reloading.
DEFAULT_BROWSER_RETRY_CODES_TRIES = 1           # how many tries we should perform if status code is in the list.

DEFAULT_CHUNK_SIZE = 3 * 1024 * 1024            # 3MB.
DEFAULT_CPU_LOAD = 50                           # percents.
DEFAULT_GEOMETRY_HEIGHT = 768
DEFAULT_GEOMETRY_WIDTH = 1024
DEFAULT_MEM_FREE = 1 * 1024 * 1024 * 1024       # 1GB.
DEFAULT_TASK_TIMEOUT = 300                      # 5 minutes.

DEFAULT_CLIENT_ID = "webchela-cli"
DEFAULT_CLIENT_OUTPUT_DIR = "/tmp/webchela"
DEFAULT_CLIENT_SCRIPTS = []
DEFAULT_CLIENT_SERVER = "127.0.0.1:50051"

# ----------------------------------------------------------------------------------------------------------------------

DEFAULT_PARAMS = {
    "default": {
        "browser_type": DEFAULT_BROWSER_TYPE,
        "browser_argument": DEFAULT_BROWSER_ARGUMENT,
        "browser_extension": DEFAULT_BROWSER_EXTENSION,
        "browser_geometry": DEFAULT_BROWSER_GEOMETRY,
        "browser_instance": DEFAULT_BROWSER_INSTANCE,
        "browser_instance_tab": DEFAULT_BROWSER_INSTANCE_TAB,
        "browser_page_size": DEFAULT_BROWSER_PAGE_SIZE,
        "browser_page_timeout": DEFAULT_BROWSER_PAGE_TIMEOUT,
        "browser_script_timeout": DEFAULT_BROWSER_SCRIPT_TIMEOUT,
        "browser_proxy": DEFAULT_BROWSER_PROXY,
        "browser_retry_codes": DEFAULT_BROWSER_RETRY_CODES,
        "browser_retry_codes_tries": DEFAULT_BROWSER_RETRY_CODES_TRIES,
        "chrome_driver_path": CHROME_DRIVER_PATH,
        "chrome_extensions_dir": CHROME_EXTENSIONS_DIR,
        "chrome_path": CHROME_PATH,
        "chrome_profiles_dir": CHROME_PROFILES_DIR,
        "chunk_size": DEFAULT_CHUNK_SIZE,
        "cpu_load": DEFAULT_CPU_LOAD,
        "firefox_driver_path": FIREFOX_DRIVER_PATH,
        "firefox_extensions_dir": FIREFOX_EXTENSIONS_DIR,
        "firefox_path": FIREFOX_PATH,
        "firefox_profiles_dir": FIREFOX_PROFILES_DIR,
        "keep_temp": DEFAULT_KEEP_TEMP,
        "log_level": DEFAULT_LOG_LEVEL,
        "mem_free": DEFAULT_MEM_FREE,
        "tab_hop_delay": TAB_HOP_DELAY,
        "task_timeout": DEFAULT_TASK_TIMEOUT
    },
    "client": {
        "batch_size": DEFAULT_CLIENT_BATCH_SIZE,
        "client_id": DEFAULT_CLIENT_ID,
        "output_dir": DEFAULT_CLIENT_OUTPUT_DIR,
        "server": DEFAULT_CLIENT_SERVER,
        "scripts": DEFAULT_CLIENT_SCRIPTS,
    },
    "server": {
        "listen": DEFAULT_SERVER_LISTEN,
        "workers": DEFAULT_SERVER_WORKERS
    }
}

# ----------------------------------------------------------------------------------------------------------------------

CONFIG_SAMPLE = """
[default]

#browser_type               = "chrome"
#browser_extension          = ["bypass-paywalls-1.7.6.crx", "ublock-origin-1.30.6.crx"]

#browser_type               = "firefox"
#browser_extension          = ["bypass-paywalls-1.7.6.xpi", "ublock-origin-1.30.6.xpi"]

#browser_geometry           = "1024x768"
#browser_instance           = 1
#browser_instance_tab       = 5
#browser_page_size          = "10M"
#browser_page_timeout       = 20
#browser_script_timeout     = 20

#browser_proxy              = "http://1.2.3.4:3128"
#browser_proxy              = "socks5://user:pass@1.2.3.4:1080"

#chrome_driver_path         = "/usr/bin/chromedriver"
#chrome_extensions_dir      = "/tmp"
#chrome_path                = "/usr/bin/google-chrome-stable"
#chrome_profiles_dir        = "/tmp"

#chunk_size                 = "3M"

#cpu_load                   = 25

#firefox_driver_path        = "/usr/bin/geckodriver"
#firefox_extensions_dir     = "/tmp"
#firefox_path               = "/usr/lib64/firefox/firefox"
#firefox_profiles_dir       = "/tmp"

#keep_temp                  = false

#log_level                  = "DEBUG"

#mem_free                   = "1G"

#browser_retry_codes        = []
#browser_retry_codes_tries  = 1

#task_timeout               = 300

[client]

#client_id                  = "webchela-cli"
#batch_size                 = 100
#output_dir                 = "/tmp/webchela"
#server                     = "127.0.0.1:50051"
#scripts                    = ["return 42;"]

[server]

#listen                     = "0.0.0.0:50051"
#workers                    = 1
"""

# ----------------------------------------------------------------------------------------------------------------------

HELP_CLIENT_URL = "Single URL address."
HELP_CLIENT_URL_FILE = "Load URL addresses from file."
HELP_CLIENT_SCRIPT = "Single line Javascript code."
HELP_CLIENT_SCRIPT_FILE = "Load Javascript code from file."

# ----------------------------------------------------------------------------------------------------------------------
