import requests, logging, time, json, traceback
from typing import Literal
import regex_helper as rh

logger = logging.getLogger(__name__)
colored: bool = False
ntfy_topic: str = ""

tags = {
    "ok":   "  OK  ",
    "info": " INFO ",
    "fail": " FAIL ",
    "warn": " WARN ",
    "trash":" .... "
}

ntfy_tags = {
    'e':'x',                # error tag
    'w':'warning',          # warning tag
    'i':'speech_balloon'    # info tag
}

priorities = {
    'e':'high',             # high priority
    'w':'default',          # default priority
    'i':'low',              # low priority
}

def init_logger(
    filename_info: str,
    filename_debug: str = "",
    colored_output: bool = False,
    ntfy_topic_str: str = ""):
    """Initialize logger.
    `filename_info` must be provided and `filename_debug` is optional (provide `""` to disable it).
    `colored_output` adds ASCII escape codes (for example, `"\\033[30m"` is red), so use it with cat or tail command.
    `ntfy_topic_str` is also optional. If you want to get notifications via ntfy.sh, then provide topic name like `"kitisbot_ntfy"`, not the full link!"""
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

    logger.setLevel(logging.DEBUG)
    # create file handler
    fhandler_info = logging.FileHandler(filename_info)
    fhandler_info.setLevel(logging.INFO)
    # set formatter
    formatter = logging.Formatter("%(message)s")
    fhandler_info.setFormatter(formatter)
    # add file handler to logger
    logger.addHandler(fhandler_info)

    if filename_debug:
        fhandler_debug = logging.FileHandler(filename_debug)
        fhandler_debug.setLevel(logging.DEBUG)
        fhandler_debug.setFormatter(formatter)
        logger.addHandler(fhandler_debug)

    # separator
    logger.info('-----------------------------------------')

    # test ntfy
    if ntfy_topic_str:
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
            ntfy_topic = ""
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
        output = time.asctime() + ' ['+ tags[tag] + '] > ' + text
        print(output)

    # write message in log
    if tag == "fail":      # error
        logger.error(output)
        # debug - write traceback
        tb_full = traceback.format_exc()
        tb_parts = tb_full.split("During handling of the above exception, another exception occurred:")
        # extract filename, line number and line
        match = rh.extract_regex(r'Traceback \(most recent call last\):\s*File (\S+),.*line (\d+).*\n\s+(.*)', tb_parts[-1])
        tb = f"File: {match[0]}, line {match[1]}\n{match[2]}" if match else tb_parts[-1].strip()
        logger.debug(f"Traceback:\n{tb}\nTraceback end\n")
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
    init_logger("log.log", "", False)
    log("ok",   "Test text")
    log("info", "Test text")
    log("fail", "Test text")
    log("warn", "Test text")
    log("trash","Test text")
