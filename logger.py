import requests, logging, time, json
from typing import Literal

logger = logging.getLogger(__name__)
colored: bool = False
ntfy_topic: str = None

tags = {
    "ok":   "  OK  ",
    "info": " INFO ",
    "fail": " FAIL ",
    "warn": " WARN ",
    "trash":" .... "
}

ntfy_tags = {
    'i':'speech_balloon',   # info tag
    'w':'warning',          # warning tag
    'e':'x'                 # error tag
}

priorities = {
    'e':'high',             # high priority
    'w':'default',          # default priority
    'i':'low',              # low priority
}

def init_logger(
    filename: str, 
    colored_output: bool = False, 
    ntfy_topic_str: str = None):
    global colors, colored, ntfy_topic

    # load colors from config
    with open("config.json", 'r') as f:
        colors = json.load(f)["colors"]
        for key, value in colors.items():
            value = value.split('.')
            if len(value) > 1:
                colors[key] = f"\033[{value[0]}m\033[{value[1]}m"
            else:
                colors[key] = f"\033[{value[0]}m"

    # colored log output
    colored = colored_output
    # update logger config
    logging.basicConfig(filename=filename, format="%(message)s", level=logging.INFO)
    # separator
    logger.info('-----------------------------------------')

    # test ntfy
    if ntfy_topic_str != None:
        # make a post request
        test_ntfy = requests.post(
            f"https://ntfy.sh/{ntfy_topic_str}",
            data=f"This is a test message to check if provided ntfy.sh topic is correct. Bot is now launching...",
            headers={
                "Title": "ntfy.sh topic test",
                "Priority": "min",
                "Tags": f"{ntfy_tags['i']}"
            }
        )
        # topic is ok
        if test_ntfy.ok:
            # enable/disable ntfy.sh (global)
            ntfy_topic = ntfy_topic_str
            log("trash", "ntfy.sh topic is ok")
        # topic incorrect
        else:
            ntfy_topic = None
            log("fail", "invalid ntfy.sh topic! notifications disabled")

def log(
    tag: Literal["ok", "info", "fail", "warn", "trash"],
    text: str,
    will_notify: bool = False,
    post_title: str = 'kitisbot notification',
    post_tag: Literal['i', 'w', 'e'] = 'i'):
    
    # concat log message and print it
    if colored:
        output = '\033[90m' + time.asctime() + '\033[0m ' + colors[tag] + '[' + tags[tag] + ']\033[0m > ' + text
        print(output)
    else:
        output = '['+ tags[tag] + '] > ' + text
        print(output)
    
    # write message in log
    if tag == "fail":      # error
        logger.error(output)
    elif tag == "warn":    # warning
        logger.warning(output)
    else:               # info
        logger.info(output)
    
    # post message to ntfy.sh if needed
    if ntfy_topic != None and will_notify:
        ntfy_post(post_tag, post_title, text)

def ntfy_post(
    tag: Literal['i', 'w', 'e'],
    title: str,
    text: str):
    
    requests.post(
        f"https://ntfy.sh/{ntfy_topic}",
        data=f"{text}",
        headers={
            "Title": f"{title}",
            "Priority": f"{priorities[tag]}",
            "Tags": f"{ntfy_tags[tag]}"
        }
    )

# for tests
if __name__ == "__main__":
    print(colors)
    init_logger("log.log", True)
    log("ok",   "Test text")
    log("info", "Test text")
    log("fail", "Test text")
    log("warn", "Test text")
    log("trash","Test text")