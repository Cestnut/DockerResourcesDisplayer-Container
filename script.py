from flask import Flask, render_template, request
import docker 
import json
import os  
import time

def calculate_cpu_percent(cpu_stats, precpu_stats):
    cpu_count = cpu_stats["online_cpus"]
    cpu_percent = 0.0
    cpu_delta = float(cpu_stats["cpu_usage"]["total_usage"]) - float(precpu_stats["cpu_usage"]["total_usage"])
    system_delta = float(cpu_stats["system_cpu_usage"]) - float(precpu_stats["system_cpu_usage"])
    if system_delta > 0.0:
       cpu_percent = cpu_delta / system_delta * 100.0 * cpu_count
    return round(cpu_percent,2)

def calculate_memory_percent(memory_stats):
   return round(float(memory_stats['usage'])/float(memory_stats['limit'])*100,2)

def calculate_network_in_out(container_stats):
        conversion_costant = 1024
        network_in = 0
        network_out = 0 
        for interface in container_stats['networks']:
                network_in += container_stats["networks"][interface]['rx_bytes']
                network_out += container_stats["networks"][interface]['tx_bytes']

        return network_in/conversion_costant, network_out/conversion_costant

app = Flask(__name__)

@app.route('/')
def index():

        return render_template('index.html')

@app.route('/containers', methods=["GET"])
def get_container():
        id = request.args.get('id')
        client = docker.from_env()
        if id:
                for container in client.containers.list():
                        stats = container.stats(stream=False)
                        print(id)
                        if stats['id'] == id:
                                print(id)
                                return json.dumps(compute_container_stats(stats))
                                break
        else:
                return json.dumps(all_containers_stats())

@app.route('/table')
def resource_table():

        client = docker.from_env()
        containers = []
        for container in client.containers.list():
                container_stats = container.stats(stream=False)
                derived_container_stats = compute_container_stats(container_stats)
                derived_container_stats['id'] = container_stats['id']
                containers.append(derived_container_stats)
                write_log(derived_container_stats)

        return render_template('resource_table.html', containers=containers)


def write_log(container_stats):
        file = open(os.path.join('./resource_logs', container_stats['id']), 'a')
        file.write(str(time.time()) + " " + str(container_stats['cpu']) + " " + str(container_stats['memory']) \
        + " " + str(container_stats['network_in']) + " " + str(container_stats['network_out']) + "\n")
        file.close()

def compute_container_stats(container_stats):
        name = container_stats['name']
       	cpu = calculate_cpu_percent(container_stats['cpu_stats'], container_stats['precpu_stats'])
        memory = calculate_memory_percent(container_stats['memory_stats'])
        network_in, network_out = calculate_network_in_out(container_stats) 

        return dict({"name": name, "cpu":cpu, "memory":memory, "network_in":network_in, "network_out":network_out})

#Different from the code in resource_table(), because here the return type is a dict where keys are id of containers.
#In the main code of resource_table() the return type is a list where in every entry the id is a key on the same level as the others.
def all_containers_stats():
        client = docker.from_env()
        containers = dict()
        for container in client.containers.list():
                container_stats = container.stats(stream=False)
                derived_container_stats = compute_container_stats(container_stats)
                containers[container_stats['id']] = derived_container_stats
        return containers

if __name__ == "__main__":
        app.run(host="0.0.0.0")


