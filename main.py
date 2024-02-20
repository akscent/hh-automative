import config.settings as settings
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import os
import time
import json
from enum import Enum

os.system("cls")


class Status(Enum):
    SUCCESS = 0
    FAILURE = 1


def read_text_file(relative_path, file_name, encoding="utf-8"):
    file_path = os.path.join(relative_path, file_name)
    with open(file_path, "r", encoding=encoding) as f:
        return f.read()


MESSAGE = read_text_file("resources", "cover-letter-ru.txt", encoding="utf-8")
ANSWER = read_text_file("resources", "links-list.txt", encoding="utf-8")
USER_AGENT = settings.USER_AGENT
COOKIES_PATH = settings.COOKIES_PATH
LOCAL_STORAGE_PATH = settings.LOCAL_STORAGE_PATH
USER_AGENT = settings.USER_AGENT
USERNAME = settings.USERNAME
PASSWORD = settings.PASSWORD
LOGIN_PAGE = settings.LOGIN_PAGE
JOB_SEARCH_QUERY = settings.JOB_SEARCH_QUERY
EXCLUDE = settings.EXCLUDE
REGION = settings.REGION
SEARCH_LINK = settings.SEARCH_LINK
MIN_SALARY = settings.MIN_SALARY
ONLY_WITH_SALARY = settings.ONLY_WITH_SALARY
ADVANCED_SEARCH_URL_QUERY = getattr(settings, "ADVANCED_SEARCH_URL_QUERY", "")

# options = webdriver.EdgeOptions()
options = webdriver.ChromeOptions()
options.use_chromium = True
options.add_argument("start-maximized")
options.page_load_strategy = "eager"
options.add_argument(f"user-agent={USER_AGENT}")
options.add_experimental_option("detach", True)

s = 10
counter = 0

# driver = webdriver.Edge(options=options)
driver = webdriver.Chrome(options=options)
action = ActionChains(driver)
wait = WebDriverWait(driver, s)


def custom_wait(driver, timeout, condition_type, locator_tuple):
    wait = WebDriverWait(driver, timeout)
    return wait.until(condition_type(locator_tuple))


def eternal_wait(driver, timeout, condition_type, locator_tuple):
    while True:
        try:
            element = WebDriverWait(driver, timeout).until(
                condition_type(locator_tuple)
            )
            return element
        except:
            print(
                f"\n\nWaiting for the element(s) {locator_tuple} to become {condition_type}…"
            )
            time.sleep(0.5)
            continue


def load_data_from_json(path):
    return json.load(open(path, "r"))


def save_data_to_json(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(data, open(path, "w"))


def add_cookies(cookies):
    [driver.add_cookie(cookie) for cookie in cookies]


def add_local_storage(local_storage):
    [
        driver.execute_script(
            f"window.localStorage.setItem({json.dumps(k)}, {json.dumps(v)});"
        )
        for k, v in local_storage.items()
    ]


def get_first_folder(
    path,
):
    return os.path.normpath(path).split(os.sep)[0]


def delete_folder(folder_path):
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            (
                delete_folder(file_path)
                if os.path.isdir(file_path)
                else os.remove(file_path)
            )
        os.rmdir(folder_path)


def success():
    try:
        custom_wait(
            driver,
            s,
            EC.presence_of_element_located,
            (By.XPATH, '//a[@data-qa="mainmenu_myResumes"]'),
        )
        return True
    except:
        return False


def navigate_and_check(probe_page):
    driver.get(probe_page)
    time.sleep(5)
    if success():
        save_data_to_json(driver.get_cookies(), COOKIES_PATH)
        save_data_to_json(
            {
                key: driver.execute_script(
                    f"return window.localStorage.getItem('{key}');"
                )
                for key in driver.execute_script(
                    "return Object.keys(window.localStorage);"
                )
            },
            LOCAL_STORAGE_PATH,
        )
        return True
    else:
        return False


def login():
    driver.get(LOGIN_PAGE)

    show_more_button = eternal_wait(
        driver,
        s,
        EC.element_to_be_clickable,
        (By.XPATH, '//button[@data-qa="expand-login-by-password"]'),
    )
    action.click(show_more_button).perform()

    login_field = eternal_wait(
        driver,
        s,
        EC.element_to_be_clickable,
        (By.XPATH, '//input[@data-qa="login-input-username"]'),
    )
    password_field = eternal_wait(
        driver, s, EC.element_to_be_clickable, (By.XPATH, '//input[@type="password"]')
    )

    login_field.send_keys(USERNAME)
    password_field.send_keys(PASSWORD)

    login_button = eternal_wait(
        driver,
        s,
        EC.element_to_be_clickable,
        (By.XPATH, "//button[@data-qa='account-login-submit']"),
    )
    click_and_wait(login_button, 5)


def check_cookies_and_login():
    driver.get(LOGIN_PAGE)

    if os.path.exists(COOKIES_PATH) and os.path.exists(LOCAL_STORAGE_PATH):
        add_cookies(load_data_from_json(COOKIES_PATH))
        add_local_storage(load_data_from_json(LOCAL_STORAGE_PATH))

        if navigate_and_check(SEARCH_LINK):
            return
        else:
            delete_folder(get_first_folder(COOKIES_PATH))

    login()
    navigate_and_check(SEARCH_LINK)


def scroll_to_bottom(delay=2):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0,document.body.scrollHeight);")
        time.sleep(delay)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if last_height == new_height:
            break
        last_height = new_height


