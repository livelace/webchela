import coloredlogs
import logging
import shutil
import uuid

from pyvirtualdisplay import Display
from seleniumwire import webdriver
from selenium.common.exceptions import *
from selenium.webdriver import FirefoxOptions
from tempfile import mkdtemp
from time import sleep

import webchela.core.protobuf.webchela_pb2 as webchela_pb2

from webchela.core.utils import *
from webchela.core.validate import *
from webchela.core.vars import *

logger = logging.getLogger("webchela.server.browser")


def chrome_grabber(config, request, task_hash, order, urls):
    b = ChromeBrowser(config, request, task_hash, order)
    return b.process(urls)


def firefox_grabber(config, request, task_hash, order, urls):
    b = FirefoxBrowser(config, request, task_hash, order)
    return b.process(urls)


def update_urls(requests):
    data = {}

    for request in requests:
        if request.response:
            data[request.url] = (request.response.status_code, request.response.headers['Content-Type'])

    return data


class Browser:
    def __init__(self, config, request, task_hash, order):
        self.config = config
        self.request = request
        self.task_hash = task_hash
        self.order = order

        self.browser = None
        self.display = None
        self.temp_dir = None

        _, self.x, self.y = is_browser_geometry("", request.browser.geometry, config.params.default.browser_geometry)

        self.selenium_wire_options = {
            "backend": "mitmproxy",
        }

        if self.request.browser.proxy:
            self.selenium_wire_options["proxy"] = {
                "http": "{}".format(self.request.browser.proxy),
                "https": "{}".format(self.request.browser.proxy),
                "no_proxy": "localhost,127.0.0.1"
            }

    def fetch(self, urls) -> dict:
        chunks = []

        # --------------------------------------------------------------------------------------------------
        # Process tabs.

        # There are could be errors during opening/awaiting/processing tabs, that is why
        # we don't use "self.browser.current_url" inside exception handling,
        # but use local variable "url" instead.
        # Session can be broken in the middle because of Xvfb/Xvnc crashing.
        #
        # Example:
        # return self.execute(Command.GET_CURRENT_URL)['value']
        # selenium.common.exceptions.InvalidSessionIdException:
        # Message: Tried to run command without establishing a connection

        self.browser.scopes = urls

        urls_origin = [0] + urls  # list of original urls + first blank tab.
        urls_final = urls_origin  # list of final urls (after all redirects) + first blank tab.
        urls_final_data = {}      # list of final urls and their data (status code, content type) + first blank tab.

        tabs_readiness = [False]  # list of tabs statuses + first blank tab.
        tabs_retries = [0]        # list of tabs retries + first blank tab.
        tabs_states = [""]        # list of tabs states (verbose) + first blank tab.
        tabs_timestamp = [0]      # list of timestamps when tabs were opened + first blank tab.

        # ------------------------------------------------------
        # Open urls.

        for index in range(1, len(urls_origin)):
            url = urls_origin[index]

            try:
                self.browser.execute_script('window.open("{0}","_blank");'.format(url))
                tabs_readiness.append(False)
                tabs_retries.append(0)
                tabs_states.append("opened")
                tabs_timestamp.append(get_timestamp())

            except WebDriverException as e:
                logger.error("[{}][{}] Browser error during open URL: {}, {}".format(
                    self.request.client_id, self.task_hash, url, e))
                return {self.order: chunks}

            except Exception as e:
                logger.error("[{}][{}] Unexpected error during open URL: {}, {}".format(
                    self.request.client_id, self.task_hash, url, e))
                return {self.order: chunks}

        # ------------------------------------------------------
        # Wait for all tabs.
        while True:
            ready = True

            # Check if origin urls are completely loaded.
            for index in range(1, len(self.browser.window_handles)):
                url = urls_origin[index]

                if not tabs_readiness[index]:
                    try:
                        self.browser.switch_to.window(self.browser.window_handles[index])
                        state = self.browser.execute_script('return document.readyState;')

                        # save possible redirected url.
                        if self.browser.current_url != 'about:blank':
                            urls_final[index] = self.browser.current_url

                        tabs_states[index] = state

                        if state != "complete":
                            sleep(self.config.params.default.tab_hop_delay)
                            ready = False

                    except TimeoutException:
                        logger.warning("[{}][{}] Timeout during waiting URL: {}".format(
                            self.request.client_id, self.task_hash, url))
                        ready = False

                    except WebDriverException as e:
                        logger.error("[{}][{}] Browser error during waiting URL: {}, {}".format(
                            self.request.client_id, self.task_hash, url, e))
                        return {self.order: chunks}

                    except Exception as e:
                        logger.error("[{}][{}] Unexpected error during waiting URL: {}, {}".format(
                            self.request.client_id, self.task_hash, url, e))
                        return {self.order: chunks}

                    # Stop page loading if timeout is reached.
                    time_diff = get_timestamp() - tabs_timestamp[index]

                    if not tabs_readiness[index] and time_diff > self.request.browser.page_timeout:
                        try:
                            self.browser.execute_script("window.stop();")
                            tabs_readiness[index] = True
                        except:
                            tabs_readiness[index] = True

                        logger.warning("[{}][{}] Timeout during page content loading for URL: {}: {}s".format(
                            self.request.client_id, self.task_hash, url, time_diff))

            # Check if final urls should be reloaded.
            urls_final_data_old = len(urls_final_data)
            urls_final_data = update_urls(self.browser.requests)  # too costly to do for each tab.

            logger.debug("[{}][{}] Total captured URLs: {} -> {}".format(
                self.request.client_id, self.task_hash, urls_final_data_old, len(urls_final_data)))

            for index in range(1, len(self.browser.window_handles)):
                url = urls_final[index]

                try:
                    status_code, _ = urls_final_data[url]
                except KeyError:
                    status_code = 0

                    logger.warning("[{}][{}] Cannot find captured URL: {}".format(
                        self.request.client_id,
                        self.task_hash,
                        url
                    ))

                if status_code in self.request.browser.retry_codes and \
                        tabs_retries[index] < self.request.browser.retry_codes_tries:
                    self.browser.switch_to.window(self.browser.window_handles[index])
                    self.browser.execute_script('location.reload();')

                    tabs_readiness[index] = False
                    tabs_retries[index] += 1
                    tabs_states[index] = "reloaded"
                    tabs_timestamp[index] = get_timestamp()

                    logger.warning("[{}][{}] Trying to reload page for URL: code: {}, {}, tries: {} of {}".format(
                        self.request.client_id,
                        self.task_hash,
                        status_code,
                        url,
                        tabs_retries[index],
                        self.request.browser.retry_codes_tries
                    ))

                    ready = False

            # Show URL states after all.
            for index in range(1, len(self.browser.window_handles)):
                url = urls_final[index]

                logger.debug("[{}][{}] Tab {}: url: {}, ready: {}, state: {}".format(
                    self.request.client_id,
                    self.task_hash,
                    index,
                    url,
                    tabs_readiness[index],
                    tabs_states[index]
                ))

            # Quit.
            if ready:
                break

        # ------------------------------------------------------
        # Process tabs.

        for index in range(1, len(self.browser.window_handles)):
            url = urls_origin[index]
            handle = self.browser.window_handles[index]
            result_uuid = str(uuid.uuid4())

            try:
                self.browser.switch_to.window(handle)

                try:
                    status_code = urls_final_data[self.browser.current_url][0]
                    content_type = urls_final_data[self.browser.current_url][1]
                except KeyError:
                    status_code = 400
                    content_type = "unknown"

                # Result will contain all data.
                result = webchela_pb2.Result(
                    UUID=result_uuid,
                    page_url=self.browser.current_url,
                    page_title=self.browser.title,
                    url=url,
                    status_code=status_code,
                    content_type=content_type
                )

                # Check page size.
                page_size = len(self.browser.page_source.encode())
                if page_size > self.request.browser.page_size:
                    msg = "[{}][{}] Page size exceeded: {}, {}".format(
                        self.request.client_id, self.task_hash, url, human_size(page_size))

                    logger.warning(msg)
                    result.page_body = msg
                else:
                    result.page_body = self.browser.page_source

                # Execute javascript code.
                for script in self.request.scripts:
                    try:
                        output = self.browser.execute_script(script)
                        result.script_output.append(str(output))

                    except JavascriptException as e:
                        msg = "[{}][{}] Javascript execution error: {}, {}".format(
                            self.request.client_id, self.task_hash, url, e.msg)

                        logger.warning(msg)
                        result.script_output.append(msg)

                    except TimeoutException:
                        msg = "[{}][{}] Javascript execution timeout: {}, {}".format(
                            self.request.client_id, self.task_hash, url,
                            self.request.browser.script_timeout)

                        logger.warning(msg)
                        result.script_output.append(msg)

                # Show what we got.
                logger.debug("uuid: {}, code: {}, url: {}, title: {}".format(
                    result_uuid, status_code, url, self.browser.title))

                # Serialize and split result into chunks.
                result_binary = result.SerializeToString()

                if result.ByteSize() > self.request.chunk_size:
                    binary_parts = [result_binary[i:i + self.request.chunk_size]
                                    for i in range(0, len(result_binary), self.request.chunk_size)]

                    for part in range(len(binary_parts)):
                        chunk = webchela_pb2.Chunk(
                            chunk=binary_parts[part]
                        )

                        if part == len(binary_parts) - 1:
                            chunk.end = True

                        chunks.append(chunk)

                else:
                    chunk = webchela_pb2.Chunk(
                        chunk=result_binary,
                        end=True
                    )

                    chunks.append(chunk)

            except WebDriverException as e:
                logger.error("[{}][{}] Browser error during processing URL: {}, {}".format(
                    self.request.client_id, self.task_hash, url, e))
                return {self.order: chunks}

            except Exception as e:
                logger.error("[{}][{}] Unexpected error during processing URL: {}, {}".format(
                    self.request.client_id, self.task_hash, url, e))
                return {self.order: chunks}

        return {self.order: chunks}

    def __del__(self):
        if self.browser:
            try:
                self.browser.quit()
            except Exception as e:
                logger.error("[{}][{}] Cannot close browser properly: {}".format(
                    self.request.client_id, self.task_hash, e))

        if self.display:
            try:
                self.display.stop()
            except Exception as e:
                logger.error("[{}][{}] Cannot stop virtual display properly: {}".format(
                    self.request.client_id, self.task_hash, e))

        if self.temp_dir and not self.config.params.default.keep_temp:
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                logger.error("[{}][{}] Cannot clean temporary directory properly: {}".format(
                    self.request.client_id, self.task_hash, e))


