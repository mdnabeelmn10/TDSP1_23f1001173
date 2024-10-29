import requests
import csv
import time

GITHUB_TOKEN = "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"  # Replace with your GitHub token
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

def get_users_in_location(location="Shanghai", min_followers=200):
    users = []
    query = f"location:{location}+followers:>{min_followers}"
    page = 1
    per_page = 100

    while True:
        url = f"https://api.github.com/search/users?q={query}&per_page={per_page}&page={page}"
        response = requests.get(url, headers=HEADERS)
        print(f"Fetching page {page} for users in {location}...")

        if response.status_code != 200:
            print("Error fetching data:", response.json())
            break

        data = response.json()
        users.extend(data.get('items', []))

        # Check if we reached the last page
        if len(data.get('items', [])) < per_page:
            break

        page += 1
        time.sleep(2)  # Avoid rate-limiting issues by pausing between requests

    detailed_users = []
    for user in users:
        user_info = get_user_details(user['login'])
        if user_info:  # Only add if user details are fetched successfully
            detailed_users.append(user_info)

    return detailed_users

def get_user_details(username):
    user_url = f"https://api.github.com/users/{username}"
    response = requests.get(user_url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Error fetching details for user {username}: {response.json()}")
        return None

    user_data = response.json()
    return {
        'login': user_data.get('login'),
        'name': user_data.get('name'),
        'company': clean_company_name(user_data.get('company')),
        'location': user_data.get('location'),
        'email': user_data.get('email'),
        'hireable': user_data.get('hireable'),
        'bio': user_data.get('bio'),
        'public_repos': user_data.get('public_repos'),
        'followers': user_data.get('followers'),
        'following': user_data.get('following'),
        'created_at': user_data.get('created_at'),
    }

def clean_company_name(company):
    if company:
        company = company.strip().upper()
        if company.startswith('@'):
            company = company[1:]
    return company



def get_user_repos(username):
    repos_url = f"https://api.github.com/users/{username}/repos"
    all_repos = []
    page = 1
    per_page = 100

    while len(all_repos) < 500:
        response = requests.get(f"{repos_url}?per_page={per_page}&page={page}", headers=HEADERS)
        
        if response.status_code != 200:
            print(f"Failed to fetch repos for {username}: {response.status_code}")
            break

        repos_data = response.json()

        if not repos_data:
            break  # Exit if no repos are returned, meaning no more pages

        all_repos.extend(repos_data)

        # Stop if there are fewer than `per_page` repos in this page (last page)
        if len(repos_data) < per_page:
            break

        page += 1
        time.sleep(1)

    # Limit to the first 500 most recently pushed repos
    repos = []
    for repo in all_repos[:500]:
        repos.append({
            'login': username,
            'full_name': repo['full_name'],
            'created_at': repo['created_at'],
            'stargazers_count': repo['stargazers_count'],
            'watchers_count': repo['watchers_count'],
            'language': repo['language'],
            'has_projects': repo['has_projects'],
            'has_wiki': repo['has_wiki'],
            'license_name': repo['license']['key'] if repo['license'] else None,
        })

    return repos



def save_users_to_csv(users):
    with open('users.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['login', 'name', 'company', 'location', 'email', 'hireable', 'bio', 'public_repos', 'followers', 'following', 'created_at'])
        writer.writeheader()
        writer.writerows(users)

def save_repos_to_csv(repos):
    with open('repositories.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['login', 'full_name', 'created_at', 'stargazers_count', 'watchers_count', 'language', 'has_projects', 'has_wiki', 'license_name'])
        writer.writeheader()
        writer.writerows(repos)


if __name__ == "__main__":
    users = get_users_in_location(location="Shanghai", min_followers=200)  # Replace 'YourLocation' with the desired location
    save_users_to_csv(users)

    all_repos = []
    for user in users:
        repos = get_user_repos(user['login'])
        all_repos.extend(repos)

    save_repos_to_csv(all_repos)
    print("Done")
