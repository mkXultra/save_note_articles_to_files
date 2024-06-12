import requests
import json
import pandas as pd
import time
from bs4 import BeautifulSoup
import sys

def get_all_notes(username: str, max_page: int, wait_time: int = 1.0):
    all_dfs = []
    for num_page in range(1, max_page + 1):
        time.sleep(wait_time)
        res = requests.get(f'https://note.com/api/v2/creators/{username}/contents?kind=note&page={num_page}')
        if res.status_code != 200:
            break
        data_json = json.loads(res.text)
        contents = data_json['data']['contents']
        if contents:
            for content in contents:
                # get article
                time.sleep(wait_time)
                res = requests.get(f'https://note.com/api/v3/notes/{content["key"]}')
                print(res)
                data_json = json.loads(res.text)
                article = data_json['data']
                # Clean HTML tags from the body using BeautifulSoup
                soup = BeautifulSoup(article['body'], 'html.parser')
                cleaned_text = soup.get_text()
                # Normalize whitespace and format paragraphs
                formatted_text = '\n\n'.join([paragraph.strip() for paragraph in cleaned_text.split('\n') if paragraph.strip()])
                # Add implementation to split sentences by period
                sentences = formatted_text.split('。')
                formatted_text = '。\n'.join([sentence.strip() for sentence in sentences if sentence.strip()]) + '。'
                article['body'] = formatted_text
                article_df = pd.DataFrame([article])
                all_dfs.append(article_df)
        else:
            break
    return all_dfs

# noteboooklmは各ソースは最大500,000語まで含めることができます。
def save_articles_to_files(dfs, username, word_limit=500000):
    current_text = ""
    file_count = 1
    word_count = 0
    FILE_NAME_TEMPLATE = f"{username}_articles_part_{{}}.txt"  # 定数化されたファイル名テンプレートにusernameをprefixとして追加

    for df in dfs:
        for index, row in df.iterrows():
            article_text = "-------------------------"
            article_text += f"\ntitle: [{row['name']}]\n"
            article_text += row['body']
            article_words = article_text.split()
            article_word_count = len(article_words)

            if word_count + article_word_count > word_limit:
                with open(FILE_NAME_TEMPLATE.format(file_count), "w", encoding="utf-8") as file:
                    file.write(current_text)
                file_count += 1
                current_text = article_text
                word_count = article_word_count
            else:
                current_text += "\n\n" + article_text
                word_count += article_word_count

    # Save any remaining text
    if current_text:
        with open(FILE_NAME_TEMPLATE.format(file_count), "w", encoding="utf-8") as file:
            file.write(current_text)

def print_help():
    print("Usage: python main.py <target_note_username>")
    print("Example: python main.py xxx")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print_help()
        sys.exit(1)

    target = sys.argv[1]
    dfs = get_all_notes(target, 100)
    save_articles_to_files(dfs, target)
