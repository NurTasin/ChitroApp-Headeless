"""
    Chitro.AI server
    The Chitro AI main server code
    Author: Nur Mahmud Ul Alam Tasin [bigT Devs]
    The perpose of this file is to process the prompts and serve the generated images
    to the users. In a sense this is the full stack web app

    Copyright (C) 2023 bigT Devs
"""



from flask import Flask,render_template,request,Response,jsonify,redirect,url_for,send_from_directory
from flask_cors import CORS,cross_origin
import json
import openai
from uuid import uuid4
import os
import threading
from deep_translator import GoogleTranslator
import datetime
import sys
import logging
import traceback
import mistune

#Controling The Behaviour

COOKIE_MAX_AGE=30*24*60*60
CHITRO_ID="__chitroID"
CHITRO_COUNT="__chitroCount"
CHITRO_ADMIN="__chitroAdmin"
MAX_GENERATION_PER_USER=20
LOG_FILE="./server_log.md"


# Statistics
GeneratedImageCount=0
RejectedImageCount=0
ServedImageCount=0
ExceptionCount=0
NSFWCount=0


def writeToLog(logFile:str,msg:str):
    with open(LOG_FILE,'a') as f:
        f.write(f"## {str(datetime.datetime.now())}\n")
        for i in msg.splitlines():
            f.write(f"{i}\n")
        f.write("\n")



translator=GoogleTranslator(source="auto",target="en")
openai.api_key=os.getenv("OPENAI_API_KEY")

#initializing the app and CORS
app=Flask(__name__,static_url_path='', 
            static_folder='static',
            template_folder='templates')
app_cors=CORS(app)

#disabling logging for werkzeug server
logging.getLogger('werkzeug').setLevel(logging.ERROR)

#Loading the NSWF words for NSFW Filtering.
with open('nsfw_words.json') as f:
    NSFW_Words=json.load(f)

#code to handle the NSFW words Filter:
def DoesContainNSFWWords(inprompt):
    for i in NSFW_Words:
        if " "+i+" " in " "+inprompt.lower()+" " or i==inprompt.lower():
            return True,i
    return False,''

#code to handle the imageGenerationProcess

CookieImageDict={}

def AddImageUrlToStack(chitroID:str,url:str):
    global CookieImageDict
    CookieImageDict[chitroID]=url

def GetImageUrlFromStack(chitroID:str):
    global CookieImageDict
    url=CookieImageDict[chitroID]
    del CookieImageDict[chitroID]
    return url

def CheckImageFromStack(chitroID:str):
    global CookieImageDict
    return chitroID in CookieImageDict

def generate_image_thread(prompt:str,chitroID:str,ip:str):
    translated_prompt=translator.translate(prompt)
    result=DoesContainNSFWWords(translated_prompt)
    if result[0]:
        global NSFWCount
        NSFWCount+=1
        print(f"## NSFW Detected on User {chitroID} <{ip}> [{prompt},{translated_prompt},{result[1]}] ##",file=sys.
    stderr)
        writeToLog(LOG_FILE,f"""### NSFW Prompt Detected
```
Chitro ID:     {chitroID}
IP Address:    {ip}
Prompt:        {prompt}
Mapped Prompt: {translated_prompt}
NSFW Word:     {result[1]}
```
""")
        image_url = {
            "NSFW":True,
            "generated":False,
            # "image_url":"/NSFWDetectedWarning"
        }
    else:
        print(f"{prompt} -> {translated_prompt}")
        # Generate the image
        try:
            response = openai.Image.create(prompt=translated_prompt,
                                        n=1,
                                        size="1024x1024")

            # Access the generated image
            image_url = {
                "NSFW":False,
                "generated":True,
                "image_url":json.loads(str(response))["data"][0]["url"]
            }
            print(image_url)
            global GeneratedImageCount
            GeneratedImageCount+=1

        except Exception as e:
            global ExceptionCount
            ExceptionCount+=1
            image_url={
                "NSFW":False,
                "generated":False,
                "image_url":"/WarningImage"
            }
            print(e,file=sys.stderr)
            writeToLog(LOG_FILE,msg=f"""### Image Generation Error
```
Exception:     {e.__class__.__name__}
Message:       {str(e)}
Prompt:        {prompt}
Mapped Prompt: {translated_prompt}
Chitro ID:     {chitroID}
IP Address:    {ip}
Traceback: 
{''.join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__))}
```
""")
    
    AddImageUrlToStack(chitroID,image_url)


