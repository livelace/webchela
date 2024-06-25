import json
import os
import re
import time
import random

import coloredlogs
import logging
import shutil
import uuid

from pyvirtualdisplay import Display
from selenium.common.exceptions import (
    InvalidArgumentException,
    JavascriptException,
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)

from selenium.webdriver import FirefoxOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from seleniumwire import webdriver
from tempfile import mkdtemp
from time import sleep

import webchela.core.protobuf.webchela_pb2 as webchela_pb2

from webchela.core.utils import get_timestamp, human_size
from webchela.core.validate import is_browser_geometry, is_tab_open_randomize

from webchela.core.vars import CHROME_CHROMEDRIVER_WRAPPER
from webchela.core.vars import FIREFOX_GECKODRIVER_WRAPPER

logger = logging.getLogger("webchela.server.browser")


def chrome_grabber(config, request, task_hash, order, urls, cookies, screenshots, scripts):
    b = ChromeGenericBrowser(config, request, task_hash, order)
    return b.process(urls, cookies, screenshots, scripts)


def firefox_grabber(config, request, task_hash, order, urls, cookies, screenshots, scripts):
    b = FirefoxGenericBrowser(config, request, task_hash, order)
    return b.process(urls, cookies, screenshots, scripts)


def update_urls(requests):
    data = {}

    for request in requests:
        if request.response:
            data[request.url] = (request.response.status_code,
                                 request.response.headers['Content-Type'])

    return data


