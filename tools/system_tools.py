import os,platform,shutil,socket,subprocess,psutil
def run_tool(tool):
    if tool=="system":
        return f"Operating system: {platform.system()}\nOS version: {platform.version()}\nMachine: {platform.machine()}\nProcessor: {platform.processor()}\nCPU count: {psutil.cpu_count(logical=True)}"
    if tool=="ram":
        m=psutil.virtual_memory();return f"You're using {m.used/1024**3:.2f} GB of {m.total/1024**3:.2f} GB RAM ({m.percent}%)."
    if tool=="disk":
        d=shutil.disk_usage(os.path.abspath(os.sep));p=d.used/d.total*100;return f"You're using {d.used/1024**3:.2f} GB of {d.total/1024**3:.2f} GB disk space ({p:.1f}%).\nFree space: {d.free/1024**3:.2f} GB."
    if tool=="cpu":return f"You have {psutil.cpu_count(logical=True)} logical CPU cores. Processor: {platform.processor()}."
    if tool=="hostname":return socket.gethostname()
    if tool=="current_user":return os.getenv("USERNAME","Unknown")
    if tool in {"ipconfig","windows_version"}:
        cmd="ipconfig" if tool=="ipconfig" else "ver"
        return subprocess.run(cmd,shell=True,capture_output=True,text=True,timeout=15).stdout.strip()
