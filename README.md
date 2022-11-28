
# 1 Introduction
The project consists in creating a monitor agent to log and visualize in real time through a web interface CPU and Memory consumption, and Network I/O of docker containers.

The agent is containerized, having in a single image both the software and the environment necessary for execution.

# 2 Web Interface
There are two main web pages.
## 2.1 /
The main page, consisting in a table with ID, CPU, Memory and Network I/O of every running container, periodically updated through a script using AJAX that communicates with the paghe /table.

With every call to /table, log files are updated including timestamps of every read.

## 2.2 /containers
This pages returns a JSON with statistics about every container, indexed by ID.

It is also possible to request a specific container through a GET request using an ID field referring to said container.

# 3 Container
Containers are executable units encapsulating a software with its libraries and dependencies.

Docker is one of the platforms that allows to create, manage and execute containers and images, and is used in this project.

It is important to distinguish between imagine and container; similiarly to object oriented programming, an image is a class and a container an instance of said class.

An image can be considered the fundamental unit of this technology; it gets created, shared and allows the execution of several containers.

To create an image with Docker a Dockerfile is used, containing all the commands necessary to build the image.


# 4 Dockerfile

The dockerfile has a layered structure, containing the commands to execute, the libraries and dependencies to import.

There could be cases where some levels are present in more images; in this cases those levels can be reused, granting improved performances and storage usage.

The dockerfile of our agent is the following:

```
FROM python:3.8-slim-buster
WORKDIR /python-docker
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN mkdir resource_logs
COPY . .
CMD [ "python3", "script.py"]
EXPOSE 5000/tcp
```

Explaination of every command:

- FROM: Inizializes a building fase and sets the base image to import, on which the following instructions will be executed to create the new layers. Every valid Dockerfile must begin with the instruction FROM. The specified image must be valid and could be both in local storage and in public repositories.

- WORKDIR: Sets the active directory, in which RUN, CMD and ENTRYPOINT will be executed. The directory will be created if it doesn't exist.

- COPU: Copies file from the source directory in the host (the former) into the destination folder in the container (the latter) 

- RUN: Executes command on the image that was built up to that point, and creates a new image on which the next commands will be executed.

- CMD: The default command that will be executed on the shell every time the container boots. There can be only a CMD field for Dockerfile.

- EXPOSE: Specifies which port must be bound to the host. It isn't automatic and has to be specified during the boot fase with the flag -p hostport:containerport.

# 5 Usage
Once the image is created, it is necessary to mount the docker socket and bind the interface port.

## 5.1 Mounting the folder which will contain the log files.
### 5.1.1 Motivazione

A folder has to be mounted, to make the new logs persistent.

### 5.1.1 Flag

The path used inside the container is /python-docker/resource_logs.
The option to add is hence:

```
-v log_folder_path:/python-docker/resource_logs
```

## 5.2 Using docker from inside the container
There are two ways to do this.

### 5.2.1 Mounting docker socket
This has to be done mounting the docker.sock file in the path inside the container, which is the default location of the socket: /var/run/docker.sock. The option to add is:

```
-v docker_socket_path:/var/run/docker.sock
```

This makes the security of the container way thinnier, since the daemon docker is executing on the host with root privileges.

So in case the agent and the docker daemon were exploitable it would be possible to attack the host machine.

### 5.2.2 Alternative: --privileged
Another way to make the socket accessible from within the container is to use the --privileged flag at run fase.

This option automatically mounts the dock.sock in the default path, but also grants the container more privileges, for example mounting all host devices inside the container, making it possible to mount the host's filesystem inside the container which could then read and modify it since Docker is executed with root privileges.

### 5.2.3 Differences
Even though the second approach sounds much riskier in case someone could exploit the services exposed by the container, in reality the difference is none.

In fact once the socket is bound, it is possible to create new containers from inside the first container. And since a new container can be created with the --privileged flag, one could easily go from the first case to the second.


## 5.3 Port binding
### 5.3.1 Motivazione
Port binding has to be done in order to make services accessible from outside.
### 5.3.2 Flag
The web server is listening on port 5000, hence a free port on the host has to be bound to port 5000 inside the container. The option is:

```
-p free_port:5000
```

