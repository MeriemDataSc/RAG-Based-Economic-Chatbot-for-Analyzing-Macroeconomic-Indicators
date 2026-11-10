import re
words=[{'text': '11', 'x0': 18.7883, 'x1': 35.407466400000004, 'top': 39.32135400000004, 'doctop': 39.32135400000004, 'bottom': 68.395354, 'upright': True, 'height': 29.073999999999955, 'width': 16.619166400000005, 'direction': 'ltr'},
       {'text': 'International', 'x0': 72.5669, 'x1': 135.45770000000002, 'top': 46.442999999999984, 'doctop': 46.442999999999984, 'bottom': 58.442999999999984, 'upright': True, 'height': 12.0, 'width': 62.89080000000001, 'direction': 'ltr'},
       {'text': 'merchandise', 'x0': 138.7937, 'x1': 205.03370000000007, 'top': 46.442999999999984, 'doctop': 46.442999999999984, 'bottom': 58.442999999999984, 'upright': True, 'height': 12.0, 'width': 66.24000000000007, 'direction': 'ltr'},
       {'text': 'trade', 'x0': 208.36970000000005, 'x1': 235.04570000000004, 'top': 46.442999999999984, 'doctop': 46.442999999999984, 'bottom': 58.442999999999984, 'upright': True, 'height': 12.0, 'width': 26.675999999999988, 'direction': 'ltr'},
       {'text': 'Table', 'x0': 56.6929, 'x1': 80.6044, 'top': 82.40899999999999, 'doctop': 82.40899999999999, 'bottom': 91.90899999999999, 'upright': True, 'height': 9.5, 'width': 23.911499999999997, 'direction': 'ltr'}, 
       {'text': '1.1.1', 'x0': 83.2454, 'x1': 104.37340000000002, 'top': 82.40899999999999, 'doctop': 82.40899999999999, 'bottom': 91.90899999999999, 'upright': True, 'height': 9.5, 'width': 21.128000000000014, 'direction': 'ltr'}]


# titles=[]
# for i, word in enumerate(words):   # word est le dict (text+ coordonnes)

#     if "Table" in word["text"]:
#         line_top = word["top"]
#         line_words = [w["text"] for w in words if abs(w["top"] - line_top) < 1]
#         title_text = ' '.join(line_words)
#         titles.append({"text": title_text,"top": line_top})
                    
#         print(titles)

for row in words:
    row["title"]="meriem"
print(words)


table_top = min(w["x0"] for w in words)
print(table_top)