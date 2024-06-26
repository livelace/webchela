import sys

import coloredlogs
import gc
import grpc
import importlib
import logging
import signal

from concurrent import futures
from concurrent.futures import ThreadPoolExecutor
from time import sleep
from threading import Lock

import webchela.core.protobuf.webchela_pb2 as webchela_pb2
import webchela.core.protobuf.webchela_pb2_grpc as webchela_pb2_grpc

from webchela.core.browser import chrome_grabber, firefox_grabber
from webchela.core.config import Config

# Get configuration, set log level.
from webchela.core.utils import get_load, gen_hash, split_items, human_size, exit_handler
from webchela.core.validate import is_browser_type
from webchela.core.vars import DEFAULT_LOG_FORMAT, APP_NAME, APP_VERSION

config = Config()
logger = logging.getLogger("webchela.server")
coloredlogs.install(fmt=DEFAULT_LOG_FORMAT, level=config.params.default.log_level)

# Disable "noise" logging.
logging.getLogger("easyprocess").setLevel(logging.ERROR)
logging.getLogger("hpack").setLevel(logging.ERROR)
logging.getLogger("passlib").setLevel(logging.ERROR)
logging.getLogger("pyvirtualdisplay.abstractdisplay").setLevel(logging.ERROR)
logging.getLogger("seleniumwire").setLevel(logging.ERROR)
logging.getLogger("selenium.webdriver.remote.remote_connection").setLevel(logging.ERROR)
logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)

get_load_mutex = Lock()
get_load_busy = False