def click_and_wait(element, delay=1):
    action.move_to_element(element).click().perform()
    time.sleep(delay)


def js_click(driver, element):
    try:
        if element.is_displayed() and element.is_enabled():
            driver.execute_script(
                f"""
                arguments[0].scrollIntoView();
                var event = new MouseEvent('click', {{
                    'view': window,
                    'bubbles': true,
                    'cancelable': true
                }});
                arguments[0].dispatchEvent(event);
            """,
                element,
            )
        else:
            print("Element is not visible or not enabled for clicking.")
    except Exception as e:
        print(f"An error occurred: {e}")


def select_all_countries():
    region_select_button = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, '//button[@data-qa="advanced-search-region-selectFromList"]')
        )
    )
    driver.execute_script("arguments[0].click()", region_select_button)
    # select all countries:
    countries = driver.find_elements(
        By.XPATH, '//input[@name="bloko-tree-selector-default-name-0"]'
    )
    for country in countries:
        driver.execute_script("arguments[0].click()", country)
    # submit selected countries:
    region_submit_button = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, '//button[@data-qa="bloko-tree-selector-popup-submit"]')
        )
    )
    driver.execute_script("arguments[0].click()", region_submit_button)


def international_ok():
    try:
        international = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, '//button[@data-qa="relocation-warning-confirm"]')
            )
        )
        driver.execute_script("arguments[0].click()", international)
    except:
        return
    driver.refresh()


def check_cover_letter_popup(message):
    global counter
    try:
        cover_letter_popup = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    '//textarea[@data-qa="vacancy-response-popup-form-letter-input"]',
                )
            )
        )
        set_value_with_event(cover_letter_popup, message)

        action.click(
            wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//button[@data-qa="vacancy-response-submit-popup"]')
                )
            )
        ).perform()

        popup_cover_letter_submit_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, '//button[@data-qa="vacancy-response-submit-popup"]')
            )
        )
        driver.execute_script("arguments[0].click()", popup_cover_letter_submit_button)
        time.sleep(3)
        try:
            error = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//div[@class="bloko-translate-guard"]')
                )
            )
            if error:
                return Status.SUCCESS
        except:
            pass
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//div[@class="vacancy-actions_responded"]')
            )
        )
        counter += 1
        return Status.SUCCESS
    except:
        return Status.FAILURE


def set_value_with_event(element, value):
    action.move_to_element(element).click().perform()
    driver.execute_script("arguments[0].value = '';", element)
    driver.execute_script(
        """
    var setValue = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
    var element = arguments[0];
    var value = arguments[1];
    
    setValue.call(element, value);
    
    var event = new Event('input', { bubbles: true });
    element.dispatchEvent(event);
    """,
        element,
        value,
    )


