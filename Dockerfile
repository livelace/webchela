ARG             IMAGE_TAG

FROM            registry.livelace.ru/dev/webchela:${IMAGE_TAG}

ENV             PIP_CONFIG_FILE="pip.conf"

ENV             WEBCHELA_TEMP="/tmp/webchela"

USER            "user"

# install webchela.
COPY            "work" "$WEBCHELA_TEMP"

RUN             cd "$WEBCHELA_TEMP" && \
                pip install --no-cache-dir --user -r "requirements.txt" && \
                pip install --no-cache-dir --user . && \
                rm -rf "$WEBCHELA_TEMP"

ENV             PATH=$PATH:"/home/user/.local/bin"

WORKDIR         "/home/user"

CMD             ["tini", "--", "/home/user/.local/bin/webchela"]
