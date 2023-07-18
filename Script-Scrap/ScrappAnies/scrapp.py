import os
import time

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

redirect_tag = {}

def selector_normalisation(selector):
    return selector.replace("[", ":nth-child(").replace("]", ")").replace("%20", " ")

kumpulan_nama = ['#aniesbaswedan', '#anieskeren','#aniespresiden2024', '#aniessandi', '#aniesforpresidenri2024', '#aniesgabisakerja', '#anies2024', '#aniespresidenku']

kumpulan_akun = ['aniesupdate', 'langkah_anies','pejuang_aniesbaswedan', 'aniesbaswedan_ri1', 'aniestoday', 'sahabat.anies2024']

n = len(kumpulan_nama)
n = n - 1
n

n2 = len(kumpulan_akun)
n2 = n2 - 1
n2

def handle_step(driver, steps, index_step, temp_data):
    """
    :param process_id: a str
    :param email: a str
    :param index_step: an int
    :param steps: a list<str>
    :param driver: a WebDriver
    :param temp_data: a dic
    :return int
    """
    returner = temp_data
    step = steps[index_step]
    split = step.split(" ")
    if split[-1].endswith("@redirect") and split[0] != "BACK":
        redirect_tag[split[-1]] = driver.current_url
        split = split[0:-1]

    if split[0] == "LOOP":
        looping_steps = []
        # must BEGIN
        begin_str = steps[index_step + 1]
        # must have END
        end_str = begin_str.replace("BEGIN", "END")
        last_index = index_step
        for i in range(index_step + 2, len(steps)):
            if steps[i] != end_str:
                looping_steps.append(steps[i].replace(" ", "", 4))
                last_index = i
            else:
                break

        temp_data_looping = {split[1]: 0} | temp_data

        start_index = int(split[2])

        if split[3].startswith("length"):
            element_key = selector_normalisation(":".join(split[3].split(":")[1::])).format(**temp_data)
            element = driver.find_elements(By.CSS_SELECTOR, element_key)
            end_index = len(element)
        else:
            end_index = int(split[3])

        if len(split) > 4:
            variable_declare = split[4].split(":")
            if variable_declare[1] == "DIC":
                temp_data_looping[variable_declare[0]] = {}
            elif variable_declare[1] == "ARRAY":
                temp_data_looping[variable_declare[0]] = []

        for i in range(start_index, end_index):
            pass_index = -1
            temp_data_looping[split[1]] = i + 1
            for j in range(len(looping_steps)):
                if j > pass_index:
                    pass_index, temp_data_looping = handle_step(driver=driver, steps=looping_steps, index_step=j, temp_data=temp_data_looping)
        if len(split) > 4:
            variable_declare = split[4].split(":")
            if variable_declare[0] not in returner:
                returner[variable_declare[0]] = temp_data_looping[variable_declare[0]]
            else:
                if variable_declare[1] == "DIC":
                    returner[variable_declare[0]] = returner[variable_declare[0]] | temp_data_looping[
                        variable_declare[0]]
                elif variable_declare[1] == "ARRAY":
                    returner[variable_declare[0]] += temp_data_looping[variable_declare[0]]
            if "TEMP_FILE" in temp_data_looping:
                returner["TEMP_FILE"] = temp_data_looping["TEMP_FILE"]
        return last_index + 1, returner
    elif split[0] == "WHILE":
        looping_steps = []
        # must BEGIN
        begin_str = steps[index_step + 1]
        # must have END
        end_str = begin_str.replace("BEGIN", "END")
        last_index = index_step
        for i in range(index_step + 2, len(steps)):
            if steps[i] != end_str:
                looping_steps.append(steps[i].replace(" ", "", 4))
                last_index = i
            else:
                break

        temp_data_looping = temp_data

        if len(split) > 3:
            variable_declare = split[3].split(":")
            if variable_declare[1] == "DIC":
                temp_data_looping[variable_declare[0]] = {}
            elif variable_declare[1] == "ARRAY":
                temp_data_looping[variable_declare[0]] = []

        cont = True

        while cont:
            if split[1] == "EXISTS":
                try:
                    selector = selector_normalisation(split[2]).format(**temp_data)
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    cont = True
                except NoSuchElementException:
                    cont = False
                    break
            elif split[1] == "EVAL":
                cont = eval(split[2])
                if not cont:
                    break
            pass_index = -1
            for j in range(len(looping_steps)):
                if j > pass_index:
                    pass_index, temp_data_looping = handle_step(driver=driver, steps=looping_steps, index_step=j, temp_data=temp_data_looping)

        if len(split) > 3:
            variable_declare = split[3].split(":")
            if variable_declare[0] not in returner:
                returner[variable_declare[0]] = temp_data_looping[variable_declare[0]]
            else:
                if variable_declare[1] == "DIC":
                    returner[variable_declare[0]] = returner[variable_declare[0]] | temp_data_looping[
                        variable_declare[0]]
                elif variable_declare[1] == "ARRAY":
                    returner[variable_declare[0]] += temp_data_looping[variable_declare[0]]
            if "TEMP_FILE" in temp_data_looping:
                returner["TEMP_FILE"] = temp_data_looping["TEMP_FILE"]

        return last_index + 1, returner
    elif split[0] == "GET":
        driver.get(split[1])
    elif split[0] == "SLEEP":
        time.sleep(int(split[1]))
    elif split[0] == "CLOSE":
        driver.close()
        pass
    elif split[0] == "REFRESH":
        driver.refresh()
    elif split[0] == "CLICK":
        selector = selector_normalisation(split[1]).format(**temp_data)
        element = driver.find_element(By.CSS_SELECTOR, selector)
        element.click()
    elif split[0] == "SET":
        value = split[2].replace("%20", " ")
        temp_split = value.split(":")
        if temp_split[0] == "TEXT":
            if split[-1] == "@IF_EXIST":
                try:
                    selector = selector_normalisation(":".join(temp_split[1::])).format(**temp_data)
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    value = element.text
                except NoSuchElementException:
                    value = "-"
            else:
                selector = selector_normalisation(":".join(temp_split[1::])).format(**temp_data)
                element = driver.find_element(By.CSS_SELECTOR, selector)
                value = element.text
        elif temp_split[0] == "DIC":
            value = {}
        elif temp_split[0] == "ARRAY":
            value = []
        temp_data[split[1]] = value
    elif split[0] == "BACK":
        while redirect_tag[split[1]] != driver.current_url:
            driver.back()
    elif split[0] == "PRINT":
        print(split[1].format(**temp_data))
    elif split[0] == "SET_ARRAY":
        if split[1] not in temp_data:
            temp_data[split[1]] = [temp_data[split[2]]]
        else:
            temp_data[split[1]].append(temp_data[split[2]])
    elif split[0] == "JOIN_ARRAY":
        if split[1] not in temp_data:
            temp_data[split[1]] = temp_data[split[2]]
        else:
            temp_data[split[1]] += temp_data[split[2]]
    elif split[0] == "SET_MAP":
        if split[2] != "-":
            if split[1] not in temp_data:
                temp_data[split[1]] = {temp_data[split[2]]: temp_data[split[3]]}
            else:
                temp_data[split[1]][temp_data[split[2]]] = temp_data[split[3]]
    elif split[0] == "SCROLL_INFINITE":
        last_scroll = 0
        while True:
            last_scroll += 500
            # Scroll down to bottom
            driver.execute_script("window.scrollTo(0, {scroll_offset});".format(scroll_offset=last_scroll))
            # Wait to load page
            time.sleep(0.5)
            # Calculate new scroll height and compare with last scroll height
            offset = driver.execute_script("return document.body.scrollHeight")
            if offset < last_scroll:
                break
    elif split[0] == "SCROLL_INFINITE_UP":
        last_scroll = 0
        while True:
            last_scroll += 500
            # Scroll down to bottom
            driver.execute_script("window.scrollTo(0, -{scroll_offset});".format(scroll_offset=last_scroll))
            # Wait to load page
            time.sleep(0.5)
            # Calculate new scroll height and compare with last scroll height
            offset = driver.execute_script("return document.body.scrollHeight")
            if offset < last_scroll:
                break
    elif split[0] == "CONDITION":
        # must BEGIN
        begin_str = steps[index_step + 1]
        # must have END
        end_str = begin_str.replace("@IF", "@ENDIF")
        condition = " ".join(split[1::]).format(**returner)
        skip_index = -1
        for i in range(index_step + 2, len(steps)):
            if steps[i] == end_str:
                skip_index = i
        if not eval(condition):
            return skip_index, returner

    elif split[0] == "TO_EXCEL":
        data = temp_data[split[2]]
        df = pd.DataFrame.from_dict(data)
        sheet_name = "sheet1"
        mode = "a"
        for s in split[3::]:
            if s.startswith("@mode"):
                mode = s.split(":")[1].replace("%20", " ")
            elif s.startswith("@sheet"):
                sheet_name = s.split(":")[1].replace("%20", " ")
        fpath = split[1].replace("%20", " ")
        if os.path.exists(fpath) and mode == "a":
            x = pd.read_excel(fpath)
        else:
            x = pd.DataFrame()
        df_new = pd.concat([df, x])
        df_new.to_excel(fpath, index=False, sheet_name=sheet_name)
        file_name = split[1].replace("%20", " ")
        file_names = [i.strip() for i in temp_data['TEMP_FILE'].split(",") if i != '']
        if file_name not in file_names:
            file_names.append(file_name)
        file_name = ",".join(file_names)
        temp_data["TEMP_FILE"] = file_name

    elif split[0] == "INPUT2":
        selector = selector_normalisation(split[1]).format(**temp_data)
        element = driver.find_element(By.CSS_SELECTOR, selector)
        element.send_keys(kumpulan_nama[n])
        
    elif split[0] == "INPUT3":
        selector = selector_normalisation(split[1]).format(**temp_data)
        element = driver.find_element(By.CSS_SELECTOR, selector)
        element.send_keys(kumpulan_akun[n2])
        
    elif split[0] == "INPUT":
        selector = selector_normalisation(split[1]).format(**temp_data)
        element = driver.find_element(By.CSS_SELECTOR, selector)
        element.send_keys(split[2].replace("%20", " "))
    return index_step, returner

def start_scrap(file_scrap):
    driver = None
    try:
        f = open(file_scrap, "r")
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--window-size=1920,1080')
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
        actions = []
        for action in f:
            temp_action = action[0:-1].split('"')
            for i in range(len(temp_action)):
                if i % 2 != 0:
                    temp_action[i] = temp_action[i].replace(" ", "%20")
            actions.append("".join(temp_action))
        
        pass_index = -1
        temp_data = {"TEMP_FILE": ""}
        for i in range(len(actions)):
            if i > pass_index:
                pass_index, temp_data = handle_step(driver=driver, steps=actions, index_step=i, temp_data=temp_data)
    except Exception as e:
        if driver is not None:
            driver.close()
        print(e)

while True:
    if n >= 0:
        start_scrap("steps_instagram.scr")
        n = n - 1
    else:
        break

while True:
    if n2 >= 0:
        start_scrap("steps_akun.scr")
        n2 = n2 - 1
    else:
        break
