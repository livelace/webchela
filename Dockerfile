FROM            docker.io/livelace/gentoo-x11:latest

ARG             VERSION

ENV             WEBCHELA_TEMP="/tmp/webchela"
ENV             WEBCHELA_EXTENSIONS_TEMP="/tmp/webchela_extensions"
ENV             WEBCHELA_URL="https://github.com/livelace/webchela"
ENV             WEBCHELA_EXTENSIONS_URL="https://github.com/livelace/webchela-extensions"

# portage packages.
RUN             emerge -G -q \
                "dev-python/pip" && \
                eselect python set "python3.8" && \
                rm -rf "/usr/portage/packages"

USER            "user"

# webchela.
RUN             git clone --depth 1 --branch "$VERSION" "$WEBCHELA_URL" "$WEBCHELA_TEMP" && \
                cd "$WEBCHELA_TEMP" && \
                pip install --user -r "requirements.txt" && \
                pip install --user . && \
                rm -rf "$WEBCHELA_TEMP"

# webchela-extensions.
RUN             git clone "$WEBCHELA_EXTENSIONS_URL" "$WEBCHELA_EXTENSIONS_TEMP" && \
                cd "$WEBCHELA_EXTENSIONS_TEMP" && \
                pip install --user . && \
                rm -rf "$WEBCHELA_EXTENSIONS_TEMP"

ENV             PATH=$PATH:"/home/webchela/.local/bin"

WORKDIR         "/home/webchela"

CMD             ["tini", "--", "/home/webchela/.local/bin/webchela"]
