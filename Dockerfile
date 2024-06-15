ARG             IMAGE_TAG

FROM            registry.livelace.ru/dev/webchela:${IMAGE_TAG}

ENV             PIP_CONFIG_FILE="pip.conf"

ENV             WEBCHELA_TEMP="/tmp/webchela"

USER            "user"

# install webchela.
COPY            "work" "$WEBCHELA_TEMP"

RUN             cd "$WEBCHELA_TEMP" && \
                python -m venv venv &&  source ./venv/bin/activate && \
                pip install --no-cache-dir --user -r "requirements.txt" && \
                pip install --no-cache-dir --user . && \
                rm -rf "$WEBCHELA_TEMP"

ENV             PATH=$PATH:"/home/user/webchela/venv/bin"

WORKDIR         "/home/user"

CMD             ["tini", "--", "/home/user/webchela/venv/bin/webchela"]