def answer_questions():
    global counter
    try:
        ul_containers = driver.find_elements(By.XPATH, '//div[@data-qa="task-body"]/ul')
        for ul in ul_containers:
            input_elements = ul.find_elements(
                By.XPATH, './/input[@type="radio" or @type="checkbox"]'
            )
            if input_elements:
                driver.execute_script(
                    "arguments[0].scrollIntoView(); arguments[0].click();",
                    input_elements[-1],
                )
    except:
        pass
    try:
        test_questions_presence = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//div[@data-qa="task-body"]//textarea')
            )
        )
        if test_questions_presence:
            try:
                questions = driver.find_elements(
                    By.XPATH, '//div[@data-qa="task-body"]//textarea'
                )
                for question in questions:
                    set_value_with_event(question, ANSWER)

                submit_button = wait.until(
                    EC.element_to_be_clickable(
                        (By.XPATH, '//button[@data-qa="vacancy-response-submit-popup"]')
                    )
                )
                driver.execute_script(
                    "arguments[0].removeAttribute('disabled')", submit_button
                )
                action.click(submit_button).perform()
                time.sleep(3)
                try:
                    error = wait.until(
                        EC.presence_of_element_located(
                            (By.XPATH, '//div[@class="bloko-translate-guard"]')
                        )
                    )
                    if error:
                        return Status.SUCCESS
                except:
                    pass
                wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//div[@class="vacancy-actions_responded"]')
                    )
                )
                counter += 1
                return Status.SUCCESS
            except:
                return Status.FAILURE
    except:
        return Status.FAILURE


def fill_in_cover_letter(message):
    global counter
    scroll_to_bottom()
    try:
        cover_letter_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, '//button[@data-qa="vacancy-response-letter-toggle"]')
            )
        )
        driver.execute_script("arguments[0].click()", cover_letter_button)

        cover_letter_text = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    '//form[@action="/applicant/vacancy_response/edit_ajax"]/textarea',
                )
            )
        )
        set_value_with_event(cover_letter_text, message)

        submit_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, '//button[@data-qa="vacancy-response-letter-submit"]')
            )
        )
        driver.execute_script("arguments[0].click()", submit_button)

        # driver.execute_script(
        #     "arguments[0].removeAttribute('disabled')", submit_button
        # )  # remove 'disabled' attribute

        # action.click(submit_button).perform()
        time.sleep(3)
        try:
            error = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//div[@class="bloko-translate-guard"]')
                )
            )
            if error:
                return Status.SUCCESS
        except:
            pass
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//div[@data-qa="vacancy-response-letter-informer"]')
            )
        )
        counter += 1
        return Status.SUCCESS
    except:
        return Status.FAILURE


def click_all_jobs_on_the_page():
    global counter
    scroll_to_bottom()
    eternal_wait(
        driver,
        10,
        EC.presence_of_element_located,
        (By.XPATH, '//div[@data-qa="vacancies-search-header"]'),
    )
    try:
        job_links = custom_wait(
            driver,
            20,
            EC.presence_of_all_elements_located,
            (By.XPATH, '//a[contains(., "Откликнуться")]'),
        )
    except:
        return Status.FAILURE

    for link in job_links:
        a = link.get_attribute("href")

        # for i in range(1): # this line is for debug
        #     a = "https://hh.ru/applicant/vacancy_response?vacancyId=85935747" # this line is for debug

        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])
        driver.get(a)
        time.sleep(3)
        international_ok()
        try:
            company_name = custom_wait(
                driver,
                10,
                EC.presence_of_element_located,
                (By.XPATH, '//a[@data-qa="vacancy-company-name"]'),
            ).text
        except:
            pass
        try:
            vacancy_title = custom_wait(
                driver,
                10,
                EC.presence_of_element_located,
                (By.XPATH, '//h1[@data-qa="vacancy-title"]'),
            ).text
        except:
            pass
        if company_name and vacancy_title:
            customized_message = f"Здравствуйте, уважаемый рекрутер {company_name}!\nПрошу рассмотреть мою кандидатуру на вакансию «{vacancy_title}».\n\n{MESSAGE}"
        elif company_name:
            customized_message = (
                f"Здравствуйте, уважаемый рекрутер {company_name}!\n\n{MESSAGE}"
            )
        elif vacancy_title:
            customized_message = f"Здравствуйте, уважаемый рекрутер!\nПрошу рассмотреть мою кандидатуру на вакансию «{vacancy_title}».\n\n{MESSAGE}"
        else:
            customized_message = MESSAGE

        if fill_in_cover_letter(customized_message) == Status.SUCCESS:
            driver.close()
            time.sleep(1)
            driver.switch_to.window(driver.window_handles[0])
        elif check_cover_letter_popup(customized_message) == Status.SUCCESS:
            driver.close()
            time.sleep(1)
            driver.switch_to.window(driver.window_handles[0])
        else:
            try:
                answer_questions()
                driver.close()
                time.sleep(1)
                driver.switch_to.window(driver.window_handles[0])
            except:
                driver.close()
                time.sleep(1)
                driver.switch_to.window(driver.window_handles[0])
                continue


