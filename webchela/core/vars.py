import os
from importlib.util import find_spec
from os.path import dirname, join, isdir

# ----------------------------------------------------------------------------------------------------------------------

APP_NAME = "webchela"
APP_VERSION = "v1.8.0"

BASE_DIR = dirname(find_spec("webchela").loader.path)

DEFAULT_LOG_FORMAT = "%(asctime)s %(name)s %(levelname)s %(message)s"
DEFAULT_LOG_LEVEL = "INFO"

DEFAULT_SHM_SIZE = 1 * 1024 * 1024 * 1024  # 1GB

DEFAULT_KEEP_TEMP = False

# ----------------------------------------------------------------------------------------------------------------------
# Chrome settings.
CHROME_DRIVER_PATH = "/usr/bin/chromedriver"
CHROME_EXTENSIONS_DIR = os.path.join(BASE_DIR, "extensions", "chrome")
CHROME_PATH = "/usr/bin/google-chrome-stable"
CHROME_PROFILE = ""
CHROME_PROFILES_DIR = "/tmp/webchela/chrome"
CHROME_CHROMEDRIVER_WRAPPER = os.path.join(BASE_DIR, "script", "chromedriver.sh")

# Firefox settings.
FIREFOX_DRIVER_PATH = "/usr/bin/geckodriver"
FIREFOX_EXTENSIONS_DIR = os.path.join(BASE_DIR, "extensions", "firefox")
FIREFOX_PATH = "/usr/bin/firefox"
FIREFOX_PROFILE = ""
FIREFOX_PROFILES_DIR = "/tmp/webchela/firefox"
FIREFOX_GECKODRIVER_WRAPPER = os.path.join(BASE_DIR, "script", "geckodriver.sh")

# ----------------------------------------------------------------------------------------------------------------------

# Server.
DEFAULT_SERVER_LISTEN = "0.0.0.0:50051"
DEFAULT_SERVER_WORKERS = 10  # how many tasks can receive grpc server.

# Client.
DEFAULT_BROWSER_ARGUMENT = []
DEFAULT_BROWSER_EXTENSION = []
DEFAULT_BROWSER_GEOMETRY = "1920x1080"
DEFAULT_BROWSER_INSTANCE = 1
DEFAULT_BROWSER_INSTANCE_TAB = 10
DEFAULT_BROWSER_PROXY = ""
DEFAULT_BROWSER_RETRY_CODES = []  # list of status codes which will trigger page reloading.
DEFAULT_BROWSER_RETRY_CODES_TRIES = 1  # how many tries we should perform if status code is in the list.
DEFAULT_BROWSER_TYPE = "chrome"

DEFAULT_DEBUG_PRE_CLOSE_DELAY = 0
DEFAULT_DEBUG_PRE_OPEN_DELAY = 0
DEFAULT_DEBUG_PRE_PROCESS_DELAY = 0
DEFAULT_DEBUG_PRE_WAIT_DELAY = 0

DEFAULT_CHUNK_SIZE = 3 * 1024 * 1024  # 3MB.
DEFAULT_CPU_LOAD = 30  # percents.
DEFAULT_GEOMETRY_HEIGHT = 1080
DEFAULT_GEOMETRY_WIDTH = 1920
DEFAULT_MEM_FREE = 1 * 1024 * 1024 * 1024  # 1GB.
DEFAULT_PAGE_SIZE = 10 * 1024 * 1024  # 10MB.
DEFAULT_PAGE_TIMEOUT = 60  # seconds.
DEFAULT_RETRY_CODES = []
DEFAULT_RETRY_CODES_TRIES = 1
DEFAULT_SCREENSHOT_TIMEOUT = 30  # seconds.
DEFAULT_SCRIPT_TIMEOUT = 30  # seconds.
DEFAULT_TAB_HOP_DELAY = 1  # delay between tab "hopping" (for page status checking).
DEFAULT_TAB_OPEN_RANDOMIZE = "0:0"
DEFAULT_TASK_TIMEOUT = 600  # 10 minutes.

DEFAULT_UNIQUE_SEPARATOR = "= == === ==== ====="

# ----------------------------------------------------------------------------------------------------------------------

