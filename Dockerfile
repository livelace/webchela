FROM            harbor-core.k8s-2.livelace.ru/infra/gentoo-x11:latest

ENV             USER_NAME="user"
ENV             USER_HOME="/home/${USER_NAME}"

ENV             WEBCHELA_TEMP="/tmp/webchela"
ENV             WEBCHELA_EXTENSIONS_TEMP="/tmp/webchela_extensions"

ENV             WEBCHELA_URL="https://github.com/livelace/webchela"
ENV             WEBCHELA_EXTENSIONS_URL="https://github.com/livelace/webchela-extensions"

# portage packages.
RUN             emerge -G -q \
                "dev-python/pip" && \
                echo "python3.8" > "/etc/python-exec/python-exec.conf" && \
                rm -rf "/usr/portage/packages"

USER            "$USER_NAME"

# install webchela.
COPY            "work" "$WEBCHELA_TEMP"

RUN             cd "$WEBCHELA_TEMP" && \
                pip install --user -r "requirements.txt" && \
                pip install --user . && \
                rm -rf "$WEBCHELA_TEMP"

# install webchela-extensions.
RUN             git clone "$WEBCHELA_EXTENSIONS_URL" "$WEBCHELA_EXTENSIONS_TEMP" && \
                cd "$WEBCHELA_EXTENSIONS_TEMP" && \
                pip install --user . && \
                rm -rf "$WEBCHELA_EXTENSIONS_TEMP"

ENV             PATH=$PATH:"${USER_HOME}/.local/bin"

WORKDIR         "$USER_HOME"

CMD             ["tini", "--", "/${USER_HOME}/.local/bin/webchela"]
