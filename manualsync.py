# Used to manually edit/add news entires

import os
from datetime import datetime
from git import Repo

# Constants
FILE_PATH = r'C:\Users\Ryan\Downloads\DARE Aquatics SDK\dare-website\news.html'
LOCAL_REPO_PATH = r'C:\Users\Ryan\Downloads\DARE Aquatics SDK\dare-website'

# Function to input news items
def input_news_items():
    news_items = []

    while True:
        title = input("Enter the title of the news item (or 'done' to finish): ")
        if title.lower() == 'done':
            break

        while True:
            date = input("Enter the date of the news item (MM-DD-YYYY): ")
            try:
                datetime.strptime(date, '%m-%d-%Y')
                break
            except ValueError:
                print("Invalid date format. Please enter the date in MM-DD-YYYY format.")

        content = input("Enter the content of the news item: ")

        news_items.append({
            'title': title,
            'date': date,
            'content': content
        })

    return news_items

# Generate HTML for news items
def generate_html(news_items):
    news_html = ''

    for item in news_items:
        formatted_date = datetime.strptime(item['date'], '%m-%d-%Y').strftime('%B %d, %Y')

        news_html += f'''
        <div class="news-item">
            <h2 class="news-title">{item["title"]}</h2>
            <p class="news-date">Published on {formatted_date}</p>
            <p class="news-content">{item["content"]}</p>
        </div>
        '''

    return news_html

# Update the HTML file with new news items
def update_html_file(news_html):
    with open(FILE_PATH, 'r', encoding='utf-8') as file:
        content = file.read()

    # Define markers for the section to be replaced
    start_marker = '<!-- START UNDER HERE -->'
    end_marker = '<!-- Add more news items here -->'
    start_index = content.find(start_marker) + len(start_marker)
    end_index = content.find(end_marker)

    # Update the content between markers
    updated_content = content[:start_index] + '\n' + news_html + '\n' + content[end_index:]

    with open(FILE_PATH, 'w', encoding='utf-8') as file:
        file.write(updated_content)


# Commit and push the changes to GitHub
def push_to_github():
    repo = Repo(LOCAL_REPO_PATH)
    repo.git.add(FILE_PATH)
    repo.index.commit('automated:: update news.html')
    origin = repo.remote(name='origin')
    origin.push()

# Main function to run the update process
def main():
    print("Inputting news items...")
    news_items = input_news_items()

    print("Generating HTML...")
    news_html = generate_html(news_items)

    print("Updating HTML file...")
    update_html_file(news_html)

    print("Pushing changes to GitHub...")
    push_to_github()

    print("Done!")

if __name__ == "__main__":
    main()
