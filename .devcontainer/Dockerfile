FROM frappe/bench:latest

USER frappe

ENV NVM_DIR=/home/frappe/.nvm
ENV PATH=/home/frappe/.nvm/versions/node/v24.16.0/bin:/home/frappe/.local/bin:${PATH}

RUN bash -lc '. "$NVM_DIR/nvm.sh" \
    && nvm install 24.16.0 \
    && nvm alias default 24.16.0 \
    && uv python install 3.14'

USER root

RUN mkdir -p \
      /home/frappe/.vscode-server/bin \
      /home/frappe/.vscode-server/data \
      /home/frappe/.vscode-server/extensions \
      /home/frappe/.cache \
      /home/frappe/.local \
    && chown -R frappe:frappe \
      /home/frappe/.vscode-server \
      /home/frappe/.cache \
      /home/frappe/.local

USER frappe

WORKDIR /workspace/frappe-bench