DEFAULT_PARAMS = {
    "default": {
        "browser_argument": DEFAULT_BROWSER_ARGUMENT,
        "browser_extension": DEFAULT_BROWSER_EXTENSION,
        "browser_geometry": DEFAULT_BROWSER_GEOMETRY,
        "browser_instance": DEFAULT_BROWSER_INSTANCE,
        "browser_instance_tab": DEFAULT_BROWSER_INSTANCE_TAB,
        "browser_proxy": DEFAULT_BROWSER_PROXY,
        "browser_retry_codes": DEFAULT_BROWSER_RETRY_CODES,
        "browser_retry_codes_tries": DEFAULT_BROWSER_RETRY_CODES_TRIES,
        "browser_script_timeout": DEFAULT_SCRIPT_TIMEOUT,
        "browser_type": DEFAULT_BROWSER_TYPE,
        "chrome_driver_path": CHROME_DRIVER_PATH,
        "chrome_extensions_dir": CHROME_EXTENSIONS_DIR,
        "chrome_path": CHROME_PATH,
        "chrome_profile": CHROME_PROFILE,
        "chrome_profiles_dir": CHROME_PROFILES_DIR,
        "chunk_size": DEFAULT_CHUNK_SIZE,
        "cpu_load": DEFAULT_CPU_LOAD,
        "debug_pre_close_delay": DEFAULT_DEBUG_PRE_CLOSE_DELAY,
        "debug_pre_open_delay": DEFAULT_DEBUG_PRE_OPEN_DELAY,
        "debug_pre_process_delay": DEFAULT_DEBUG_PRE_PROCESS_DELAY,
        "debug_pre_wait_delay": DEFAULT_DEBUG_PRE_WAIT_DELAY,
        "firefox_driver_path": FIREFOX_DRIVER_PATH,
        "firefox_extensions_dir": FIREFOX_EXTENSIONS_DIR,
        "firefox_path": FIREFOX_PATH,
        "firefox_profile": FIREFOX_PROFILE,
        "firefox_profiles_dir": FIREFOX_PROFILES_DIR,
        "keep_temp": DEFAULT_KEEP_TEMP,
        "log_level": DEFAULT_LOG_LEVEL,
        "mem_free": DEFAULT_MEM_FREE,
        "page_size": DEFAULT_PAGE_SIZE,
        "page_timeout": DEFAULT_PAGE_TIMEOUT,
        "retry_codes": DEFAULT_RETRY_CODES,
        "retry_codes_tries": DEFAULT_RETRY_CODES_TRIES,
        "screenshot_timeout": DEFAULT_SCREENSHOT_TIMEOUT,
        "script_timeout": DEFAULT_SCRIPT_TIMEOUT,
        "tab_hop_delay": DEFAULT_TAB_HOP_DELAY,
        "tab_open_randomize": DEFAULT_TAB_OPEN_RANDOMIZE,
        "task_timeout": DEFAULT_TASK_TIMEOUT,
        "unique_separator": DEFAULT_UNIQUE_SEPARATOR
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
#browser_extension          = []                                    # crx files included into webchela package

#browser_type               = "firefox"
#browser_extension          = []                                    # xpi files included into webchela package

#browser_geometry           = "1920x1080"
#browser_geometry           = "dynamic"                             # window will be resized to page content
#browser_instance           = 1                                     # amount of instances will be launched in parallel
#browser_instance_tab       = 10

#browser_proxy              = "http://1.2.3.4:3128"
#browser_proxy              = "socks5://user:pass@1.2.3.4:1080"

#browser_retry_codes        = [503]
#browser_retry_codes_tries  = 1

#chrome_driver_path         = "/usr/bin/chromedriver"
#chrome_extensions_dir      = "<INSTALL_PATH>/extensions/chrome"
#chrome_path                = "/usr/bin/google-chrome-stable"
#chrome_profile             = ""                                    # only one browser instance at time if set
#chrome_profiles_dir        = "/tmp/webchela/chrome"

#firefox_driver_path        = "/usr/logcal/bin/geckodriver"
#firefox_extensions_dir     = "<INSTALL_PATH>/extensions/firefox"
#firefox_path               = "/usr/bin/firefox"
#firefox_profile            = ""                                    # only one browser instance at time if set
#firefox_profiles_dir       = "/tmp/webchela/firefox"

#chunk_size                 = "3M"
#cpu_load                   = 30                                    # browser is a heavy thing, be careful with limits
#keep_temp                  = false
#log_level                  = "DEBUG"
#mem_free                   = "1G"                                  # browser is a heavy thing, be careful with limits
#page_size                  = "10M"
#page_timeout               = 60
#screenshot_timeout         = 30
#script_timeout             = 30
#task_timeout               = 600

[server]

#listen                     = "0.0.0.0:50051"
#workers                    = 10                                    # set a lower value if you experiencing issues
"""

# ----------------------------------------------------------------------------------------------------------------------

HELP_CLIENT_URL = "Single URL address."
HELP_CLIENT_URL_FILE = "Load URL addresses from file."
HELP_CLIENT_SCRIPT = "Single line Javascript code."
HELP_CLIENT_SCRIPT_FILE = "Load Javascript code from file."

# ----------------------------------------------------------------------------------------------------------------------