# Serving The Homepage
@app.route("/",methods=["GET"])
@cross_origin()
def HomePage():
    print(CookieImageDict)
    if CHITRO_ID in request.cookies and CHITRO_COUNT in request.cookies:
        print(f"Requests Recieved From {request.cookies.get(CHITRO_ID)}")
        return render_template("index.html")
    else:
        resp=Response(render_template("index.html"))
        resp.set_cookie(CHITRO_ID,str(uuid4()),max_age=COOKIE_MAX_AGE)
        resp.set_cookie(CHITRO_COUNT,str(0),max_age=COOKIE_MAX_AGE)
        return resp

@app.route("/index.html",methods=["GET"])
@cross_origin()
def HomePageAlias1():
    return redirect(url_for("HomePage"))

@app.route("/home",methods=["GET"])
@cross_origin()
def HomePageAlias2():
    return redirect(url_for("HomePage"))


@app.route("/about-us",methods=["GET"])
@cross_origin()
def AboutUsPage():
    return render_template("about-us.html")

@app.route("/about-us.html",methods=["GET"])
@cross_origin()
def AboutUsPageAlias():
    return redirect(url_for("AboutUsPage"))

@app.route("/faq",methods=["GET"])
@cross_origin()
def FAQ():
    return render_template("faq.html")

@app.route("/faq.html",methods=["GET"])
@cross_origin()
def RAQAlias1():
    return redirect(url_for("FAQ"))

@app.route("/WarningImage",methods=["GET"])
@cross_origin()
def ServeWarningImage():
    return send_from_directory('static', "assets/img/error.gif")

@app.route("/generate",methods=["POST"])
@cross_origin()
def AddPromptToQueue():
    if (CHITRO_ID in request.cookies) and (CHITRO_COUNT in request.cookies):
        #Handling Chitro Admin
        if CHITRO_ADMIN in request.cookies:
            if request.cookies.get(CHITRO_ADMIN)=="h3h3b0y5":
                prompt=request.get_json()["prompt"]
                chitroID=request.cookies.get(CHITRO_ID)
                ip="N/A"
                if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
                    ip=request.environ['REMOTE_ADDR'] + " (ADMIN)"
                else:
                    ip=request.environ['HTTP_X_FORWARDED_FOR']+" (ADMIN)"
                thread = threading.Thread(target=generate_image_thread, args=(prompt,chitroID,ip))
                thread.start()
                resp = Response("Started Generation Process",200)
                return resp
            else:
                return Response("Fake Admin").delete_cookie(CHITRO_ADMIN)
        #Handling Normal User
        elif int(request.cookies.get(CHITRO_COUNT))<MAX_GENERATION_PER_USER:
            prompt=request.get_json()["prompt"]
            chitroID=request.cookies.get(CHITRO_ID)
            ip="N/A"
            if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
                ip=request.environ['REMOTE_ADDR']
            else:
                ip=request.environ['HTTP_X_FORWARDED_FOR']
            thread = threading.Thread(target=generate_image_thread, args=(prompt,chitroID,ip))
            thread.start()
            resp = Response("Started Generation Process",200)
            resp.set_cookie(CHITRO_COUNT,str(int(request.cookies.get(CHITRO_COUNT))+1),max_age=COOKIE_MAX_AGE)
            return resp
        else:
            global RejectedImageCount
            RejectedImageCount+=1
            return jsonify({"msg":"You have reached the image generation limit. Try again next month"}),403
    else:
        print(request.cookies)
        return redirect(url_for("HomePage")),302