def clear_region():
    try:
        clear_region_buttons = custom_wait(
            driver,
            10,
            EC.presence_of_all_elements_located,
            (By.XPATH, '//button[@data-qa="bloko-tag__cross"]'),
        )
        for button in clear_region_buttons:
            js_click(driver, button)
    except:
        return


def advanced_search():
    advanced_search_button = eternal_wait(
        driver,
        10,
        EC.element_to_be_clickable,
        (By.XPATH, '//a[@data-qa="advanced-search"]'),
    )

    js_click(driver, advanced_search_button)
    advanced_search_textarea = eternal_wait(
        driver,
        10,
        EC.element_to_be_clickable,
        (By.XPATH, '//input[@data-qa="vacancysearch__keywords-input"]'),
    )
    advanced_search_textarea.send_keys(JOB_SEARCH_QUERY)
    advanced_search_textarea.send_keys(Keys.TAB)

    if REGION == "global":
        clear_region()

    try:
        exclude_these_results = custom_wait(
            driver,
            10,
            EC.element_to_be_clickable,
            (By.XPATH, '//input[@name="excluded_text"]'),
        )
        exclude_these_results.send_keys(EXCLUDE)
    except:
        pass

    try:
        no_agency = custom_wait(
            driver,
            5,
            EC.element_to_be_clickable,
            (
                By.XPATH,
                '//input[@data-qa="advanced-search__label-item-label_not_from_agency"]',
            ),
        )
        js_click(driver, no_agency)
    except:
        pass

    salary = custom_wait(
        driver,
        10,
        EC.element_to_be_clickable,
        (By.XPATH, '//input[@data-qa="advanced-search-salary"]'),
    )
    salary.send_keys(MIN_SALARY)

    if ONLY_WITH_SALARY:
        salary_only_checkbox = custom_wait(
            driver,
            10,
            EC.element_to_be_clickable,
            (By.XPATH, '//input[@name="only_with_salary"]'),
        )
        js_click(driver, salary_only_checkbox)

    quantity = driver.find_element(
        By.XPATH, '//input[@data-qa="advanced-search__items_on_page-item_100"]'
    )
    js_click(driver, quantity)

    advanced_search_submit_button = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, '//button[@data-qa="advanced-search-submit-button"]')
        )
    )
    js_click(driver, advanced_search_submit_button)


def main():
    global counter

    check_cookies_and_login()

    if ADVANCED_SEARCH_URL_QUERY:
        driver.get(ADVANCED_SEARCH_URL_QUERY)
    else:
        advanced_search()

    while counter < 200:
        if click_all_jobs_on_the_page() == Status.FAILURE:
            os.system("cls")
            print(
                "It's either the hh.ru server has become undresponsive or all the links within the current search query have been clicked. \n 1) check if hh.ru is alive and responsive \n 2) check if you have clicked all the links available for the job search query. In that case, change the 'JOB_SEARCH_QUERY = ' value. \n \n Sincerely Yours, \n NAKIGOE.ORG\n"
            )
            driver.close()
            driver.quit()

        driver.switch_to.window(driver.window_handles[0])

        try:
            next_page_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//a[@data-qa="pager-next"]'))
            )
            driver.execute_script("arguments[0].click()", next_page_button)
        except:
            os.system("cls")
            print(
                "It's either the hh.ru server has become undresponsive or all the links within the current search query have been clicked. \n 1) check if hh.ru is alive and responsive \n 2) check if you have clicked all the links available for the job search query. In that case change the 'JOB_SEARCH_QUERY = ' value. \n \n Sincerely Yours, \n NAKIGOE.ORG\n"
            )
            driver.close()
            driver.quit()

    os.system("cls")
    print(
        "Congratulations!\n The script has completed successfully in one go!!! You've sent 200 resumes today, that is currently a limit on HH.RU\n Come again tomorrow! \n \n Sincerely Yours, \n NAKIGOE.ORG\n"
    )
