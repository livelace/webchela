from collections import namedtuple

import coloredlogs
import logging
import os
import psutil
import sys
import toml

from webchela.core.utils import human_size

from webchela.core.validate import is_log_level, is_browser_type, is_list, is_browser_geometry, is_int, is_bytes, \
    is_string, is_file, is_dir, is_bool

from webchela.core.vars import DEFAULT_LOG_FORMAT, DEFAULT_LOG_LEVEL, DEFAULT_PARAMS, CONFIG_SAMPLE, DEFAULT_SHM_SIZE, \
    DEFAULT_BROWSER_TYPE, DEFAULT_BROWSER_ARGUMENT, DEFAULT_BROWSER_EXTENSION, DEFAULT_BROWSER_GEOMETRY, \
    DEFAULT_BROWSER_INSTANCE, DEFAULT_BROWSER_PAGE_SIZE, DEFAULT_BROWSER_INSTANCE_TAB, DEFAULT_BROWSER_PAGE_TIMEOUT, \
    DEFAULT_BROWSER_SCRIPT_TIMEOUT, DEFAULT_BROWSER_PROXY, DEFAULT_BROWSER_RETRY_CODES, \
    DEFAULT_BROWSER_RETRY_CODES_TRIES, CHROME_DRIVER_PATH, CHROME_EXTENSIONS_DIR, CHROME_PATH, CHROME_PROFILE, CHROME_PROFILES_DIR, \
    DEFAULT_CHUNK_SIZE, DEFAULT_CPU_LOAD, FIREFOX_DRIVER_PATH, FIREFOX_EXTENSIONS_DIR, FIREFOX_PATH, \
    FIREFOX_PROFILE, FIREFOX_PROFILES_DIR, DEFAULT_KEEP_TEMP, DEFAULT_MEM_FREE, DEFAULT_TASK_TIMEOUT, DEFAULT_CLIENT_BATCH_SIZE, \
    DEFAULT_CLIENT_ID, DEFAULT_CLIENT_OUTPUT_DIR, DEFAULT_CLIENT_SERVER, DEFAULT_CLIENT_SCRIPTS, \
    DEFAULT_SERVER_LISTEN, DEFAULT_SERVER_WORKERS

logger = logging.getLogger("webchela.config")
coloredlogs.install(fmt=DEFAULT_LOG_FORMAT, level=DEFAULT_LOG_LEVEL)


class Params:
    def __init__(self, data):
        for key, value in data.items():
            if isinstance(value, dict):
                f = Params(value)
                self.__dict__.update({key: f})
            else:
                self.__dict__.update({key: value})


