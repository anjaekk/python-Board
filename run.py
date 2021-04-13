from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return "헬로파이썬"


if __name__ == "__main__":
    app.run(debug=True)