class GenericBrowser:
    def __init__(self, config, request, task_hash, order):
        self.config = config
        self.request = request
        self.task_hash = task_hash
        self.order = order

        self.browser = None
        self.display = None
        self.keep_temp = None
        self.profile_dir = None

        _, self.x, self.y = is_browser_geometry(
            "", request.browser.geometry, config.params.default.browser_geometry)

        _, self.rand_min, self.rand_max = is_tab_open_randomize(
            "", request.tab_open_randomize, config.params.default.tab_open_randomize)

        self.selenium_wire_options = {
            "backend": "default",
        }

        if self.request.browser.proxy:
            self.selenium_wire_options["proxy"] = {
                "http": "{}".format(self.request.browser.proxy),
                "https": "{}".format(self.request.browser.proxy),
                "no_proxy": "localhost,127.0.0.1"
            }

    def fetch(self, urls, cookies, screenshots, scripts) -> dict:
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

        urls_origin = ["0"] + urls  # list of original urls + first blank tab.
        # list of final urls (after all redirects) + first blank tab.
        urls_final = urls_origin.copy()
        # list of final urls and their data (status code, content type) + first blank tab.
        urls_final_data = {}

        cookies = ["0"] + cookies  # list of screenshots + first blank tab.
        screenshots = ["0"] + screenshots  # list of screenshots + first blank tab.
        scripts = ["0"] + scripts  # list of scripts + first blank tab.

        tabs_readiness = [False]  # list of tabs statuses + first blank tab.
        tabs_retries = [0]  # list of tabs retries + first blank tab.
        # list of tabs states (verbose) + first blank tab.
        tabs_states = [""]
        # list of timestamps when tabs were opened + first blank tab.
        tabs_timestamp = [0]

        # ------------------------------------------------------
        # ------------------------------------------------------
        # Close unwanted tabs (might be opened by an extension).

        logger.debug("[{}][{}] Debug pre close delay: {}s".format(
            self.request.client_id, self.task_hash, self.request.debug.pre_close_delay))
        time.sleep(self.request.debug.pre_close_delay)

        if len(self.browser.window_handles) > 1:
            for i in reversed(range(1, len(self.browser.window_handles))):
                self.browser.switch_to.window(self.browser.window_handles[i])
                self.browser.close()

            self.browser.switch_to.window(self.browser.window_handles[0])

        # ------------------------------------------------------
        # ------------------------------------------------------
        # Open URLs.

        logger.debug("[{}][{}] Debug pre open delay: {}s".format(
            self.request.client_id, self.task_hash, self.request.debug.pre_open_delay))
        time.sleep(self.request.debug.pre_open_delay)

        for index in range(1, len(urls_origin)):
            url = urls_origin[index]

            try:
                self.browser.execute_script(
                    'window.open("{0}","_blank");'.format(url))
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

            rand_sec = random.randint(self.rand_min, self.rand_max)
            logger.debug("[{}][{}] Tab open randomize: {}s".format(
                self.request.client_id, self.task_hash, rand_sec))
            time.sleep(rand_sec)

        # ------------------------------------------------------
        # ------------------------------------------------------
        # Wait for tabs loading.

        logger.debug("[{}][{}] Debug pre wait delay: {}s".format(
            self.request.client_id, self.task_hash, self.request.debug.pre_wait_delay))
        time.sleep(self.request.debug.pre_wait_delay)

        while True:
            ready = True

            # Check if origin urls are completely loaded.
            for index in range(1, len(self.browser.window_handles)):
                url = urls_origin[index]

                if not tabs_readiness[index]:
                    try:
                        self.browser.switch_to.window(
                            self.browser.window_handles[index])

                        state = self.browser.execute_script(
                            'return document.readyState;')

                        # save possible redirected url.
                        if self.browser.current_url != 'about:blank':
                            urls_final[index] = self.browser.current_url

                        tabs_states[index] = state

                        if state == "complete":
                            tabs_readiness[index] = True
                        else:
                            sleep(self.config.params.default.tab_hop_delay)
                            ready = False

                    except TimeoutException:
                        logger.warning("[{}][{}] Timeout during waiting URL: {}".format(
                            self.request.client_id, self.task_hash, url))
                        ready = False

                    except WebDriverException as e:
                        logger.error("[{}][{}] Browser error during waiting URL: {}, {}".format(
                            self.request.client_id, self.task_hash, url, e))
                        ready = False

                    except Exception as e:
                        logger.error("[{}][{}] Unexpected error during waiting URL: {}, {}".format(
                            self.request.client_id, self.task_hash, url, e))
                        return {self.order: chunks}

                    # Stop page loading if timeout is reached.
                    time_diff = get_timestamp() - tabs_timestamp[index]

                    # Enough is enough, stop waiting.
                    if not tabs_readiness[index] and time_diff > self.request.page_timeout:
                        try:
                            self.browser.execute_script("window.stop();")
                            tabs_readiness[index] = True
                        except Exception:
                            tabs_readiness[index] = True

                        logger.warning("[{}][{}] Timeout during page content loading for URL: {}: {}s".format(
                            self.request.client_id, self.task_hash, url, time_diff))

            # Check if final urls should be reloaded.
            urls_final_data_old = len(urls_final_data)
            # too costly to do for each tab.
            urls_final_data = update_urls(self.browser.requests)

            logger.debug("[{}][{}] Total captured URLs: {} -> {}".format(
                self.request.client_id, self.task_hash, urls_final_data_old, len(urls_final_data)))

            for index in range(1, len(self.browser.window_handles)):
                url = urls_final[index]

                try:
                    status_code, _ = urls_final_data[url]

                    if status_code in self.request.retry_codes and \
                            tabs_retries[index] < self.request.retry_codes_tries:
                        self.browser.switch_to.window(
                            self.browser.window_handles[index])
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
                            self.request.retry_codes_tries
                        ))

                        ready = False

                except KeyError:
                    logger.warning("[{}][{}] Cannot find captured URL: {}".format(
                        self.request.client_id,
                        self.task_hash,
                        url
                    ))

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
        # ------------------------------------------------------
        # Processing tabs.

        logger.debug("[{}][{}] Debug pre process delay: {}s".format(
            self.request.client_id, self.task_hash, self.request.debug.pre_process_delay))
        time.sleep(self.request.debug.pre_process_delay)

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

                # ------------------------------------------------------------
                # Check page size.

                page_size = len(self.browser.page_source.encode())
                if page_size > self.request.page_size:
                    msg = "[{}][{}] Page size exceeded: {}, {}".format(
                        self.request.client_id, self.task_hash, url, human_size(page_size))

                    logger.warning(msg)
                    result.page_body = msg
                else:
                    result.page_body = self.browser.page_source

                # ------------------------------------------------------------
                # Set cookies.

                logger.debug("[{}][{}] Debug pre cookie delay: {}s".format(
                    self.request.client_id, self.task_hash, self.request.debug.pre_cookie_delay))
                time.sleep(self.request.debug.pre_cookie_delay)

                for cookie_index, cookie_value in enumerate(
                        re.split(self.config.params.default.unique_separator, cookies[index])):

                    if cookie_value:
                        try:
                            cookie_object = json.loads(cookie_value)
                            if isinstance(cookie_object, list):
                                for o in cookie_object:
                                    self.browser.add_cookie(o)
                            else:
                                self.browser.add_cookie(cookie_object)

                        except Exception as e:
                            msg = "[{}][{}] Cookie injecting error: {}, {}".format(
                                self.request.client_id, self.task_hash, url, e)

                            logger.warning(msg)

                # reload page after cookie injecting.
                if cookies[index]:
                    self.browser.execute_script('location.reload();')

                # ------------------------------------------------------------
                # Resize browser window.

                if self.request.browser.geometry == "dynamic":
                    try:
                        width = self.browser.execute_script(
                            "return Math.max( document.body.scrollWidth, document.body.offsetWidth, "
                            "document.documentElement.clientWidth, document.documentElement.scrollWidth, "
                            "document.documentElement.offsetWidth );")
                        height = self.browser.execute_script(
                            "return Math.max( document.body.scrollHeight, document.body.offsetHeight, "
                            "document.documentElement.clientHeight, document.documentElement.scrollHeight, "
                            "document.documentElement.offsetHeight );")

                        self.browser.set_window_size(width, height)

                    except Exception as e:
                        msg = "[{}][{}] Browser window maximizing error: {}, {}".format(
                            self.request.client_id, self.task_hash, url, e)
                        logger.warning(msg)

                # ------------------------------------------------------------
                # Execute javascript code.

                logger.debug("[{}][{}] Debug pre script delay: {}s".format(
                    self.request.client_id, self.task_hash, self.request.debug.pre_script_delay))
                time.sleep(self.request.debug.pre_script_delay)

                for script_index, script_value in enumerate(
                        re.split(self.config.params.default.unique_separator, scripts[index])):

                    if script_value:
                        try:
                            script_output = self.browser.execute_script(script_value)

                            result.scripts.append(str(script_output))
                            result.scripts_id.append(script_index)

                        except JavascriptException as e:
                            msg = "[{}][{}] Javascript execution error: {}, {}".format(
                                self.request.client_id, self.task_hash, url, e.msg)

                            logger.warning(msg)
                            result.scripts.append(msg)
                            result.scripts_id.append(script_index)

                        except TimeoutException:
                            msg = "[{}][{}] Javascript execution timeout: {}, {}".format(
                                self.request.client_id, self.task_hash, url,
                                self.request.script_timeout)

                            logger.warning(msg)
                            result.scripts.append(msg)
                            result.scripts_id.append(script_index)

                # ------------------------------------------------------------
                # Get screenshots.

                logger.debug("[{}][{}] Debug pre screenshot delay: {}s".format(
                    self.request.client_id, self.task_hash, self.request.debug.pre_screenshot_delay))
                time.sleep(self.request.debug.pre_screenshot_delay)

                if len(screenshots) > 1:
                    self.browser.implicitly_wait(self.request.screenshot_timeout)

                for screenshot_index, screenshot_value in enumerate(
                        re.split(self.config.params.default.unique_separator, screenshots[index])):

                    if screenshot_value:
                        prefix, value = screenshot_value.split(':')

                        screenshot_elements = None

                        try:
                            match prefix:
                                case "class":
                                    screenshot_elements = self.browser.find_elements(By.CLASS_NAME, value)
                                case "css":
                                    screenshot_elements = self.browser.find_elements(By.CSS_SELECTOR, value)
                                case "id":
                                    screenshot_elements = self.browser.find_elements(By.ID, value)
                                case "name":
                                    screenshot_elements = self.browser.find_elements(By.NAME, value)
                                case "tag":
                                    screenshot_elements = self.browser.find_elements(By.TAG_NAME, value)
                                case "xpath":
                                    screenshot_elements = self.browser.find_elements(By.XPATH, value)
                                case _:
                                    pass

                        except NoSuchElementException as e:
                            msg = "[{}][{}] Screenshot elements searching error: {}, {}".format(
                                self.request.client_id, self.task_hash, url, e.msg)

                            logger.warning(msg)

                        try:
                            for screenshot_element in screenshot_elements:
                                r = screenshot_element.rect
                                if r["width"] > 0 and r["height"] > 0:
                                    self.browser.execute_script("arguments[0].scrollIntoView(true);", screenshot_element)
                                    result.screenshots.append(screenshot_element.screenshot_as_base64)
                                    result.screenshots_id.append(screenshot_index)

                        except JavascriptException as e:
                            msg = "[{}][{}] Screenshot elements processing error: {}, {}".format(
                                self.request.client_id, self.task_hash, url, e.msg)
                            logger.warning(msg)

                # ------------------------------------------------------------
                # Show what we got.

                logger.debug("uuid: {}, code: {}, url: {}, title: {}".format(
                    result_uuid, status_code, url, self.browser.title))

                # ------------------------------------------------------------
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

        if self.profile_dir and not self.keep_temp:
            try:
                shutil.rmtree(self.profile_dir)
            except Exception as e:
                logger.error("[{}][{}] Cannot clean temporary directory properly: {}".format(
                    self.request.client_id, self.task_hash, e))


