from time import sleep

import coloredlogs
import logging
import shutil
import uuid

from pyvirtualdisplay import Display
from seleniumwire import webdriver
from selenium.common.exceptions import *
from selenium.webdriver import FirefoxOptions
from tempfile import mkdtemp

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

        # save window handles order.
        window_handles = []

        # open urls.
        for index in range(len(urls)):
            url = urls[index]

            try:
                if index == 0:
                    self.browser.get(url)
                    window_handles.append(self.browser.current_window_handle)
                else:
                    self.browser.execute_script('window.open("{}","_blank");'.format(url))
                    self.browser.switch_to.window(self.browser.window_handles[index])
                    window_handles.append(self.browser.current_window_handle)

            except TimeoutException:
                logger.warning("[{}][{}] Timeout during open URL: {}".format(
                    self.request.client_id, self.task_hash, url))
                continue

            except WebDriverException as e:
                logger.error("[{}][{}] Browser error during open URL: {}, {}".format(
                    self.request.client_id, self.task_hash, url, e))
                return {self.order: chunks}

            except Exception as e:
                logger.error("[{}][{}] Unexpected error during open URL: {}, {}".format(
                    self.request.client_id, self.task_hash, url, e))
                return {self.order: chunks}

        # wait for all tabs.
        while True:
            ready = True

            for index in range(len(urls)):
                url = urls[index]
                window = window_handles[index]

                try:
                    self.browser.switch_to.window(window)
                    status = self.browser.execute_script('return document.readyState;')

                    if status != "complete":
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

                # don't waste cpu power.
                sleep(self.config.params.default.tab_hop_delay)

            if ready:
                break

        # save urls data (status_code AND content_type).
        urls_data = {}
        for request in self.browser.requests:
            if request.response:
                urls_data[request.url] = (request.response.status_code, request.response.headers['Content-Type'])

        # process tabs.
        for index in range(len(urls)):
            uid = str(uuid.uuid4())
            url = urls[index]
            window = window_handles[index]

            try:
                self.browser.switch_to.window(window)

                # Result will contain all data.
                result = webchela_pb2.Result(
                    UUID=uid,
                    page_url=self.browser.current_url,
                    page_title=self.browser.title,
                    url=url,
                    status_code=urls_data[self.browser.current_url][0],
                    content_type=urls_data[self.browser.current_url][1]
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
                logger.debug("uuid: {}, url: {}, title: {}".format(uid, url, self.browser.title))

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

        if self.temp_dir:
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
