import pickle
import sklearn
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

app = FastAPI()

pk_file = open('language_model.pk', 'rb')
cv, model, le = pickle.load(pk_file)
pk_file.close()

def predict(text):
    x = cv.transform([text]).toarray()
    lang = model.predict(x)
    lang = le.inverse_transform(lang)
    return lang[0]

html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/buefy/dist/buefy.min.css">
    <title>Language Detection</title>
</head>
<body>
    <div id="app">
        <section class="hero is-large">
            <div class="hero-head">
                <nav class="navbar">
                    <div class="container">
                        <div class="navbar-brand">
                            <a class="navbar-item">
                                <p class="title">Language Detection</p>
                            </a>
                        </div>
                    </div>
                </nav>
            </div>
            <div class="hero-body">
                <div class="container has-text-centered">
                    <div class="columns">
                        <div class="column"></div>
                        <div class="column is-two-thirds">
                            <div class="box">
                                <b-tag v-if="text.trim()" type="is-primary" size="is-large">
                                    <template v-if="!onDetect && state === 1">{{ lang }} Language</template>
                                    <template v-else>Loading...</template>
                                </b-tag>
                                <b-tag v-else type="is-primary" size="is-large">Input Text</b-tag>
                                <b-field class="mt-3 mb-3">
                                    <b-input v-on:input="sendText" v-model="text" type="textarea" :disabled="state !== 1"></b-input>
                                </b-field>
                            </div>
                        </div>
                        <div class="column"></div>
                    </div>
                    <p class="subtitle">Support 22 languages</p>
                </div>
            </div>
        </section>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/vue@2"></script>
    <script src="https://unpkg.com/buefy/dist/buefy.min.js"></script>
    <script>
        var app = new Vue({
            el: '#app',
            data: {
                text: '',
                lang: '',
                onDetect: false,
                socket: null,
                state: null
            },
            watch: {
                state: function() {
                    if (!this.state) return this.$buefy.toast.open({message: "Connecting...", type: "is-warning", indefinite: true})
                    else if(this.state !== 1) return this.$buefy.toast.open({message: "Disconnected", type: "is-danger", indefinite: true})
                }
            },
            methods: {
                sendText: function() {
                    if (this.text.trim()) {
                        this.onDetect = true
                        this.socket.send(this.text)
                    }
                },
                connect: function() {
                    this.socket = new WebSocket('wss://detectlang.herokuapp.com/')
                    this.state = this.socket.readyState
                    this.socket.onopen = (e) => {
                        this.state = 1
                        this.$buefy.toast.open({
                            message: "Connected",
                            type: "is-success",
                            duration: 2000
                        })
                    }
                    this.socket.onmessage = (e) => {
                        this.lang = e.data
                        this.onDetect = false
                    }
                    this.socket.onclose = (e) => {
                        this.state = 2
                        setTimeout(() => this.connect(), 5000)
                    }
                    this.socket.onerror = (e) => {
                        this.state = 3
                        setTimeout(() => this.connect(), 5000)
                    }
                }
            },
            created: function() {
                this.connect()
            }
        })
    </script>
</body>
</html>
"""

@app.get("/")
async def index():
    return HTMLResponse(html)

@app.websocket("/")
async def websocket_index(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        data = predict(data)
        await websocket.send_text(data)