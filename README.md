# sysinfo-restapp

This application is a basic Python3 Flask application which uses the platform module to print information about the system running it.  On its own, it doesn't do anything spectacular - it uses the /proc filesystemsn and the [Python platform module](https://docs.python.org/3/library/platform.html) to generate a report on system information.  Data is stored in a dictionary and returned via Flask's jsonify.

In this case, the code isn't really the point - I needed a small, independent REST service that I could deploy in a container.

## Background

This whole project started because I wanted to learn about running Kubernetes on Raspberry Pi hardware.  I have three Raspberry Pi 3b+ models on the network which are used for electronics projects and clustering projects.  While I have experience with containers and kubernetes, I have not tried deploying containers to the pis.

I recently learned about the [k3s project from Rancher](https://rancher.com/docs/k3s/latest/en/) and thought it would be a good test for my mini-cluster.  I decided to take the following approach:

* Create a simple Python Flask application which uses a [Python virtual environment](https://docs.python.org/3/library/venv.html)
* Place the application in a Docker image
* Install and configure a k3s cluster on my Raspberry Pi servers
* Deploy the containers to the k3s cluster
* Reverse proxy access to the application using Nginx

This approach worked and I got the whole thing done in less than 24 hours.

## Installation Process

### Creating the Application

[Flask](https://flask.palletsprojects.com/en/1.1.x/) is a simple framework for building web applications in Python.  While Flask can do a lot of things, it has become my go-to framework for building web services in Python.

I also use Python virtual environments when developing applications.  This allows me to have full control over application dependencies and versions.  It also makes creating a Docker container easy since the virtual environment can be configured there as well.

In this case, the application consists of a single file *sysinfo.py* that uses the /proc filesystem and *platform* module to create a data structure containing system information.  When a request is routed to the function, the application loads the data and returns it in JSON format.

I tested the Flask application before continuing - that involves setting the FLASK_APP environment variable and starting the application:

```text
flask run --host 0.0.0.0
```
The application will be available at http://127.0.0.1:5000/info

### Building a Docker Image

[Docker](https://www.docker.com/) is great and I love using it.  In this case, I knew my end goal was deploying this application to Kubernetes so I wanted to build a Docker image of the application.  

When I make Docker images for Python applications, I like to use virtual environments, just as I do for non-containerized Python applications.  There are [multiple ways](https://pythonspeed.com/articles/activate-virtualenv-dockerfile/) to use virtual environments in your Docker image but I try to use the simplest option - setting VIRTUAL_ENV and PATH environment variables in my Dockerfile.

The Docker image is based on the Ubuntu 18.04 ARMv7 image.  It then installs Python 3 and the necessary components via apt.  Once the Python packages are installed, the Flask library dependencies is installed via pip.  Finally, after all the software is installed, the Flask application is started.

Normally, at this point, I build the image and run it locally to validate that it works.  This involves running:
```text
docker build -t sysinfo-restapp:v1
```
and then running the image via:
```text
docker run -p 5000:5000 sysinfo-restapp
```
However, that won't work here - I'm working on a laptop running Ubuntu but it uses the x86_64 architecture instead of ARMv7 (as used by the Raspberry Pi).  To build for a different platform we need to use a strategy as described [in this blog post](https://www.docker.com/blog/multi-platform-docker-builds/) - using an emulator and *buildx*.  I downloaded the buildx binary from [their Github site](https://github.com/docker/buildx), installed in my local *~/.docker/cli-plugins/* directory.

Once buildx is installed, we can build the cross-platform image via this command:
```text
docker buildx build --platform linux/arm/v7 -t sysinfo-restapp-raspbian:v1 .
```
By specifying the platform, we can build the image via the emulator.  This takes a little longer but gets the job done.

I finished by uploading the Docker images to my personal repo on Docker Hub.  This will let me download and deploy them to Kubernetes.

### Configuring K3S

Setting up K3S was easy.  I already had three Pi 3b+ servers with Raspbian installed so I just needed to get K3S installed.  I followed their [Quick Start](https://rancher.com/docs/k3s/latest/en/quick-start/) instructions and it worked fine.  I created 1 master node and 2 worker nodes.

K3S is set up to be controlled via systemd so I needed to make one change on the master node - I needed to edit the */etc/systemd/system/k3s.service* file and add the *--with-kubeconfig-mode 644* to the start command.  Other than that, it was exactly like the instructions.

Note that you may need to futz with iptables depending on your version of raspbian - info is (here)[https://rancher.com/docs/k3s/latest/en/advanced/#enabling-legacy-iptables-on-raspbian-buster].

### Deploying to K3S

Once K3S was up and running, I followed a normal Kubernetes deployment structure.  This involved:

1. Creating a namespace
```text
kubectl create -f ns-sysinfo-restapp.yaml
```
2. Creating a service
```text
kubectl create -f service-sysinfo-restapp.yaml
```
3. Deploying the image
```text
kubectl create -f deployment-sysinfo-restapp.yaml
```
After these steps, the image is deployed and running on the K3S cluster.  I validated this with:

```text
pi@dusty:~ $ kubectl get deployments -n sysinfo-restapp
NAME              READY   UP-TO-DATE   AVAILABLE   AGE
sysinfo-restapp   3/3     3            3           3h33m

pi@dusty:~ $ kubectl get pods -n sysinfo-restapp
NAME                               READY   STATUS    RESTARTS   AGE
sysinfo-restapp-7bc65bcb49-qftwr   1/1     Running   0          3h33m
sysinfo-restapp-7bc65bcb49-7kp6v   1/1     Running   0          3h33m
sysinfo-restapp-7bc65bcb49-dqq4k   1/1     Running   0          3h33m
```
This shows three instances of the image running in pods.

### Accessing the Service

With the application deployed and running, we need to access it and validate it works.  This means we need an IP address to access.   Find it with this command:

```text
pi@dusty:~ $ kubectl get svc -n sysinfo-restapp
NAME              TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
sysinfo-restapp   NodePort   10.43.127.147   <none>        80:31485/TCP   9h
```

From the K3S master, I validated the service with curl.  It works!

```text
pi@dusty:~ $ curl http://10.43.127.147/info | python -m json.tool
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100   419  100   419    0     0    399      0  0:00:01  0:00:01 --:--:--   399
{
    "architecture": "32bit ",
    "cpus": [
        " ARMv7 Processor rev 4 (v7l)",
        " ARMv7 Processor rev 4 (v7l)",
        " ARMv7 Processor rev 4 (v7l)",
        " ARMv7 Processor rev 4 (v7l)"
    ],
    "distro": "Ubuntu 18.04 bionic",
    "freeMemory": "296248 kB",
    "node": "sysinfo-restapp-7bc65bcb49-qftwr",
    "processorFamily": "armv7l",
    "release": "4.19.97-v7+",
    "timestamp": "2020-05-19 22:49:32",
    "totalMemory": "895516 kB",
    "version": "#1294 SMP Thu Jan 30 13:15:58 GMT 2020"
}
```
Note that, even though the Flask application runs on port 5000, we remapped the ports in the service YAML file so the application is avaliable on port 80.

For a final step, I installed Nginx and set up a reverse proxy.  This isn't necessary but it's a good step for security purposes and added flexibiity.