## 5.4 Command
The full command to correctly run the agent is:
```
$ docker run -p free_port:5000 -v docker_socket_path:/var/run/docker.sock  \
-v log_folder_path:/python-docker/resource_logs imageName

```

or,

```
$ docker run -p free_port:5000 \
-v log_folder_path:/python-docker/resource_logs --privileged imageName
```

# 6 Code
The server was written in Python, using the framework Flask to build the web interface, and the docker module to interact with the Docker daemon.

Server main code:

```
client = docker.from_env()
containers = []
        for container in client.containers.list():
                container_stats = container.stats(stream=False)
                derived_container_stats = compute_container_stats(container_stats)
                derived_container_stats['id'] = container_stats['id']
                containers.append(derived_container_stats)
                write_log(derived_container_stats)

        return render_template('resource_table.html', containers=containers)
        
        def compute_container_stats(container_stats):
        name = container_stats['name']
       	cpu = calculate_cpu_percent(container_stats['cpu_stats'], container_stats['precpu_stats'])
        memory = calculate_memory_percent(container_stats['memory_stats'])
        network_in, network_out = calculate_network_in_out(container_stats['networks']) 

        return dict({"name": name, "cpu":cpu, "memory":memory, "network_in":network_in, "network_out":network_out})
```

First a client variable that connects to docker socket is initialized.

Then every running container is listed, and sent to the function compute_container_stats() which takes the fields: name, id and:
- sends to function calculate_cpu_percent() the fields cpu_stats e precpu_stats
- sends to the function calculate_memory_percent() the field memory_stats
- sends to calculate_network_in_out() the field networks

The formulas used to compute resources usage will now be explained.

## CPU Usage Formula
The following is the function used inside the code.[^CPUFormula]

[^CPUFormula]: [CPU usage Formula](https://gist.github.com/BeardedDonut/5e3643b06e90ce4d41197d8cfb8fb0b5)

```
def calculate_cpu_percent(cpu_stats, precpu_stats):
    cpu_count = cpu_stats["online_cpus"]
    cpu_percent = 0.0
    cpu_delta = float(cpu_stats["cpu_usage"]["total_usage"]) - float(precpu_stats["cpu_usage"]["total_usage"])
    system_delta = float(cpu_stats["system_cpu_usage"]) - float(precpu_stats["system_cpu_usage"])
    if system_delta > 0.0:
       cpu_percent = cpu_delta / system_delta * 100.0 * cpu_count
    return round(cpu_percent,2)
```

First let's clarify the difference between cpu_stats and precpu_stats.

The former are the last stats calculated, the latter are about the previous tick.

This is because saved data refers to all data generated from the beginning of data monitoring, and not only about the latest tick, hence we have to subtract the last stats to the previous one to calculate cpu_delta and system_delta.

We then calculate the change between the container usage of cpu (cpu_delta) and the whole system usage of it (system_delta) including idle usage, both from kernel and from users.

In the end the percentage is calculated, multiplying by the number of cpus (cpu_count). This implies that it is possible to see cpu usage above 100%. (100% means that the equivalent to a whole cpu is fully utilized)[^CPUPercentageOver100]

[^CPUPercentageOver100]: [Why can CPU usage be over 100](https://github.com/moby/moby/issues/13626#issuecomment-107522479)

## 6.1 Memory Usage Formula

```
def calculate_memory_percent(memory_stats):
   return round(float(memory_stats['usage'])/float(memory_stats['limit'])*100,2)
```

In this formula we consider how much memory is used currently by the container and how much is available in the whole system.[^MemoryFormula] (Above which the container would be in Out Of Memory).

[^MemoryFormula]: [Memory Usage Formula](https://github.com/moby/moby/blob/eb131c5383db8cac633919f82abad86c99bffbe5/cli/command/container/stats_helpers.go#L110)

## 6.2 Network I/O Usage Formula

```
def calculate_network_in_out(container_stats):
        conversion_costant = 1024
        network_in = 0
        network_out = 0 
        for interface in container_stats['networks']:
                network_in += container_stats["networks"][interface]['rx_bytes']
                network_out += container_stats["networks"][interface]['tx_bytes']

        return network_in/conversion_costant, network_out/conversion_costant
```

Bytes going in and out of every interface are counted. The results are then divided by a costant, in this case kiloBytes.
