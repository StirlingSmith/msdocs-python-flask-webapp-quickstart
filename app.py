from flask import Flask, request, Response
import os
import requests

import bs4 as bs
import redis
import json
import threading

app = Flask(__name__)


@app.route('/', methods=["GET", "POST"])
@app.route('/home')
def home():
    print("Hello hello hello")
    return {"text": "Hello World"}




###################
@app.route('/call_llm', methods=["POST"])
def call_llm():
    attachments = request.json.get("attachments")
    soup = bs.BeautifulSoup(attachments[0]["content"], "html")
    text = soup.get_text()

    print(text)

    # Start a new thread for processing the event
    thread = threading.Thread(target=process_call_llm_async, args=(str(text),))
    thread.start()

    # Respond immediately to Slack
    return Response(), 200

def process_call_llm_async(text):
    # Your existing logic for processing the news query
    formatted_text = text.replace(" ", "+")
    # processing_message = get_processing_message(text)
    # print(processing_message)
    url = os.environ["LLMADDR"]+f"/news_query?query={formatted_text}&channel_id=''"
    resp = requests.get(url, timeout=120)

    #conn = redis.from_url(resp.text)
    #r = redis.Redis(conn)

    print("URL: ", url)
    print("LLM response code: ", resp)

    redis_url, job_id = json.loads(resp.text)

    conn = redis.from_url(redis_url, ssl_cert_reqs=None)
    q = Queue(connection=conn)

    def foo():
        pass
    j = q.create_job(foo)

    output = j.fetch(job_id, conn)
    print("redis url: ",redis_url)
    
    # response = client.chat_postMessage(
    #     channel=channel_id, text=processing_message)
    
    message_id = response['ts']

    i=0
    max_iters=10
    while output.result==None and i<max_iters:
        i+=1
        if i>1:
            # dot_text = processing_message + "." * (i-1)
            # response = client.chat_update(
            #     channel=channel_id, ts=message_id, text=dot_text)
            
            message_id = response['ts']
        print(output.get_status())
        if output.get_status() == "failed":
            print("job failed, retrying")
            
            resp = requests.get(url, timeout=120)
            redis_url, job_id = json.loads(resp.text)

            conn = redis.from_url(redis_url, ssl_cert_reqs=None)
            q = Queue(connection=conn)

            def foo():
                pass
            j = q.create_job(foo)

            output = j.fetch(job_id, conn)
            print("redis url: ",redis_url)
        time.sleep(15)

    # client.chat_delete(
    #             channel=channel_id, ts=message_id)
    
    if output.result==None:
        return {"text":"No response from LLM"}
        # client.chat_postMessage(
        #     channel=channel_id, text="PROMPT: \n"+text+"\n No response from LLM")  
    else:
        return {"text": str(output.result)}  
        # client.chat_postMessage(
        #     channel=channel_id, text="PROMPT: \n"+text+"\n"+str(output.result))




@app.route('/configure')
def configure():
    conf_html = """<body>
        <header class="header">
            <header class="header">
                <div class="header-inner-container">
                    <div style="display: flex; align-content: center; font-size: 24px;">Welcome to {{App Name}} App</div>
                </div>
                <div class="header-inner-container">
                    <div style="display: flex; align-content: center;font-size: 18px;">Press save to continue</div>
                </div>
            </header>
            <script src="https://statics.teams.microsoft.com/sdk/v1.8.0/js/MicrosoftTeams.min.js"></script>
            <script>
                microsoftTeams.initialize();
                microsoftTeams.appInitialization.notifySuccess();
                microsoftTeams.settings.registerOnSaveHandler(function (saveEvent) {
                    microsoftTeams.settings.setSettings({
                        entityID: "{{App Name}}",
                        contentUrl: `${window.location.origin}/index.html`,
                        suggestedTabName: "{{App Name}}",
                        websiteUrl: `${window.location.origin}/index.html`,
                    });
                    saveEvent.notifySuccess();
                    microsoftTeams.settings.setValidityState(true);
                    // microsoftTeams.appInitialization.notifyAppLoaded();
                });
                microsoftTeams.settings.setValidityState(true);
            </script>
    </body>"""
    return conf_html




# Start the server on port 3000
if __name__ == "__main__":
  app.run(port=3000)