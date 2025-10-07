# Image for a NYU Lab development environment
FROM rofrano/nyu-devops-base:su25

# Set up the Python development environment
WORKDIR /app
COPY Pipfile Pipfile.lock ./
RUN sudo python -m pip install --upgrade pip pipenv && \
    sudo pipenv install --system --dev

# Add missing dependencies for MySQL + migrations
RUN sudo pip install flask_migrate pymysql

# Install user mode tools
COPY .devcontainer/scripts/install-tools.sh /tmp/
RUN cd /tmp && bash ./install-tools.sh