@app.route("/getGeneratedResults",methods=["GET"])
@cross_origin()
def SendGeneratedResults():
    if CHITRO_ID in request.cookies:
        chitroID=request.cookies.get(CHITRO_ID)
        result=CheckImageFromStack(chitroID)
        if result:
            image_obj=GetImageUrlFromStack(chitroID)
            if image_obj["NSFW"]:
                return jsonify({"msg":"We have detected one or more NSFW words in your prompt. If this continues, your Chitro ID will be banned."}),400
            if image_obj["generated"]:
                global ServedImageCount
                ServedImageCount+=1
                return jsonify({"image_url":image_obj["image_url"]}),200
            else:
                resp=Response(json.dumps({"image_url":image_obj["image_url"]}),200)
                if int(request.cookies.get(CHITRO_COUNT))>0:
                    resp.set_cookie(CHITRO_COUNT,str(int(request.cookies.get(CHITRO_COUNT))-1),max_age=COOKIE_MAX_AGE)
                else:
                    resp.set_cookie(CHITRO_COUNT,str(request.cookies.get(CHITRO_COUNT)),max_age=COOKIE_MAX_AGE)
                return resp
        else:
            return jsonify({"finished":False}),404
    else:
        return jsonify({"msg":"Bad Request"}),400

@app.route("/getLogs",methods=["GET"])
@cross_origin()
def serverLogs():
    if CHITRO_ADMIN in request.cookies:
        with open(LOG_FILE) as f:
            return f"""
            <head> <meta http-equiv="refresh" content="5"> <title> Chitro Logs</title> </head>
            <body>{mistune.html(f.read())}</body>
            """
    else:
        return "<h1>Access Denied</h1>",403
@app.route("/adminLogin",methods=["GET","POST"])
@cross_origin()
def adminLogin():
    if request.method=="GET":
        if CHITRO_ADMIN in request.cookies:
            global GeneratedImageCount
            global ServedImageCount
            global RejectedImageCount
            global ExceptionCount
            global NSFWCount

            return f"""
<html>
<head> <meta http-equiv="refresh" content="5"> <title> Chitro Admin</title> </head>
<body>
<h1> Chitro Admin Panel</h1>
<br><br>
Generated Images : {GeneratedImageCount} <br>
Served Images :    {ServedImageCount} <br>
Rejected Images:   {RejectedImageCount} <br>
Server Error:      {ExceptionCount} <br>
NSFW Prompt Count: {NSFWCount} <br>
In-cache Image:    {GeneratedImageCount-ServedImageCount} <br>
<br>
<br>
<br>
<a href="/getLogs">Check Logs</a>
<br>
<a href="/clearCachedImages">Clear In-Cache Images</a>
<br>
<a href="/clearLog">Clear Log</a>
</body>
</html>
"""
        else:
            return """
<form action="/adminLogin" method="POST">
<input type="text" name="loginCode" placeholder="Login Code">
<br>
<input type="submit" value="Login">
</form>
"""

    elif request.method=="POST":
        if "loginCode" in request.form:
            if str(request.form.get("loginCode")) == os.getenv("CHITRO_LOGIN_CODE"):
                resp=redirect("/adminLogin")
                resp.set_cookie(CHITRO_ADMIN,"h3h3b0y5",max_age=2*60*60)
                return resp
            else:
                return "Wrong Admin Code",403
        else:
            return "Bad Request",400

@app.route("/clearCachedImages")
@cross_origin()
def clearCacheImages():
    if CHITRO_ADMIN in request.cookies:
        if request.cookies.get(CHITRO_ADMIN)=="h3h3b0y5":
            global CookieImageDict
            CookieImageDict={}
            global ServedImageCount
            global GeneratedImageCount
            ServedImageCount=GeneratedImageCount
            return redirect("/adminLogin")
        else:
            return "Fake Admin",403
    else:
        return "<h1>Access Denied</h1>",403

@app.route("/clearLog")
@cross_origin()
def ClearCache():
    if CHITRO_ADMIN in request.cookies:
        if request.cookies.get(CHITRO_ADMIN)=="h3h3b0y5":
            with open(LOG_FILE,"w") as f:
                f.write("""# ChitroAI LOGS

""")
            global ExceptionCount
            ExceptionCount=0
            global NSFWCount
            NSFWCount=0
            return redirect("/adminLogin")
        else:
            return "Fake Admin",403
    else:
        return "<h1>Access Denied</h1>",403

if __name__=="__main__":
    app.run("0.0.0.0",os.getenv('PORT'))