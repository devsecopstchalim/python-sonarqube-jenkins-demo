from flask import Flask, jsonify

import calculator


def create_app() -> Flask:
    flask_app = Flask(__name__)

    @flask_app.get("/health")
    def health():
        return jsonify(status="ok Argocd sonarqube jenkins")

    @flask_app.get("/add/<int:a>/<int:b>")
    def add(a, b):
        return jsonify(result=calculator.add(a, b))

    @flask_app.get("/divide/<int:a>/<int:b>")
    def divide(a, b):
        try:
            return jsonify(result=calculator.divide(a, b))
        except ValueError as exc:
            return jsonify(error=str(exc)), 400

    return flask_app


app = create_app()
