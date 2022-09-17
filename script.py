from flask import Flask, render_template 
import docker 
import json
import os  

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


app = Flask(__name__)

@app.route('/')
def index():

        return render_template('index.html')

@app.route('/table')
def resource_table():

        client = docker.from_env()
        containers = []
        for container in client.containers.list():
                container_stats = container.stats(stream=False)
                name = container_stats['name']
               	id = container_stats['id']
               	cpu = calculate_cpu_percent(container_stats['cpu_stats'], container_stats['precpu_stats'])
                memory = calculate_memory_percent(container_stats['memory_stats'])
                containers.append({"id": id, "name": name, "cpu":cpu, "memory":memory})

                file = open(os.path.join('./resource_logs', id), 'a')
                file.write(str(cpu) + " " + str(memory)+ "\n")
                file.close()

        return render_template('resource_table.html', containers=containers)

if __name__ == "__main__":
        app.run(host="0.0.0.0")


