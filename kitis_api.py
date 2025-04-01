import requests, json, time, logger
from typing import Literal
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from logger import log

# some dictionaries for formatting
t_days = {
    "Пн": "Понедельник",
    "Вт": "Вторник",
    "Ср": "Среда",
    "Чт": "Четверг",
    "Пт": "Пятница",
    "Сб": "Суббота",
    "Вс": "Воскресенье"
}

t_bells_monday = {
    "1":"8:30-9:00 / 15:20-15:50",
    "2":"9:10-10:30",
    "3":"10:40-12:00",
    "4":"12:20-13:40",
    "5":"13:50-15:10",
    "6":"16:00-17:20",
    "7":"17:30-18:50"
}

t_bells_week = {
    "1":"8:30-10:00",
    "2":"10:10-11:40",
    "3":"12:10-13:40",
    "4":"13:50-15:20",
    "5":"15:30-17:00",
    "6":"17:10-18:40",
    "7":"18:50-20:20"
}

statuses = {
    200: "В норме",
    204: "Нет контента (в норме)",
    400: "Неверный запрос",
    401: "Неавторизованный (ошибка запроса)",
    403: "Доступ запрещён",
    404: "Не найдено",
    408: "Таймаут запроса",
    409: "Конфликт запросов",
    418: "Я чайник",
    429: "Слишком много запросов",
    500: "Ошибка внутреннего сервера",
    502: "Неверный шлюз",
    503: "Сервис недоступен",
    504: "Таймаут шлюза"
}

# create links dictionary
links = dict()

# fake user-agent for sessions
ua = UserAgent()

def update_session() -> None:
    global s

    # make new session
    s = requests.Session()
    # update headers so we can make "human" or "real" requests
    headers = {
        "Accept-Language":  "en-US,en;q=0.5",
        "Cache-Control":    "no-cache",
        "Connection":       "keep-alive",
        "Pragma":           "no-cache",
        "Priority":         "u=0, i",
        "User-Agent":       f"{ua.random}"
    }
    s.headers.update(headers)

# tries a connection to link
def try_request(link: str) -> requests.Response:
    global s

    try:
        r = s.get(link, timeout=5)
        return r
    except (requests.ConnectTimeout, requests.ReadTimeout) as e:
        r = retry_connection(link)
        if not r:
            return None
        else:
            return r

# session_test() using this method if getting timeout or status code 401/403 
# basically just tries to connect to host 3 times
def retry_connection(link: str) -> requests.Response:
    global s

    log("warn", "Got timeout, retrying...")
    sleep_increment = 0
    attemps = 0
    while attemps < 3:
        attemps += 1
        sleep_increment += 2
        try:
            r = s.get(link, timeout=5)
            log("trash", "Got response")
            return r
        except Exception as e:
            if type(e) == requests.ConnectTimeout or type(e) == requests.ReadTimeout:
                log("warn", f"Timed out again, retrying after {sleep_increment} seconds with new session...")
                update_session()
                time.sleep(sleep_increment)
                continue
            else:
                log("fail", f"Unexpected error: {e}")
                return None
    else:
        log("fail", "Host is not accessible")
        return None

# method for testing host connection and updating session if necessary
def session_test() -> int:
    global s

    log("trash", "Testing session...")
    test_host = "http://94.72.18.202:8083/index.htm"
    r = try_request(test_host)

    if r.status_code == 200:
        log("ok", "Session is ok, host is available")
        return 0
    else:
        attempts = 0
        while r.status_code == 401 or r.status_code == 403 and attempts < 10:
            attempts += 1
            log("warn", f"Host returned {r.status_code}, updating session...")
            update_session()
            if not retry_connection(test_host):
                return 2
        else:
            if attempts == 10:
                log("fail", "Failed to update session!")
                return 10
            elif not r.ok:
                log("fail", f"Host returned {r.status_code}")
                return 1
        log("ok", "Updated session")
        return 0

