# Docker and Docker Compose Installs

## Once the virtual machine is up with the operative system fully installed, we proceed with installing Docker and Docker compose

### 1) We start updating Linux packages and some needed dependencies
```bash
sudo apt update && sudo apt upgrade -y
```

```bash
sudo apt install apt-transport-https ca-certificates curl software-properties-common
sudo apt install gnupg
```

### 2) Then, add Docker's official GPG key to the trusted keyring directory
```bash
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo tee /etc/apt/trusted.gpg.d/docker.asc
```

### 3) Download Docker Repo
```bash
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
```

### 4) Check versions
```bash
apt-cache madison docker-ce
```

### 5) Select versions and Install
```bash
sudo apt install docker-ce=5:27.5.1-1~ubuntu.24.04~noble docker-ce-cli=5:27.5.1-1~ubuntu.24.04~noble containerd.io
```

### 6) Enable
```bash
sudo systemctl start docker
sudo systemctl enable docker
```

### 7) Now, Docker Compose
```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
```

### 8) Add execute permissions
```bash
sudo chmod +x /usr/local/bin/docker-compose
```


## Useful commands

`Notice the compose commands need the docker-compose.yaml/yml file to be present in the directory where it's being run`

### Start container
```bash
sudo docker-compose up
```

### Start in detached mode
```bash
sudo docker-compose up -d
```

### Build from Dockerfiles + Start in detached mode
```bash
sudo docker-compose up --build -d
```

### Check running containers
```bash
sudo docker ps
```

### Stop and remove container
```bash
sudo docker-compose down
```

### Stop and also remove volume
```bash
sudo docker-compose down -v
```

### Stop remove container, keep volume
```bash
sudo docker-compose down --volumes
```