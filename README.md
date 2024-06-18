# webchela


***webchela*** ("web" + "chela") is a daemon for interacting with web pages through automated browsers (Chrome or Firefox). 

### Main goal:

Provide a plugin endpoint to other tool - [gosquito](https://github.com/livelace/gosquito). 

### Features:

* Accepts tasks from clients over single [GRPC](https://grpc.io/) connection (control/data links). 
* Combines tasks into batches, control how many browser instances/tabs should run in parallel.
* Splits fetched data into sized chunks (avoid transport limits).
* Fully controlled on client side (browser type/arguments/extensions etc.). 
* Exposes server load to clients (client may skip busy one and switch to an idle server).
* Can utilize GPU with help of [VirtualGL](https://www.virtualgl.org/)/[TurboVNC](https://www.turbovnc.org/) for graphics offloading.
* Works in fully graphical mode (not native [headless mode](https://developer.chrome.com/docs/chromium/new-headless)), 
exposes 590x/VNC ports per browser instance for visual inspection.
* Resizes browser window dynamically. 
* Makes full page screenshots and/or specific page elements. 
* Passing cookies to pages in JSON.


### Quick start:

**Start daemon (software rendering)**
```shell script
user@localhost / $ docker run -p 50051:50051 -ti --rm -v /dev/shm:/dev/shm ghcr.io/livelace/webchela:v1.8.0
2024-06-17 21:17:19,438 INFO supervisord started with pid 1
2024-06-17 21:17:20,440 INFO spawned: 'xorg' with pid 2
2024-06-17 21:17:20,442 INFO spawned: 'webchela' with pid 3
2024-06-17 21:17:20,470 WARN exited: xorg (exit status 1; not expected)
2024-06-17 21:17:20 webchela.config INFO Config sample was written successfully: /home/user/.webchela.toml
2024-06-17 21:17:20 webchela.server INFO webchela v1.8.0

```

**Start daemon (GPU rendering)**
```shell script
user@localhost / $ docker run --privileged -p 50051:50051 -ti --rm -v /dev/shm:/dev/shm ghcr.io/livelace/webchela:v1.8.0
2024-06-17 21:19:55,179 INFO supervisord started with pid 1
2024-06-17 21:19:56,180 INFO spawned: 'xorg' with pid 7
2024-06-17 21:19:56,182 INFO spawned: 'webchela' with pid 8
2024-06-17 21:19:56 webchela.server INFO webchela v1.8.0
2024-06-17 21:19:57,782 INFO success: xorg entered RUNNING state, process has stayed up for > than 1 seconds (startsecs)
2024-06-17 21:19:57,782 INFO success: webchela entered RUNNING state, process has stayed up for > than 1 seconds (startsecs)
```

**Use gosquito [configuration example](https://github.com/livelace/gosquito/blob/master/docs/plugins/process/webchela.md)**

### Configuration example:

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

### Known issues:

**Making full page screenshots in Chrome may finish with error: 
"Message: disconnected: Unable to receive message from renderer"**

Chromedriver has hardcoded timeout value for making page screenshots - 10 seconds, 
it could be not enough for really big screenshots.  
Use Firefox or wait for [fix](https://bugs.chromium.org/p/chromedriver/issues/detail?id=3916&q=screenshot%20timeout&can=2).