# maybe i will sometime make so message updates in realtime while request or retry is performing
def ping(link: str) -> dict:
    global s
    result = dict()

    r = try_request(link)

    result["status"] = statuses[r.status_code]
    result["code"] = r.status_code
    result["time"] = round(r.elapsed.microseconds / 1000) / 1000    # elapsed time in seconds, %.3f format
    return result

# s_ stands for schedule, r_ for records
def get_source_links(source: Literal["s_group", "s_lecturer", "s_room", "r_group", "r_lecturer"]) -> dict:
    result = dict()
    link = config["links"][f"{source}"]
    
    r = try_request(link)
    if not r:
        return None
    soup = BeautifulSoup(r.content, "html.parser")

    # this is the soup part
    t = soup.find("table", class_="inf")
    rows = t.find_all("tr")
    for tr in rows:
        td = tr.find_all("td", class_="ur")
        if not td:
            continue
        group = td[1].find("a", class_="z0")
        group_name = group.text
        group_link = group.get("href")
        
        result[f"{group_name}"] = f"{config["links"]["base"]}{group_link}"

    return result

def get_lesson_info(td_with_lesson) -> (str, str, str):
    # these z is class names from html
    z1 = ""
    z2 = ""
    z3 = ""
    for z in td_with_lesson:
        if z.get("class")[0] == "z1":
            z1 += z.text + " "
        elif z.get("class")[0] == "z2":
            z2 += z.text + " "
        elif z.get("class")[0] == "z3":
            z3 += z.text + " "
    if not z2:
        z2 = "Кабинет не указан"
    z1 = z1.strip()
    z2 = z2.strip()
    z3 = z3.strip()
    return (z1, z2, z3)

def append_schedule_lesson(
    result: dict, date: str, td_with_lesson, n: str, subgroup: str) -> dict:
    z1, z2, z3 = get_lesson_info(td_with_lesson)
    # subgroup is only for group schedules, None for others
    result["lessons"].append({
        "n":        n,
        "z1":       z1,
        "z2":       z2,
        "z3":       z3,
        "subgroup": subgroup
    })
    return result

# takes soup and returns normalized dictionary
def parse_soup_schedule(soup: BeautifulSoup) -> dict:
    result = dict()

    # get fields from soup
    header = soup.find("h1").text
    update_time = soup.find("div", class_="ref").text.strip()
    days = dict()
    
    # search through a table
    trows = soup.find("table", class_="inf").find_all("tr")
    # start from 4th row, because this html is fucking bullshit and i can't fix it
    for tr in trows[2:]:
        tds = tr.find_all("td")
        # skip if empty row
        if tds[0].get("class")[0] == "hd0":
            continue
        # current row is first lesson in this day, also different lessons for both subgroups, that's why len is 4
        if len(tds) == 4 and len(tds[0].text) > 1:
            current_date, weekday_short = tds[0].get_text(separator=" ").split()
            weekday = t_days[weekday_short]
            
            days[current_date] = dict()
            days[current_date]["weekday"] = weekday
            days[current_date]["lessons"] = list()

            lesson_number = tds[1].text
            # subgroup 1
            td_with_lesson = tds[2].find_all("a")
            if td_with_lesson:
                days[current_date] = append_schedule_lesson(days[current_date], current_date, td_with_lesson, lesson_number, "1")
            # subgroup 2
            td_with_lesson = tds[3].find_all("a")
            if td_with_lesson:
                days[current_date] = append_schedule_lesson(days[current_date], current_date, td_with_lesson, lesson_number, "2")
        # current row is first lesson in this day
        elif len(tds) == 3 and len(tds[0].text) > 1:
            current_date, weekday_short = tds[0].get_text(separator=" ").split()
            weekday = t_days[weekday_short]
            
            days[current_date] = dict()
            days[current_date]["weekday"] = weekday
            days[current_date]["lessons"] = list()
            
            lesson_number = tds[1].text
            
            td_with_lesson = tds[2].find_all("a")
            if td_with_lesson:
                days[current_date] = append_schedule_lesson(days[current_date], current_date, td_with_lesson, lesson_number, "0")
        # current row has different lessons for both subgroups, that's why len is 3
        elif len(tds) == 3:
            lesson_number = tds[0].text

            # subgroup 1
            td_with_lesson = tds[1].find_all("a")
            if td_with_lesson:
                days[current_date] = append_schedule_lesson(days[current_date], current_date, td_with_lesson, lesson_number, "1")
            # subgroup 2
            td_with_lesson = tds[2].find_all("a")
            if td_with_lesson:
                days[current_date] = append_schedule_lesson(days[current_date], current_date, td_with_lesson, lesson_number, "2")
        
        # current row has only lesson and its number
        elif len(tds) == 2:
            lesson_number = tds[0].text

            td_with_lesson = tds[1].find_all("a")
            if td_with_lesson:
                days[current_date] = append_schedule_lesson(days[current_date], current_date, td_with_lesson, lesson_number, "0")
    
    # fill result dictionary
    result["header"] = header
    result["update_time"] = update_time
    result["days"] = days

    return result

