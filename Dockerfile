ARG             IMAGE_TAG

FROM            registry.livelace.ru/dev/webchela:${IMAGE_TAG}

ENV             PIP_CONFIG_FILE="pip.conf"

ENV             WEBCHELA_DIR="/home/user/webchela"

USER            "user"

# install webchela.
COPY            "work" "$WEBCHELA_DIR"

RUN             cd "$WEBCHELA_DIR" && \
                python -m venv venv &&  source ./venv/bin/activate && \
                pip install --no-cache-dir -r "requirements.txt" && \
                pip install --no-cache-dir .

ENV             PATH=$PATH:"/home/user/webchela/venv/bin"

WORKDIR         "/home/user"

CMD             ["tini", "--", "/home/user/webchela/venv/bin/webchela"]
