import os
import shutil
import re
import sys
import json

def find_markdown_links(text):
    md_link_pattern = r'\[([^\]]+)\]\(([^#)]+)([^)]*)\)'
    matches = re.findall(md_link_pattern, text)
    
    return matches

def replace_word_in_file(file_path, target, replacement):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()


    links = find_markdown_links(content)

    content_replaced = ''
    for _, url, _ in links:
        if url == target:
            content_replaced = content.replace(url, replacement)

    if content_replaced != '' and content != content_replaced:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content_replaced)
        print(f"Replaced in file: {file_path}")

def replace_word_in_repo(repo_path, target, replacement, file_extensions=None):
    for root, dirs, files in os.walk(repo_path):
        
        for file_name in files:
            if file_extensions:
                if not any(file_name.endswith(ext) for ext in file_extensions):
                    continue
            
            if root.find("node_modules") != -1:
                continue

            file_path = os.path.join(root, file_name)
            
            replace_word_in_file(file_path, target, replacement)

def get_redirect(path):
    res = os.path.splitext(path)[0]
    spl = res.split("/")

    res = res[len(spl[0])+1:]
    res = res[len(spl[1]):]

    return res

def redirect(from_r, to_r, json_file):
    obj = {
        "from": from_r,
        "to": to_r
    }

    data = []
    with open(json_file, 'r') as file:
        data = json.load(file)
        
    data.append(obj)

    with open(json_file, 'w') as file:
        json.dump(obj, file, indent=4)

    
if __name__ == "__main__":
    s = sys.argv[1]
    source = get_redirect(s)
    print(source)
    d = sys.argv[2]
    destination = get_redirect(d)
    print(destination)

    path_r = destination.split("/")[1]
    json_file = f"./redirects/{path_r}.json"

    repo_path = os.getcwd()
    file_extensions = ['.mdx', '.md']
    
    try:
        dd = os.path.dirname(d)
        print(dd)
        if not os.path.exists(dd):
            os.makedirs(dd)
        shutil.copy(s, d)
        print("File moved successfully!")
    except FileNotFoundError:
        print(f"Error: The file {s} does not exist.")
    except PermissionError:
        print(f"Error: Permission denied while trying to move {d}.")
    except Exception as e:
        print(f"An error occurred: {e}")

    replace_word_in_repo(repo_path, "", "", file_extensions)
    redirect(source, destination, json_file)
    
