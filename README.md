# python-sonar-demo

Tiny Flask API used to test the pipeline GitHub -> Jenkins -> SonarQube -> Docker image.

Run locally:

    python -m venv .venv && . .venv/bin/activate
    pip install -r requirements-dev.txt
    python -m pytest --cov --cov-report=xml:coverage.xml
    docker build -t python-sonar-demo . && docker run --rm -p 8000:8000 python-sonar-demo
    curl localhost:8000/add/2/3