class ChromeBrowser(Browser):
    def __init__(self, config, request, task_hash, order):
        super().__init__(config, request, task_hash, order)

    def create_browser(self) -> bool:
        try:
            self.display = Display(backend="xvnc", size=(self.x, self.y), rfbport=0)
            self.display.start()
        except Exception as e:
            logger.warning("[{}][{}] Cannot create virtual display: {}".format(
                self.request.client_id, self.task_hash, e))
            return False

        try:
            self.temp_dir = mkdtemp(dir=self.config.params.default.chrome_profiles_dir,
                                    prefix="task_{}_".format(self.task_hash))
        except Exception as e:
            logger.warning("[{}][{}] Cannot create temporary directory: {}".format(
                self.request.client_id, self.task_hash, e))
            return False

        options = webdriver.ChromeOptions()
        options.binary_location = self.config.params.default.chrome_path

        # add user-defined arguments.
        for argument in self.request.browser.argument:
            try:
                options.add_argument(argument)
            except InvalidArgumentException:
                logger.warning("[{}][{}] Invalid argument: {}".format(
                    self.request.client_id, self.task_hash, argument))
                continue

        # add application related arguments.
        options.add_argument("no-sandbox")
        options.add_argument("user-data-dir={}".format(self.temp_dir))

        # "hide" selenium.
        options.add_experimental_option("excludeSwitches", ["enable-automation", "test-type"])
        options.add_experimental_option("useAutomationExtension", False)

        # add extensions.
        for extension in self.request.browser.extension:
            try:
                options.add_extension(os.path.join(self.config.params.default.chrome_extensions_dir, extension))
            except IOError as e:
                logger.warning("[{}][{}] Invalid extension: {}, {}".format(
                    self.request.client_id, self.task_hash, extension, e))
                continue

        # create browser.
        try:
            log = os.path.join(self.temp_dir, "chromedriver.log")

            self.browser = webdriver.Chrome(executable_path=self.config.params.default.chrome_driver_path,
                                            options=options,
                                            seleniumwire_options=self.selenium_wire_options,
                                            service_args=["--log-level=DEBUG"],
                                            service_log_path=log)
        except WebDriverException as e:
            logger.error("[{}][{}] Cannot create browser: {}".format(
                self.request.client_id, self.task_hash, e))
            return False

        # set geometry.
        self.browser.set_window_size(self.x, self.y)

        # set timeouts.
        self.browser.set_page_load_timeout(self.request.browser.page_timeout)
        self.browser.set_script_timeout(self.request.browser.script_timeout)

        return True

    def process(self, urls) -> dict:
        if self.create_browser():
            return self.fetch(urls)
        else:
            return {}

    def __del__(self):
        super(ChromeBrowser, self).__del__()


