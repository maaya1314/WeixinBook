import os

html_head = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>abc</title>
</head>
<body>
"""

html_tail = """
</body>
</html>
"""

path = 'G:\\srq\\txt/'
files = os.listdir(path)
# print(files)
fail = 0
for file in files:
    try:
        if file.endswith('.txt') and '(' not in file:
            f_name = file.split('.')[0]
            with open(path+file, 'r') as f:
                context_list = f.readlines()
            context = ""
            for i in context_list:
                context += ("<p>" + (i + '\n') + "</p>")
            html_all = html_head + context + html_tail

            with open('G:\\srq\\txt2html/{}.html'.format(f_name), "w", encoding='utf-8') as f:
                f.write(html_all)
    except Exception as e:
        # print(e)
        fail += 1
        continue
print(fail)
print("finish!")