class Server(webchela_pb2_grpc.ServerServicer):
    def GetLoad(self, request, context):
        # Prevent race between clients.
        # Give clients "cpu_load=1, mem_free=1, score=1",
        # if some client already requesting server load.
        global get_load_busy

        if get_load_busy:
            # don't use "0", "0" could mean wrong protobuf message fields values.
            return webchela_pb2.Load(cpu_load=1, mem_free=1, score=1)
        else:
            with get_load_mutex:
                get_load_busy = True

                _, cpu_load, mem_free, score = get_load(0, 0, 5)

                get_load_busy = False

                return webchela_pb2.Load(cpu_load=cpu_load, mem_free=mem_free, score=score)

    def RunTask(self, request, context):
        # Generate hash for log messages.
        task_hash = gen_hash()

        # --------------------------------------------------------------------------------------------------------------
        # Set defaults, if client provides nothing.

        if not request.browser.type:
            request.browser.type = config.params.default.browser_type
        else:
            request.browser.type = is_browser_type("", request.browser.type, config.params.default.browser_type)

        if not request.browser.argument:
            request.browser.argument.extend(config.params.default.browser_argument)

        if not request.browser.extension:
            request.browser.extension.extend(config.params.default.browser_extension)

        if request.browser.instance == 0:
            request.browser.instance = config.params.default.browser_instance

        if request.browser.instance_tab == 0:
            request.browser.instance_tab = config.params.default.browser_instance_tab

        if not request.browser.proxy:
            request.browser.proxy = config.params.default.browser_proxy


        if request.chunk_size == 0:
            request.chunk_size = config.params.default.chunk_size

        if request.cpu_load == 0:
            request.cpu_load = config.params.default.cpu_load

        if request.mem_free == 0:
            request.mem_free = config.params.default.mem_free

        if request.page_size == 0:
            request.page_size = config.params.default.page_size

        if request.page_timeout == 0:
            request.page_timeout = config.params.default.page_timeout

        if not request.retry_codes:
            request.retry_codes.extend(config.params.default.retry_codes)

        if request.retry_codes_tries == 0:
            request.retry_codes_tries = config.params.default.retry_codes_tries

        if request.screenshot_timeout == 0:
            request.screenshot_timeout = config.params.default.screenshot_timeout

        if request.script_timeout == 0:
            request.script_timeout = config.params.default.script_timeout

        if request.timeout == 0:
            request.timeout = config.params.default.task_timeout

        # Split urls per tabs.
        jobs_urls = split_items(request.urls, request.browser.instance_tab)
        jobs_cookies = split_items(request.cookies, request.browser.instance_tab)
        jobs_screenshots = split_items(request.screenshots, request.browser.instance_tab)
        jobs_scripts = split_items(request.scripts, request.browser.instance_tab)

        # --------------------------------------------------------------------------------------------------------------

        # Save jobs amount (jobs list will be shrunk).
        jobs_amount = len(jobs_urls)

        logger.info(
            "[{}][{}] Task received. Total: jobs: {}, urls: {}, cookies: {}, screenshots: {}, scripts {}.".format(
                request.client_id,
                task_hash,
                jobs_amount,
                len(request.urls),
                len(request.cookies),
                len(request.screenshots),
                len(request.scripts)))

        logger.debug("[{}][{}] browser.type: {}".format(
            request.client_id, task_hash, request.browser.type))
        logger.debug("[{}][{}] browser.argument: {}".format(
            request.client_id, task_hash, request.browser.argument))
        logger.debug("[{}][{}] browser.extension: {}".format(
            request.client_id, task_hash, request.browser.extension))
        logger.debug("[{}][{}] browser.geometry: {}".format(
            request.client_id, task_hash, request.browser.geometry))
        logger.debug("[{}][{}] browser.instance: {}".format(
            request.client_id, task_hash, request.browser.instance))
        logger.debug("[{}][{}] browser.instance_tab: {}".format(
            request.client_id, task_hash, request.browser.instance_tab))
        logger.debug("[{}][{}] browser.proxy: {}".format(
            request.client_id, task_hash, request.browser.proxy))

        logger.debug("[{}][{}] debug.pre_close_delay: {}".format(
            request.client_id, task_hash, request.debug.pre_close_delay))
        logger.debug("[{}][{}] debug.pre_cookie_delay: {}".format(
            request.client_id, task_hash, request.debug.pre_cookie_delay))
        logger.debug("[{}][{}] debug.pre_open_delay: {}".format(
            request.client_id, task_hash, request.debug.pre_open_delay))
        logger.debug("[{}][{}] debug.pre_process_delay: {}".format(
            request.client_id, task_hash, request.debug.pre_process_delay))
        logger.debug("[{}][{}] debug.pre_screenshot_delay: {}".format(
            request.client_id, task_hash, request.debug.pre_screenshot_delay))
        logger.debug("[{}][{}] debug.pre_script_delay: {}".format(
            request.client_id, task_hash, request.debug.pre_script_delay))
        logger.debug("[{}][{}] debug.pre_wait_delay: {}".format(
            request.client_id, task_hash, request.debug.pre_wait_delay))

        logger.debug("[{}][{}] chunk_size: {}".format(
            request.client_id, task_hash, human_size(request.chunk_size)))
        logger.debug("[{}][{}] cpu_load: {}%".format(
            request.client_id, task_hash, request.cpu_load))
        logger.debug("[{}][{}] mem_free: {}".format(
            request.client_id, task_hash, human_size(request.mem_free)))
        logger.debug("[{}][{}] page_size: {}".format(
            request.client_id, task_hash, human_size(request.page_size)))
        logger.debug("[{}][{}] page_timeout: {}".format(
            request.client_id, task_hash, request.page_timeout))
        logger.debug("[{}][{}] retry_codes: {}".format(
            request.client_id, task_hash, request.retry_codes))
        logger.debug("[{}][{}] retry_codes_tries: {}".format(
            request.client_id, task_hash, request.retry_codes_tries))
        logger.debug("[{}][{}] screenshot_timeout: {}".format(
            request.client_id, task_hash, request.screenshot_timeout))
        logger.debug("[{}][{}] script_timeout: {}".format(
            request.client_id, task_hash, request.script_timeout))
        logger.debug("[{}][{}] tab_open_randomize: {}".format(
            request.client_id, task_hash, request.tab_open_randomize))
        logger.debug("[{}][{}] timeout: {}".format(
            request.client_id, task_hash, request.timeout))

        jobs_running = []  # will contain jobs/threads.
        results = {}  # will contain results of all jobs.
        timeout_counter = 0  # count task timeout.

        # Main thread pool for job processing.
        # Amount of threads is limited by browser instances amount, not pool itself.
        executor = ThreadPoolExecutor()

        # Iterate over jobs.
        while True:
            if timeout_counter > request.timeout:
                logger.warning("[{}][{}] Task timeout: {}s".format(request.client_id, task_hash, request.timeout))
                break

            # No jobs, no running jobs. Exit.
            if len(jobs_urls) == 0 and len(jobs_running) == 0:
                break

            # Run new job if limits (number of jobs, workload limits) are good.
            if len(jobs_urls) > 0 and len(jobs_running) < request.browser.instance:
                # 1 second resolution workload stat.
                load, cpu, mem, _ = get_load(request.cpu_load, request.mem_free)
                if load:
                    job_urls = jobs_urls.pop()
                    job_cookies = []
                    job_screenshots = []
                    job_scripts = []

                    if len(jobs_cookies) > 0:
                        job_cookies = jobs_cookies.pop()

                    if len(jobs_screenshots) > 0:
                        job_screenshots = jobs_screenshots.pop()

                    if len(jobs_scripts) > 0:
                        job_scripts = jobs_scripts.pop()

                    job_order = len(jobs_urls)  # be careful of jobs.pop()

                    if request.browser.type == "chrome":
                        job = executor.submit(chrome_grabber, config, request, task_hash, job_order, job_urls,
                                              job_cookies, job_screenshots, job_scripts)
                    else:
                        job = executor.submit(firefox_grabber, config, request, task_hash, job_order, job_urls,
                                              job_cookies, job_screenshots, job_scripts)

                    jobs_running.append(job)

                    logger.debug("[{}][{}] Run job: {} of {}".format(
                        request.client_id, task_hash, jobs_amount - len(jobs_urls), jobs_amount))
                else:
                    logger.warning(
                        "[{}][{}] Workload limits are reached: current: {:>4}%, {}, limit: {:>2}%, {}".format(
                            request.client_id, task_hash, cpu, human_size(mem),
                            request.cpu_load, human_size(request.mem_free)))

            # Wait and check running jobs.
            for job in jobs_running:
                if job.done():
                    result = job.result()
                    if result:
                        results = {**results, **result}

                    jobs_running.remove(job)

            timeout_counter += 1
            sleep(1)

        # Clean jobs (if task timeout, for instance).
        executor.shutdown(wait=False)

        # Assemble ordered results in chunks.
        chunks = []

        if len(results) > 0:
            for order in range(jobs_amount):
                for chunk in results[order]:
                    chunks.append(chunk)

        logger.info("[{}][{}] Task completed. Total: chunks: {}.".format(request.client_id, task_hash, len(chunks)))

        # # Explicitly free and clean resources.
        # gc.collect()

        # Return ordered data to client.
        for chunk in chunks:
            yield chunk


def main():
    logger.info("{} {}".format(APP_NAME, APP_VERSION))

    signal.signal(signal.SIGINT, exit_handler)

    try:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=config.params.server.workers))
        webchela_pb2_grpc.add_ServerServicer_to_server(Server(), server)
        server.add_insecure_port(config.params.server.listen)
        server.start()
        server.wait_for_termination()

    except RuntimeError as e:
        logger.error("Cannot start server: {}".format(e))


if __name__ == "__main__":
    main()