class FirefoxBrowser(Browser):
    def __init__(self, config, request, task_hash, order):
        super(FirefoxBrowser, self).__init__(config, request, task_hash, order)

    def create_browser(self) -> bool:
        try:
            self.display = Display(backend="xvnc", size=(self.x, self.y), rfbport=0)
            self.display.start()
        except Exception as e:
            logger.warning("[{}][{}] Cannot create virtual display: {}".format(
                self.request.client_id, self.task_hash, e))
            return False

        try:
            self.temp_dir = mkdtemp(dir=self.config.params.default.firefox_profiles_dir,
                                    prefix="task_{}_".format(self.task_hash))
        except Exception as e:
            logger.warning("[{}][{}] Cannot create temporary directory: {}".format(
                self.request.client_id, self.task_hash, e))
            return False

        options = FirefoxOptions()
        options.binary_location = self.config.params.default.firefox_path

        # add application related arguments.
        options.add_argument("--new-instance")
        options.set_preference("browser.link.open_newwindow", 3)  # open urls in tabs, not in windows.
        options.set_preference("dom.webnotifications.enabled", False)  # disable all notifications.
        options.set_preference("media.autoplay.default", 5)  # disable all media autoplaying.

        # add user-defined arguments.
        for argument in self.request.browser.argument:
            try:
                options.add_argument(argument)
            except InvalidArgumentException:
                logger.warning("[{}][{}] Invalid argument: {}".format(
                    self.request.client_id, self.task_hash, argument))
                continue

        # create browser.
        try:
            log = os.path.join(self.temp_dir, "geckodriver.log")

            self.browser = webdriver.Firefox(executable_path=FIREFOX_GECKODRIVER_WRAPPER,
                                             firefox_binary=self.config.params.default.firefox_path,
                                             log_path=log,
                                             options=options,
                                             seleniumwire_options=self.selenium_wire_options,
                                             service_args=[
                                                 "--log", "trace",
                                                 self.config.params.default.firefox_driver_path,  # must be before last
                                                 self.temp_dir                                    # must be last
                                             ])
        except WebDriverException as e:
            logger.error("[{}][{}] Cannot create browser: {}".format(self.request.client_id, self.task_hash, e))
            return False

        # add extensions.
        for extension in self.request.browser.extension:
            try:
                self.browser.install_addon(os.path.join(self.config.params.default.firefox_extensions_dir, extension))
            except Exception as e:
                logger.warning("[{}][{}] Invalid extension: {}, {}".format(
                    self.request.client_id, self.task_hash, extension, e))
                continue

        # set geometry.
        self.browser.set_window_size(self.x, self.y)

        # set timeouts.
        self.browser.set_page_load_timeout(self.request.browser.page_timeout)
        self.browser.set_script_timeout(self.request.browser.script_timeout)

        return True

    def process(self, urls) -> dict:
        if self.create_browser():
            return self.fetch(urls)
        else:
            return {}

    def __del__(self):
        super(FirefoxBrowser, self).__del__()
