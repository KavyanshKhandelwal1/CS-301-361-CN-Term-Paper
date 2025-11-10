import asyncio
import random
import time  # For potential timing stubs
from collections import namedtuple
import networkx as nx
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for saving plots
import matplotlib.pyplot as plt
import nest_asyncio
nest_asyncio.apply()  # For Jupyter/async environments

# --- Configuration ---
UAC_LATENCY_SECONDS = 3.0
UAC_PACKET_LOSS_RATE = 0.2
SENSOR_READING_INTERVAL = 5.0
NODE_TO_NODE_HOP_DELAY = 0.2
FOG_NODE_BATCH_SIZE = 10
MAX_HISTORY = 100

# --- Data Structure ---
SensorData = namedtuple("SensorData", ["timestamp", "source_node", "value", "data_type"])
historical_data = []  # Global for plotting across rounds

# --- Visualization ---
def plot_sensor_data(new_batch: list, round_id: int):
    print(f"VISUALIZER: Updating plot for round {round_id}...")
    for data in new_batch:
        historical_data.append((data.timestamp, data.value))
    while len(historical_data) > MAX_HISTORY:
        historical_data.pop(0)
    if not historical_data:
        return
    x_data = [d[0] for d in historical_data]
    y_data = [d[1] for d in historical_data]
    plt.figure(figsize=(10, 5))
    plt.scatter(x_data, y_data, c='blue', s=50, label='Sensor Reading')
    plt.title(f"Cloud View - Sensor Data (Round {round_id})")
    plt.xlabel("Timestamp")
    plt.ylabel("Sensor Value")
    plt.grid(True)
    plt.savefig(f"sensor_data_plot_round{round_id}.png")
    plt.close()
    print(f"VISUALIZER: sensor_data_plot_round{round_id}.png saved.")

def plot_network_graph(G: nx.Graph, round_id: int):
    print(f"VISUALIZER: Drawing network topology (Round {round_id})...")
    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(G, seed=42)
    colors = ['red' if G.nodes[n].get('type') == 'sink' else 'lightblue' for n in G.nodes()]
    nx.draw(G, pos, with_labels=True, node_color=colors, node_size=2000, font_size=10, edge_color='gray')
    plt.title(f"UIoT Network Topology (Round {round_id})")
    plt.savefig(f"network_topology_round{round_id}.png")
    plt.close()
    print(f"VISUALIZER: network_topology_round{round_id}.png saved.")

# --- Communication, Fog, Cloud ---
class UAC_Channel:
    def __init__(self, fog_node):
        self.fog_node = fog_node

    async def send_data(self, data: SensorData):
        await asyncio.sleep(UAC_LATENCY_SECONDS)
        if random.random() < UAC_PACKET_LOSS_RATE:
            print(f"COMM-LAYER: Lost packet from {data.source_node}")
            return
        self.fog_node.process_data(data)

class CloudServer:
    async def receive_data_batch(self, batch: list[SensorData], round_id: int):
        print(f"CLOUD: Received batch of {len(batch)} readings.")
        await asyncio.sleep(0.5)
        plot_sensor_data(batch, round_id)

class FogNode:
    def __init__(self, cloud):
        self.cloud = cloud
        self.buffer = []

    def process_data(self, data: SensorData):
        if data.data_type == "Emergency":
            print(f"FOG: Emergency from {data.source_node}! Value={data.value}")
        else:
            self.buffer.append(data)
            if len(self.buffer) >= FOG_NODE_BATCH_SIZE:
                asyncio.create_task(self.cloud.receive_data_batch(self.buffer, data.timestamp // 10 + 1))
                self.buffer = []

# --- Sensing & Networking ---
class SensorNode:
    def __init__(self, node_id, G, sink_id):
        self.node_id = node_id
        self.G = G
        self.sink_id = sink_id
        self.t = 0

    def _get_raw(self):
        return round(random.uniform(10,120),2)

    def _classify(self, v):
        return "Emergency" if v > 80 else "Normal"

    async def run(self):
        while self.t < 30: # Run 30 simulated seconds
            await asyncio.sleep(SENSOR_READING_INTERVAL)
            v = self._get_raw()
            t = self._classify(v)
            self.t += 1
            data = SensorData(self.t, self.node_id, v, t)
            print(f"{self.node_id}: Generated {t} value {v}")
            asyncio.create_task(self.forward(data))

    async def forward(self, data):
        try:
            path = nx.shortest_path(self.G, self.node_id, self.sink_id)
            if len(path) < 2:
                return
            nxt = self.G.nodes[path[1]]['instance']
            await asyncio.sleep(NODE_TO_NODE_HOP_DELAY)
            await nxt.receive_data(data, self.node_id)
        except:
            pass

    async def receive_data(self, data, from_node):
        if self.node_id == self.sink_id:
            await self.G.nodes['sink']['instance'].receive_data(data, from_node)
        else:
            asyncio.create_task(self.forward(data))

class SinkNode:
    def __init__(self, node_id, channel):
        self.node_id = node_id
        self.channel = channel

    async def receive_data(self, data, from_node):
        print(f"SINK: Received from {from_node}, forwarding to surface.")
        asyncio.create_task(self.channel.send_data(data))

# --- Main Simulation ---
async def run_round(round_id: int):
    print(f"\n===== Simulation Round {round_id} Start =====")
    cloud = CloudServer()
    fog = FogNode(cloud)
    ch = UAC_Channel(fog)
    G = nx.Graph()
    sink = SinkNode('sink', ch)
    G.add_node('sink', instance=sink, type='sink')
    sensors = [SensorNode(f'sensor-{i}', G, 'sink') for i in range(5)]
    for s in sensors:
        G.add_node(s.node_id, instance=s, type='sensor')
    edges = [('sensor-0', 'sensor-1'), ('sensor-1', 'sensor-2'),
             ('sensor-2', 'sensor-3'), ('sensor-3', 'sensor-4'), ('sensor-4', 'sink')]
    G.add_edges_from(edges)
    plot_network_graph(G, round_id)
    await asyncio.gather(*(s.run() for s in sensors))
    print(f"===== Simulation Round {round_id} End =====")

async def main():
    for r in range(1, 4): # Run 3 rounds for comparison
        await run_round(r)
        await asyncio.sleep(2)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Simulation stopped.")