from flask import Flask, jsonify
import platform
from datetime import datetime

app = Flask(__name__)

# API endpoint for retrieving system info
@app.route('/info', methods=['GET'])
def getSystemInfo():
    sysinfo = {}
    sysinfo['architecture'] = ' '.join(platform.architecture())
    sysinfo['distro'] = ' '.join(platform.dist())
    sysinfo['processorFamily'] = platform.processor()
    sysinfo['release'] = platform.release()
    sysinfo['version'] = platform.version()
    sysinfo['node'] = platform.node()
    with open("/proc/cpuinfo", "r")  as f:
        info = f.readlines()
    cpuinfo = [x.strip().split(":")[1] for x in info if "model name"  in x]
    sysinfo['cpus'] = cpuinfo
    with open("/proc/meminfo", "r") as f:
        mem_info = f.readlines()
    sysinfo['totalMemory'] = ' '.join(mem_info[0].strip().split()[1:])
    sysinfo['freeMemory'] = ' '.join(mem_info[1].strip().split()[1:])
    sysinfo['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return jsonify(sysinfo)

if __name__ == '__main__':
    app.run()