import json
with open("./nsfw_words.json") as f:
    wordlist=json.load(f)

def DoesCintainNSFWWords(inprompt):
    for i in wordlist:
        if " "+i+" " in " "+inprompt.lower()+" " or i==inprompt.lower():
            return True,i
    return False,''

while True:
    try:
        prompt=input(">> ")
        res=DoesCintainNSFWWords(prompt)
        if res[0]:
            print(f"NSFW Detected <{res[1]}>")
        else:
            print("Good to go....")
    except KeyboardInterrupt:
        exit()