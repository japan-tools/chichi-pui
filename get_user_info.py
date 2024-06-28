import os
import json
import requests
import traceback
from bs4 import BeautifulSoup

base_url = "https://www.chichi-pui.com"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
}


def get_users():
    response = requests.get(base_url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    alinks = soup.find_all("a", class_="p-image-cards-with-like__item-link")
    users = []
    for alink in alinks:
        url = alink.attrs.get("href")
        if "posts" in url:
            res1 = requests.get(f"{base_url}{url}", headers=headers)
            soup1 = BeautifulSoup(res1.content, "html.parser")
            user_div_container = soup1.find(
                "div", class_="image-posts-detail-user-info__user-image-outer"
            )
            user_link = user_div_container.find("a")
            user_id = user_link.attrs.get("href").split("/")[-2]
            if user_id:
                user_detail_info = soup1.find_all(
                    "span", class_="image-posts-detail-user-info__stats-item-number"
                )
                post_count = user_detail_info[0].text
                follower_count = user_detail_info[2].text
                users.append(
                    {
                        "user_id": user_id,
                        "follower_count": follower_count,
                        "post_count": post_count,
                    }
                )
    return users


def write_users_to_file(file_name, users):
    with open(file_name, "w") as final:
        json.dump(users, final, indent=4)


def file_exists(file_name):
    return os.path.exists(file_name)


def mkdir(path):
    if not file_exists(path):
        os.makedirs(path)


def merge_users_to_file(file_name, users):
    if file_exists(file_name):
        with open(file_name, "r") as file:
            data = json.load(file)
            users = merge_data_to_file(users, data)
            write_users_to_file(file_name, users)
    else:
        write_users_to_file(file_name, users)


def merge_data_to_file(current_data, before_data):
    tmp_obj = {}
    if current_data and before_data:
        concat_data = current_data + before_data
        for data in concat_data:
            tmp_obj[data.get("user_id")] = data.copy()
        merge_datas = [tmp_obj.get(id) for id in tmp_obj]
        return merge_datas
    elif current_data:
        return current_data
    else:
        return before_data


def get_user_total_page(url):
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    paginations = soup.find_all("a", class_="pagination-link")
    if paginations:
        return int(paginations[-1].text)


def get_user_posts(user_id, page):
    url = f"{base_url}/users/{user_id}/?p={page}"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    all_post_link_list = soup.find_all("a", class_="is-relative")
    posts = [base_url + link.attrs.get("href") for link in all_post_link_list]
    return posts


def download_pic(url):
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    post_title = soup.find("h1", class_="c-section-title").text
    post_title = post_title.replace("/", "-")
    imgs = soup.find_all(
        "img", class_="image-posts-detail-thumbnail-carousel__slide-image"
    )
    main_img = soup.find("img", class_="image-posts-detail-main-image__image")
    mkdir(f"./data/images/")
    if imgs:
        idx = 1
        for img in imgs:
            img_src = img.attrs.get("src").split("?")[0]
            response = requests.get(img_src, headers=headers)
            with open(f"./data/images/{post_title}_{idx}.jpeg", "wb") as file:
                file.write(response.content)
            idx += 1

    elif main_img:
        img_src = main_img.attrs.get("src")
        response = requests.get(img_src, headers=headers)
        with open(f"./data/images/{post_title}.jpeg", "wb") as file:
            file.write(response.content)


def handle_datas():
    try:
        users = get_users()
        if not users:
            return
        for user in users:
            posts = []
            user_id = user.get("user_id")
            url = f"{base_url}/users/{user_id}/"
            total_page = get_user_total_page(url)
            for page in range(1, total_page + 1):
                posts.extend(get_user_posts(user_id, page))

            for post in posts:
                download_pic(post)

        mkdir("./data")
        merge_users_to_file("./data/users.json", users)
    except Exception:
        print(traceback.format_exc())


if __name__ == "__main__":
    handle_datas()
