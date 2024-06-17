# webchela


***webchela*** ("web" + "chela") is a daemon for interacting with web pages through automated browsers (Chrome or Firefox). 

### Main goal:

Provide a plugin endpoint to other tool - [gosquito](https://github.com/livelace/gosquito). 

### Features:

* Accepts tasks from clients over single [GRPC](https://grpc.io/) connection (control/data links). 
* Combines tasks into batches, control how many browser instances/tabs should run in parallel.
* Splits fetched data into chunks (avoid transport limits).
* Fully controlled on client side (browser type/arguments/extensions, cookies etc.). 
* Exposes server load to clients (client may skip busy one and switch to an idle server).
* Works in fully graphical mode (not native [headless mode](https://developer.chrome.com/docs/chromium/new-headless)), 
exposes 590x/VNC ports per browser instance for visual control.
* Resizes browser window dynamically. 
* Makes full page screenshots and/or specific page elements. 

### Dependencies:

* Python 3.11+
* Chrome, [chromedriver](https://chromedriver.chromium.org/).
* Firefox, [geckodriver](https://github.com/mozilla/geckodriver).
* [TigerVNC](https://wiki.archlinux.org/index.php/TigerVNC).

### Quick start:

**Start daemon**
```shell script
user@localhost / $ docker run -p 50051:50051 -ti --rm -v /dev/shm:/dev/shm ghcr.io/livelace/webchela:v1.8.0
2021-02-09 18:11:54 webchela.config INFO Config sample was written successfully: /home/webchela/.webchela.toml
2021-02-09 18:11:54 webchela.server INFO webchela v1.8.0
```

**Use gosquito [example configuration](https://github.com/livelace/gosquito/blob/master/docs/plugins/process/webchela.md)**

### Config sample:

```toml

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

```

### Screenshot example:

![main](assets/worldclock.png)
