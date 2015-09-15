echo Installing docker
command -v docker >/dev/null 2>&1 || $(wget -qO- https://get.docker.com/ | sh)

echo Installing docker-compose
command -v docker-compose >/dev/null 2>&1 || $(curl -L https://github.com/docker/compose/releases/download/1.3.0rc2/docker-compose-`uname -s`-`uname -m` > /usr/local/bin/docker-compose && chmod +x /usr/local/bin/docker-compose)

