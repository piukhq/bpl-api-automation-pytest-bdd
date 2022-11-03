FROM ghcr.io/binkhq/python:3.9-pipenv

WORKDIR /app
ADD . .

RUN pipenv install --system --deploy --ignore-pipfile && \
    apt-get update && apt-get install -y wget && apt-get install -y curl && \
    curl -sL https://aka.ms/InstallAzureCLIDeb | bash && \
    apt-get autoremove -y wget && rm -rf /var/lib/apt/lists

CMD [ "python", "schedule.py" ]
