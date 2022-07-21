ARG             IMAGE_TAG

FROM            harbor-core.k8s-2.livelace.ru/dev/webchela:${IMAGE_TAG}

ENV             PIP_CONFIG_FILE="pip.conf"

ENV             WEBCHELA_TEMP="/tmp/webchela"

# portage packages.
RUN             emerge -G -q \
                "dev-python/pip" && \
                echo "python3.8" > "/etc/python-exec/python-exec.conf" && \
                rm -rf "/usr/portage/packages"

USER            "user"

# install webchela.
COPY            "work" "$WEBCHELA_TEMP"

RUN             cd "$WEBCHELA_TEMP" && \
                pip install --user -r "requirements.txt" && \
                pip install --user . && \
                rm -rf "$WEBCHELA_TEMP"

ENV             PATH=$PATH:"/home/user/.local/bin"

WORKDIR         "/home/user"

CMD             ["tini", "--", "/home/user/.local/bin/webchela"]