class ChromeGenericBrowser(GenericBrowser):
    def __init__(self, config, request, task_hash, order):
        super().__init__(config, request, task_hash, order)

    def create_browser(self) -> bool:
        try:
            self.display = Display(
                backend="xvnc", size=(self.x, self.y), rfbport=0)
            self.display.start()
        except Exception as e:
            logger.warning("[{}][{}] Cannot create virtual display: {}".format(
                self.request.client_id, self.task_hash, e))
            return False

        if self.config.params.default.chrome_profile:
            self.keep_temp = True

            self.profile_dir = os.path.join(
                self.config.params.default.chrome_profiles_dir, self.config.params.default.chrome_profile)

            try:
                os.makedirs(self.profile_dir, exist_ok=True)
            except Exception as e:
                logger.warning("[{}][{}] Cannot create profile directory: {}".format(
                    self.request.client_id, self.task_hash, e))
                return False

        if not self.config.params.default.chrome_profile:
            self.keep_temp = self.config.params.default.keep_temp

            try:
                self.profile_dir = mkdtemp(dir=self.config.params.default.chrome_profiles_dir,
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
        options.add_argument("in-process-gpu")  # virtualgl
        options.add_argument("use-gl=egl")      # virtualgl
        options.add_argument("no-sandbox")
        options.add_argument("user-data-dir={}".format(self.profile_dir))

        # "hide" selenium.
        options.add_argument("disable-blink-features=AutomationControlled")
        options.add_experimental_option(
            "excludeSwitches", ["enable-automation", "test-type"])
        options.add_experimental_option("useAutomationExtension", False)

        # add extensions.
        for extension in self.request.browser.extension:
            try:
                options.add_extension(os.path.join(
                    self.config.params.default.chrome_extensions_dir, extension.strip()))
            except IOError as e:
                logger.warning("[{}][{}] Invalid extension: {}, {}".format(
                    self.request.client_id, self.task_hash, extension.strip(), e))
                continue

        # create browser.
        try:
            log = os.path.join(self.profile_dir, "chromedriver.log")

            self.browser = webdriver.Chrome(
                options=options,
                seleniumwire_options=self.selenium_wire_options,
                service=ChromeService(
                    executable_path=CHROME_CHROMEDRIVER_WRAPPER,
                    service_args=[
                        self.config.params.default.chrome_driver_path,
                        "--log-level={}".format(self.config.params.default.log_level)
                    ],
                    log_output=log
                ))
        except WebDriverException as e:
            logger.error("[{}][{}] Cannot create browser: {}".format(
                self.request.client_id, self.task_hash, e))
            return False

        # set geometry.
        self.browser.set_window_size(self.x, self.y)

        # set timeouts.
        self.browser.set_page_load_timeout(self.request.page_timeout)
        self.browser.set_script_timeout(self.request.script_timeout)

        return True

    def process(self, urls, cookies, screenshots, scripts) -> dict:
        if self.create_browser():
            return self.fetch(urls, cookies, screenshots, scripts)
        else:
            return {}

    def __del__(self):
        super(ChromeGenericBrowser, self).__del__()


class FirefoxGenericBrowser(GenericBrowser):
    def __init__(self, config, request, task_hash, order):
        super(FirefoxGenericBrowser, self).__init__(
            config, request, task_hash, order)

    def create_browser(self) -> bool:
        try:
            self.display = Display(
                backend="xvnc", size=(self.x, self.y), rfbport=0)
            self.display.start()
        except Exception as e:
            logger.warning("[{}][{}] Cannot create virtual display: {}".format(
                self.request.client_id, self.task_hash, e))
            return False

        if self.config.params.default.firefox_profile:
            self.keep_temp = True

            self.profile_dir = os.path.join(
                self.config.params.default.firefox_profiles_dir, self.config.params.default.firefox_profile)

            try:
                os.makedirs(self.profile_dir, exist_ok=True)
            except Exception as e:
                logger.warning("[{}][{}] Cannot create profile directory: {}".format(
                    self.request.client_id, self.task_hash, e))
                return False

        if not self.config.params.default.firefox_profile:
            self.keep_temp = self.config.params.default.keep_temp

            try:
                self.profile_dir = mkdtemp(dir=self.config.params.default.firefox_profiles_dir,
                                           prefix="task_{}_".format(self.task_hash))
            except Exception as e:
                logger.warning("[{}][{}] Cannot create temporary directory: {}".format(
                    self.request.client_id, self.task_hash, e))
                return False

        options = FirefoxOptions()
        options.binary_location = self.config.params.default.firefox_path

        # add application related arguments.
        options.add_argument("--new-instance")
        options.add_argument("-profile")
        options.add_argument(self.profile_dir)
        # open urls in tabs, not in windows.
        options.set_preference("browser.link.open_newwindow", 3)
        # disable all notifications.
        options.set_preference("dom.webnotifications.enabled", False)
        # disable all media autoplaying.
        options.set_preference("media.autoplay.default", 5)

        # add user-defined arguments.
        for argument in self.request.browser.argument:
            try:
                options.add_argument(argument)
            except InvalidArgumentException:
                logger.warning("[{}][{}] Invalid argument: {}".format(
                    self.request.client_id, self.task_hash, argument))
                continue

        # create browser.
        log = os.path.join(self.profile_dir, "geckodriver.log")

        try:
            self.browser = webdriver.Firefox(
                options=options,
                service=FirefoxService(
                    executable_path=FIREFOX_GECKODRIVER_WRAPPER,
                    log_output=log,
                    service_args=[
                        "--log", self.config.params.default.log_level.lower(),
                        self.config.params.default.firefox_driver_path,
                        self.profile_dir
                    ]
                ),
                seleniumwire_options=self.selenium_wire_options,
            )
        except WebDriverException as e:
            logger.error("[{}][{}] Cannot create browser: {}".format(
                self.request.client_id, self.task_hash, e))
            return False

        # add extensions.
        for extension in self.request.browser.extension:
            try:
                self.browser.install_addon(
                    os.path.join(self.config.params.default.firefox_extensions_dir, extension.strip()))
            except Exception as e:
                logger.warning("[{}][{}] Invalid extension: {}, {}".format(
                    self.request.client_id, self.task_hash, extension.strip(), e))
                continue

        # set geometry.
        self.browser.set_window_size(self.x, self.y)

        # set timeouts.
        self.browser.set_page_load_timeout(self.request.page_timeout)
        self.browser.set_script_timeout(self.request.script_timeout)

        return True

    def process(self, urls, cookies, screenshots, scripts) -> dict:
        if self.create_browser():
            return self.fetch(urls, cookies, screenshots, scripts)
        else:
            return {}

    def __del__(self):
        super(FirefoxGenericBrowser, self).__del__()
