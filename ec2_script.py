import threading
import time
import random
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service

URL = "http://new-cc-website-host.s3-website-us-east-1.amazonaws.com"
IMAGE_PATH = "./images/image.jpg"
NUM_MODIFICATIONS = 5
RAMP_UP_MINUTES = 40
USERS_PER_MINUTE = 5

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
service = Service('/usr/bin/chromedriver')

times = []
stop_flag = False


def wait_for_image_id(wait):
    wait.until(lambda d: d.execute_script("return window.image_id !== null"))


def upload_test(user_id):
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 10)
    driver.get(URL)

    mod_buttons = [
        driver.find_element(By.ID, "bwButton"),
        driver.find_element(By.ID, "blurButton"),
        driver.find_element(By.ID, "sharpenButton"),
        driver.find_element(By.ID, "rotateButton"),
        driver.find_element(By.ID, "resizeButton"),
    ]
    revert_button = driver.find_element(By.ID, "revertButton")

    img_input = driver.find_element(By.ID, "imageInput")
    test_image = os.path.abspath(IMAGE_PATH)
    img_input.send_keys(test_image)

    wait_for_image_id(wait)

    start = time.time()
    for i in range(NUM_MODIFICATIONS):
        do_revert = revert_button.is_enabled() and random.choice([True, False, False, False, False, False])

        if do_revert:
            print(f"[User {user_id}] Reverting change")
            revert_button.click()
        else:
            btn = random.choice(mod_buttons)
            if btn.get_attribute("id") == "resizeButton":
                width_input = driver.find_element(By.ID, "width")
                height_input = driver.find_element(By.ID, "height")
                w = random.randint(100, 1000)
                h = random.randint(100, 1000)
                width_input.clear()
                width_input.send_keys(str(w))
                height_input.clear()
                height_input.send_keys(str(h))
                print(f"[User {user_id}] Setting resize to {w}x{h} and applying Resize")
            else:
                print(f"[User {user_id}] Applying modification: {btn.text}")
            btn.click()

        wait.until(lambda d: mod_buttons[0].is_enabled())

    end = time.time()
    duration = end - start
    print(f"[User {user_id}] Time taken for {NUM_MODIFICATIONS} modifications: {duration:.2f} seconds")
    times.append(duration)

    driver.get("about:blank")
    driver.quit()


PHASES = [
    (5, 5),   
    (5, 10),
    (5, 15),
    (5, 15),
    (5, 10),
    (5, 5),
]

threads = []

for phase_idx, (duration, users_per_minute) in enumerate(PHASES, start=1):
    for minute in range(duration):
        print(f"⏱️ Phase {phase_idx}, minute {minute+1}/{duration}: starting {users_per_minute} new users")
        for _ in range(users_per_minute):
            user_id = len(threads) + 1
            t = threading.Thread(target=upload_test, args=(user_id,))
            threads.append(t)
            t.start()
        time.sleep(60)

stop_flag = True

for t in threads:
    t.join()

if times:
    avg_time = sum(times) / len(times)
    print(f"Average time per test: {avg_time:.2f} seconds")
else:
    print("No test times recorded")
