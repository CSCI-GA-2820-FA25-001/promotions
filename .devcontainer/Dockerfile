# Image for a NYU Lab development environment
FROM rofrano/nyu-devops-base:su25

# Set up the Python development environment
WORKDIR /app
COPY Pipfile Pipfile.lock ./
RUN sudo python -m pip install --upgrade pip pipenv && \
    sudo pipenv install --system --dev
# Install user mode tools
COPY .devcontainer/scripts/install-tools.sh /tmp/
RUN cd /tmp && bash ./install-tools.sh
# Add missing dependencies for MySQL + migrations
RUN sudo pip install flask_migrate pymysql
# Add pytest
RUN pip install pytest

COPY .devcontainer/scripts/entrypoint.sh /entrypoint.sh
RUN sudo chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