class Config:
    def __init__(self):
        self.config_file = self._get_config_path()
        self._params = DEFAULT_PARAMS

        if not os.path.isfile(self.config_file):
            self._create_sample()
            self._read_config()
            self._validate_params()
        else:
            self._read_config()
            self._validate_params()

        self.params = Params(self._params)

        # Check shared memory size.
        self._check_shared_memory()

        # Set environment variables.
        self._set_env_vars()

        # Show config info.
        logger.debug("config.file: {}".format(self.config_file))

    def _create_sample(self):
        try:
            with open(self.config_file, "w") as f:
                f.write(CONFIG_SAMPLE)
            logger.info("Config sample was written successfully: {}".format(self.config_file))

        except Exception as e:
            logger.error("Cannot create config sample: {}, {}".format(self.config_file, e))
            sys.exit(1)

    def _get_config_path(self):
        try:
            config_file = os.environ["WEBCHELA_CONFIG_FILE"]
        except KeyError:
            config_file = None

        if not config_file:
            try:
                config_file = os.path.join(os.environ['HOME'], '.webchela.toml')
            except KeyError:
                logger.error("Cannot determine user home directory. Be sure HOME environment variable is set!")
                sys.exit(1)

        return config_file

    def _read_config(self):
        try:
            toml_dict = toml.load(self.config_file)

            for section in ["default", "client", "server"]:
                if section in toml_dict:
                    self._params[section] = {**self._params[section], **toml_dict[section]}

        except toml.decoder.TomlDecodeError as e:
            logger.error("Cannot parse config file: {}, {}".format(self.config_file, e))
            sys.exit(1)

        except Exception as e:
            logger.error("Cannot read config file: {}, {}".format(self.config_file, e))
            sys.exit(1)

    def _check_shared_memory(self):
        if os.path.ismount("/dev/shm"):
            size = psutil.disk_usage("/dev/shm").total
            if size >= DEFAULT_SHM_SIZE:
                logger.debug("shared.memory: {}".format(human_size(size)))
            else:
                logger.error("Shared memory size must be >= {}: {}".format(
                    human_size(DEFAULT_SHM_SIZE), human_size(size)))
                sys.exit(1)
        else:
            logger.error("Cannot find shared memory mount point: /dev/shm")
            sys.exit(1)

    def _set_env_vars(self):
        os.environ["MOZ_DISABLE_CONTENT_SANDBOX"] = "True"
        os.environ["MOZ_DISABLE_GMP_SANDBOX"] = "True"
        os.environ["MOZ_DISABLE_NPAPI_SANDBOX"] = "True"
        os.environ["MOZ_DISABLE_GPU_SANDBOX"] = "True"
        os.environ["MOZ_DISABLE_RDD_SANDBOX"] = "True"
        os.environ["MOZ_DISABLE_SOCKET_PROCESS_SANDBOX"] = "True"

    def _validate_params(self):
        # Set log level first.
        self._params["default"]["log_level"] = is_log_level(
            self._params["default"]["log_level"], DEFAULT_LOG_LEVEL)
        coloredlogs.set_level(self._params["default"]["log_level"])

        # Default.
        self._params["default"]["browser_type"] = is_browser_type(
            "default.browser_type", self._params["default"]["browser_type"], DEFAULT_BROWSER_TYPE)

        self._params["default"]["browser_argument"] = is_list(
            "default.browser_argument", self._params["default"]["browser_argument"], DEFAULT_BROWSER_ARGUMENT)

        self._params["default"]["browser_extension"] = is_list(
            "default.browser_extension", self._params["default"]["browser_extension"], DEFAULT_BROWSER_EXTENSION)

        self._params["default"]["browser_geometry"], \
        self._params["default"]["browser_geometry_x"], \
        self._params["default"]["browser_geometry_y"] = is_browser_geometry(
            "default.browser_geometry", self._params["default"]["browser_geometry"], DEFAULT_BROWSER_GEOMETRY)

        self._params["default"]["browser_instance"] = is_int(
            "default.browser_instance", self._params["default"]["browser_instance"], DEFAULT_BROWSER_INSTANCE)

        self._params["default"]["browser_instance_tab"] = is_int(
            "default.browser_instance_tab", self._params["default"]["browser_instance_tab"],
            DEFAULT_BROWSER_INSTANCE_TAB)

        self._params["default"]["browser_page_size"] = is_bytes(
            "default.browser_page_size", self._params["default"]["browser_page_size"], DEFAULT_BROWSER_PAGE_SIZE)

        self._params["default"]["browser_page_timeout"] = is_int(
            "default.browser_page_timeout", self._params["default"]["browser_page_timeout"],
            DEFAULT_BROWSER_PAGE_TIMEOUT)

        self._params["default"]["browser_script_timeout"] = is_int(
            "default.browser_script_timeout", self._params["default"]["browser_script_timeout"],
            DEFAULT_BROWSER_SCRIPT_TIMEOUT)

        self._params["default"]["browser_proxy"] = is_string(
            "default.browser_proxy", self._params["default"]["browser_proxy"], DEFAULT_BROWSER_PROXY)

        self._params["default"]["browser_retry_codes"] = is_list(
            "default.browser_retry_codes", self._params["default"]["browser_retry_codes"], DEFAULT_BROWSER_RETRY_CODES)

        self._params["default"]["browser_retry_codes_tries"] = is_int(
            "default.browser_retry_codes_tries", self._params["default"]["browser_retry_codes_tries"],
            DEFAULT_BROWSER_RETRY_CODES_TRIES)

        self._params["default"]["chrome_driver_path"] = is_file(
            "default.chrome_driver_path", self._params["default"]["chrome_driver_path"], CHROME_DRIVER_PATH)

        self._params["default"]["chrome_extensions_dir"] = is_dir(
            "default.chrome_extensions_dir", self._params["default"]["chrome_extensions_dir"], CHROME_EXTENSIONS_DIR)

        self._params["default"]["chrome_path"] = is_file(
            "default.chrome_path", self._params["default"]["chrome_path"], CHROME_PATH)
        
        self._params["default"]["chrome_profile"] = is_dir(
            "default.chrome_profile", self._params["default"]["chrome_profile"], CHROME_PROFILE)

        self._params["default"]["chrome_profiles_dir"] = is_dir(
            "default.chrome_profiles_dir", self._params["default"]["chrome_profiles_dir"], CHROME_PROFILES_DIR)

        self._params["default"]["chunk_size"] = is_bytes(
            "default.chunk_size", self._params["default"]["chunk_size"], DEFAULT_CHUNK_SIZE)

        self._params["default"]["cpu_load"] = is_int(
            "default.cpu_load", self._params["default"]["cpu_load"], DEFAULT_CPU_LOAD)

        self._params["default"]["firefox_driver_path"] = is_file(
            "default.firefox_driver_path", self._params["default"]["firefox_driver_path"], FIREFOX_DRIVER_PATH)

        self._params["default"]["firefox_extensions_dir"] = is_dir(
            "default.firefox_extensions_dir", self._params["default"]["firefox_extensions_dir"], FIREFOX_EXTENSIONS_DIR)

        self._params["default"]["firefox_path"] = is_file(
            "default.firefox_path", self._params["default"]["firefox_path"], FIREFOX_PATH)

        self._params["default"]["firefox_profile"] = is_dir(
            "default.firefox_profile", self._params["default"]["firefox_profile"], FIREFOX_PROFILE)

        self._params["default"]["firefox_profiles_dir"] = is_dir(
            "default.firefox_profiles_dir", self._params["default"]["firefox_profiles_dir"], FIREFOX_PROFILES_DIR)

        self._params["default"]["keep_temp"] = is_bool(
            "default.keep_temp", self._params["default"]["keep_temp"], DEFAULT_KEEP_TEMP)

        self._params["default"]["mem_free"] = is_bytes(
            "default.mem_free", self._params["default"]["mem_free"], DEFAULT_MEM_FREE)

        self._params["default"]["task_timeout"] = is_int(
            "default.task_timeout", self._params["default"]["task_timeout"], DEFAULT_TASK_TIMEOUT)

        # Client.
        self._params["client"]["batch_size"] = is_int(
            "client.batch_size", self._params["client"]["batch_size"], DEFAULT_CLIENT_BATCH_SIZE)

        self._params["client"]["client_id"] = is_string(
            "client.client_id", self._params["client"]["client_id"], DEFAULT_CLIENT_ID)

        self._params["client"]["output_dir"] = is_dir(
            "client.output_dir", self._params["client"]["output_dir"], DEFAULT_CLIENT_OUTPUT_DIR)

        self._params["client"]["server"] = is_string(
            "client.server", self._params["client"]["server"], DEFAULT_CLIENT_SERVER)

        self._params["client"]["scripts"] = is_list(
            "client.scripts", self._params["client"]["scripts"], DEFAULT_CLIENT_SCRIPTS)

        # Server.
        self._params["server"]["listen"] = is_string(
            "server.listen", self._params["server"]["listen"], DEFAULT_SERVER_LISTEN)

        self._params["server"]["workers"] = is_string(
            "server.workers", self._params["server"]["workers"], DEFAULT_SERVER_WORKERS)
