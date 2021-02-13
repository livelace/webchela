# webchela


***webchela*** ("web" + "chela") is a daemon for interacting with web pages through automated browsers (Chrome or Firefox). 

### Main goal:

Provide a plugin endpoint to other tool - [gosquito](https://github.com/livelace/gosquito). 

### Features:

* Accepts commands from clients over [GRPC](https://grpc.io/). 
* Split fetched data into chunks.
* Fully controlled on client side (browser type, browser extensions, loads etc.). 
* Expose server loads to clients, control loads itself.
* Works in headless mode ([TigerVNC](https://wiki.archlinux.org/index.php/TigerVNC)).
* PoC command line client.

### Dependencies:

* Python 3.7+
* Chrome, [chromedriver](https://chromedriver.chromium.org/).
* Firefox, [geckodriver](https://github.com/mozilla/geckodriver).
* TigerVNC.

### Quick start:

```shell script
# start daemon
user@localhost / $ docker run --name webchela -ti --rm -v /dev/shm:/dev/shm docker.io/livelace/webchela:v1.4.0
2021-02-09 18:11:54 webchela.config INFO Config sample was written successfully: /home/webchela/.webchela.toml
2021-02-09 18:11:54 webchela.server INFO webchela v1.4.0

# fetch page with simple client
user@localhost / $ docker exec webchela webchela-cli --url https://google.com
2021-02-09 18:12:13 webchela.client INFO webchela v1.4.0
2021-02-09 18:12:13 webchela.client INFO Send task. Total urls: 1. Total batches: 1.
2021-02-09 18:12:13 webchela.client INFO Send batch: 0. Batch size: 1
2021-02-09 18:12:19 webchela.client INFO Task completed.

# show data
user@localhost / $ docker exec webchela tree /tmp/webchela
/tmp/webchela
└── 18:12:13_09.02.2021
    └── BATCH0
        ├── URL0_CONTENT_TYPE_google.txt
        ├── URL0_PAGE_BODY_google.html
        ├── URL0_PAGE_URL_google.txt
        ├── URL0_STATUS_CODE_google.txt
        └── URL0_URL_google.txt

2 directories, 5 files
```

### Config sample:

```toml
[default]

#browser_type            = "chrome"
#browser_extension       = ["bypass-paywalls-1.7.6.crx", "ublock-origin-1.30.6.crx"]

#browser_type            = "firefox"
#browser_extension       = ["bypass-paywalls-1.7.6.xpi", "ublock-origin-1.30.6.xpi"]

#browser_geometry        = "1024x768"
#browser_instance        = 1
#browser_instance_tab    = 5
#browser_page_size       = "10M"
#browser_page_timeout    = 20
#browser_script_timeout  = 20

#browser_proxy           = "http://1.2.3.4:3128"
#browser_proxy           = "socks5://user:pass@1.2.3.4:1080"

#chrome_driver_path      = "/usr/bin/chromedriver"
#chrome_extensions_dir   = "/tmp"
#chrome_path             = "/usr/bin/google-chrome-stable"
#chrome_profiles_dir     = "/tmp"

#chunk_size              = "3M"

#cpu_load                = 25

#firefox_driver_path     = "/usr/bin/geckodriver"
#firefox_extensions_dir  = "/tmp"
#firefox_path            = "/usr/lib64/firefox/firefox"
#firefox_profiles_dir    = "/tmp"

#log_level               = "INFO"

#mem_free                = "1G"

#task_timeout            = 300

[client]

#client_id               = "webchela-cli"
#batch_size              = 100
#output_dir              = "/tmp/webchela"
#server                  = "127.0.0.1:50051"
#scripts                 = ["return 42;"]

[server]

#listen                  = "0.0.0.0:50051"
#workers                 = 1
```