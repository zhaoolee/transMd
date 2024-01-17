import os
import json
from openai import OpenAI
from hashlib import sha1
import time
import urllib.parse

# Read the API key from an environment variable

input_markdown_file_dir = "./input_markdown_file_dir"
output_markdown_file_dir = "./output_markdown_file_dir"



def translate_markdown(markdown_content):
    # Read the Markdown file content
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    client = OpenAI(api_key=OPENAI_API_KEY)
    input_lang = "Simplified Chinese"
    output_lang = "English"
    # Initialize the translation using the OpenAI API
    stream = client.chat.completions.create(
        model="gpt-4-1106-preview",
        stream=True,
        messages=[
            {
                "role": "user",
                "content": f"""
                I am translating the documentation for {input_lang}.
                Translate the Markdown content I'll paste later into {output_lang}.
                You must strictly follow the rules below.
                - Never change the Markdown markup structure. Don't add or remove links. Do not change any URL.
                - Never change the contents of code blocks even if they appear to have a bug.
                - Always preserve the original line breaks. Do not add or remove blank lines.
                - Never touch the permalink such as `{'{'}/*examples*/{'}'}` at the end of each heading.
                - Never touch HTML-like tags such as `<Notes>`.
                the document is:
                {markdown_content}
                """
            }
        ]
    )

    translated_content = ""
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="")
            translated_content = translated_content + chunk.choices[0].delta.content

    return translated_content


def get_markdown_content(file_path):
    # Read the Markdown file content
    markdown_content = ""
    with open(file_path, "r", encoding="utf-8") as file:
        markdown_content = file.read()
    print("Read markdown content from:", file_path, markdown_content)
    return markdown_content


def write_markdown_content(output_path, translated_content):
    with open(output_path, "w", encoding="utf-8") as output_file:
        output_file.write(translated_content)
    print("Translation complete. Output written to:", output_path)


def translate_markdown_file(markdown_file_path):
    output_filename = os.path.basename(markdown_file_path)
    output_path = os.path.join(output_markdown_file_dir, output_filename)
    markdown_content = get_markdown_content(markdown_file_path)
    translated_content = translate_markdown(markdown_content)
    write_markdown_content(output_path, translated_content)


def write_dic_info_to_file(dic_info, file):
    dic_info_str = json.dumps(dic_info)
    file = open(file, "w")
    file.write(dic_info_str)
    file.close()
    return True


def get_md_list(dir_path):
    md_list = []
    dirs = os.listdir(dir_path)
    for i in dirs:
        if os.path.splitext(i)[1] == ".md":
            md_list.append(os.path.join(dir_path, i))
    print(md_list)
    return md_list


def get_sha1(filename):
    sha1_obj = sha1()
    with open(filename, "rb") as f:
        sha1_obj.update(f.read())
    result = sha1_obj.hexdigest()
    print(result)
    return result


def read_dic_from_file(file):
    file_byte = open(file, "r")
    file_info = file_byte.read()
    dic = json.loads(file_info)
    file_byte.close()
    return dic


# 获取md_sha1_dic


def get_md_sha1_dic(file):
    result = {}
    if os.path.exists(file) == True:
        result = read_dic_from_file(file)
    else:
        write_dic_info_to_file({}, file)
    return result


def update_md_sha1_dic(hash_file, md_file):
    md_sha1_dic = read_dic_from_file(hash_file)
    key = os.path.basename(md_file).split(".")[0]
    value = get_sha1(md_file)

    md_sha1_dic[key] = {
        "hash_value": value,
        "file_name": key,
        "encode_file_name": urllib.parse.quote(key, safe="").lower(),
        "update_time": time.strftime("%Y-%m-%d-%H-%M-%S"),
    }

    write_dic_info_to_file(md_sha1_dic, hash_file)


def rebuild_md_sha1_dic(file, md_dir):
    md_sha1_dic = {}

    md_list = get_md_list(md_dir)

    for md in md_list:
        key = os.path.basename(md).split(".")[0]
        value = get_sha1(md)
        md_sha1_dic[key] = {
            "hash_value": value,
            "file_name": key,
            "encode_file_name": urllib.parse.quote(key, safe="").lower(),
        }

    write_dic_info_to_file(md_sha1_dic, file)


def main():
    # if out_dir no exist, create it
    if os.path.exists(output_markdown_file_dir) == False:
        os.mkdir(output_markdown_file_dir)

    md_sha1_dic = get_md_sha1_dic(os.path.join(os.getcwd(), ".md_sha1"))
    md_list = get_md_list(input_markdown_file_dir)

    for index, md in enumerate(md_list):
        print(
            "==current progress==", str(index) + "/" + str(len(md_list)), "start==", md
        )
        sha1_key = os.path.basename(md).split(".")[0]
        sha1_value = get_sha1(md)
        if (
            (sha1_key in md_sha1_dic.keys())
            and ("hash_value" in md_sha1_dic[sha1_key])
            and (sha1_value == md_sha1_dic[sha1_key]["hash_value"])
        ):
            print("==Not Need Run" + "md")
        else:
            # 读取md文件信息
            translate_markdown_file(md)
            update_md_sha1_dic(os.path.join(os.getcwd(), ".md_sha1"), md)
            print("==Finish" + md)


if __name__ == "__main__":
    main()