def get_schedule(source_type: Literal["group", "lecturer", "room"], source: str) -> dict:
    result = dict()
    link = links[f"s_{source_type}"][source]

    r = try_request(link)
    if not r:
        return 1
    soup = BeautifulSoup(r.content, "html.parser")
    data = parse_soup_schedule(soup)

    # fill result
    result["head"] = source
    result["update_time"] = data["update_time"]
    result["days"] = dict()
    # add dates to result
    for date, info in dict(data["days"]).items():
        result["days"][date] = dict()
        result["days"][date]["weekday"] = info["weekday"]
        result["days"][date]["lessons"] = list()
    # fill dates
    for date, info in dict(data["days"]).items():
        for lesson in list(data["days"][date]["lessons"]):
            number  = lesson["n"]
            bells   = t_bells_monday if info["weekday"] == "Понедельник" else t_bells_week
            match source_type:
                case "group":
                    name        = lesson["z1"]
                    room        = lesson["z2"]
                    lecturer    = lesson["z3"]
                    subgroup    = lesson["subgroup"]
                    result["days"][date]["lessons"].append({
                        "number":   number,
                        "bells":    bells[number],
                        "name":     name,
                        "room":     room,
                        "lecturer": lecturer,
                        "subgroup": subgroup
                    })
                case "lecturer":
                    group       = lesson["z1"]
                    room        = lesson["z2"]
                    name     = lesson["z3"]
                    result["days"][date]["lessons"].append({
                        "number":   number,
                        "bells":    bells[number],
                        "group":    group,
                        "room":     room,
                        "name":     name
                    })
                case "room":
                    lecturer    = lesson["z1"]
                    group       = lesson["z2"]
                    name        = lesson["z3"]
                    result["days"][date]["lessons"].append({
                        "number":   number,
                        "bells":    bells[number],
                        "lecturer": lecturer,
                        "group":    group,
                        "name":     name
                    })
    return result

# init method
def init_api() -> None:
    global config
    
    with open("config.json", 'r') as f:
        config = json.load(f)
    
    update_session()
    session_test()
    
    with open("links.json", 'w') as f:
        links["s_group"]      = get_source_links("s_group")
        links["s_lecturer"]   = get_source_links("s_lecturer")
        links["s_room"]       = get_source_links("s_room")
        links["r_group"]      = get_source_links("r_group")
        links["r_lecturer"]   = get_source_links("r_lecturer")
        json.dump(links, f, indent=4)

# main
if __name__ == "__main__":
    logger.init_logger("log.log", True)
    init_api()

    print(f"{get_schedule("group", "ИСс24-1")}")