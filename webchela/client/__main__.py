import argparse
import grpc
import coloredlogs
import logging
import os
import signal

from datetime import datetime
from slugify import slugify

import webchela.core.protobuf.webchela_pb2 as webchela_pb2
import webchela.core.protobuf.webchela_pb2_grpc as webchela_pb2_grpc

from webchela.core.config import Config
from webchela.core.utils import *
from webchela.core.vars import *

config = Config()
logger = logging.getLogger("webchela.client")
coloredlogs.install(fmt=DEFAULT_LOG_FORMAT, level=config.params.default.log_level)


def _save_to_file(path, file, data, message):
    try:
        target_file = os.path.join(path, file)
        with open(target_file, "w") as f:
            f.write(data)
        logger.debug("Data saved into file: {}".format(target_file))
    except Exception as e:
        logger.error("{}: {}, {}".format(message, file, e))
        sys.exit(1)


def save_data(date, batch, data):
    batch_dir = "BATCH{}".format(batch)
    data_dir = date.strftime("%H:%M:%S_%d.%m.%Y")
    target_path = os.path.join(config.params.client.output_dir, data_dir, batch_dir)

    try:
        os.makedirs(target_path)
    except Exception as e:
        logger.error("Cannot create data directory: {}, {}".format(target_path, e))
        sys.exit(1)

    for index in range(len(data)):
        result = data[index]
        title_identity = slugify(result.page_title, max_length=200)

        # Save "page_body".
        page_body_filename = "URL{}_PAGE_BODY_{}.html".format(index, title_identity)
        _save_to_file(target_path, page_body_filename, result.page_body, "Cannot save page body into file")

        # Save "page_url".
        page_url_filename = "URL{}_PAGE_URL_{}.txt".format(index, title_identity)
        _save_to_file(target_path, page_url_filename, result.page_url, "Cannot save page url into file")

        # Save "script_output".
        if result.script_output:
            script_output_filename = "URL{}_SCRIPT_OUTPUT_{}.txt".format(index, title_identity)
            _save_to_file(
                target_path, script_output_filename, result.script_output[0], "Cannot save script output into file")

        # Save "url".
        url_filename = "URL{}_URL_{}.txt".format(index, title_identity)
        _save_to_file(target_path, url_filename, result.url, "Cannot save url into file")

        # Save "status_code".
        status_code_filename = "URL{}_STATUS_CODE_{}.txt".format(index, title_identity)
        _save_to_file(target_path, status_code_filename, str(result.status_code), "Cannot save status code into file")

        # Save "content_type".
        content_type_filename = "URL{}_CONTENT_TYPE_{}.txt".format(index, title_identity)
        _save_to_file(target_path, content_type_filename, result.content_type, "Cannot save content type into file")


def send_task(task):
    results = []

    with grpc.insecure_channel(config.params.client.server) as channel:
        stub = webchela_pb2_grpc.ServerStub(channel)

        chunks_buffer = bytes()

        # results are split into chunks.
        # "end" field set to "true" if result boundaries are reached.
        responses = stub.RunTask(task)

        for response in responses:
            # append chunk to buffer.
            chunks_buffer += response.chunk

            # detect buffer completeness.
            if response.end:
                result = webchela_pb2.Result()
                result.ParseFromString(chunks_buffer)
                results.append(result)

                chunks_buffer = bytes()

    return results


def main():
    logger.info("{} {}".format(APP_NAME, APP_VERSION))

    signal.signal(signal.SIGINT, exit_handler)

    # Task date.
    date = datetime.now()

    # Parse arguments.
    parser = argparse.ArgumentParser(prog=APP_NAME)

    url_group = parser.add_mutually_exclusive_group(required=True)
    url_group.add_argument("--url", help=HELP_CLIENT_URL)
    url_group.add_argument("--url-file", type=argparse.FileType("r"), help=HELP_CLIENT_URL_FILE)

    script_group = parser.add_mutually_exclusive_group()
    script_group.add_argument("--script", help=HELP_CLIENT_SCRIPT)
    script_group.add_argument("--script-file", type=argparse.FileType("r"), help=HELP_CLIENT_SCRIPT_FILE)

    args = parser.parse_args()

    # Derive user-defined URLs.
    urls = []

    if args.url:
        urls.append(args.url)
    elif args.url_file:
        for url in args.url_file.read().split("\n"):
            if url:
                urls.append(url)

    # Derive user-defined javascript.
    # In this simple client we use only one script,
    # but it can contain multiple scripts.
    scripts = []

    if args.script:
        scripts.append(args.script)
    elif args.script_file:
        scripts.append(args.script_file.read())

    # Assemble and send task.
    urls_batches = split_urls(urls, config.params.client.batch_size)

    logger.info("Send task. Total urls: {}. Total batches: {}.".format(len(urls), len(urls_batches)))

    for index in range(len(urls_batches)):
        urls_batch = urls_batches[index]

        task = webchela_pb2.Task(
            urls=urls,
            scripts=scripts,
        )

        task.browser.argument.extend(config.params.default.browser_argument)
        task.browser.extension.extend(config.params.default.browser_extension)
        task.browser.geometry = config.params.default.browser_geometry
        task.browser.instance = config.params.default.browser_instance
        task.browser.instance_tab = config.params.default.browser_instance_tab
        task.browser.page_size = config.params.default.browser_page_size
        task.browser.page_timeout = config.params.default.browser_page_timeout
        task.browser.proxy = config.params.default.browser_proxy
        task.browser.script_timeout = config.params.default.browser_script_timeout
        task.browser.type = config.params.default.browser_type

        task.client_id = config.params.client.client_id
        task.chunk_size = config.params.default.chunk_size
        task.cpu_load = config.params.default.cpu_load
        task.mem_free = config.params.default.mem_free
        task.timeout = config.params.default.task_timeout

        try:
            logger.info("Send batch: {}. Batch size: {}".format(index, len(urls_batch)))

            results = send_task(task)

            if len(results) == 0:
                logger.warning("Results are empty, something wrong on server side!")
            else:
                save_data(date, index, results)

        except Exception as e:
            logger.error("Task failed. Last batch: {}. Error: {}.".format(index, e))
            break

    logger.info("Task completed.")


if __name__ == '__main__':
    main()
