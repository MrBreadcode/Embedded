import logging
import paho.mqtt.client as mqtt
from edge.app.interfaces.agent_gateway import AgentGateway
from edge.app.entities.agent_data import AgentData
from edge.app.usecases.data_processing import process_agent_data
from edge.app.interfaces.hub_gateway import HubGateway

class AgentMQTTAdapter(AgentGateway):
    def __init__(self, broker_host, broker_port, topic, hub_gateway: HubGateway, batch_size=10):
        self.batch_size = batch_size
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.topic = topic
        self.client = mqtt.Client()
        self.hub_gateway = hub_gateway

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logging.info("Connected to MQTT broker")
            self.client.subscribe(self.topic)
        else:
            logging.info(f"Failed to connect to MQTT broker with code: {rc}")

    def on_message(self, client, userdata, msg):
        try:
            payload: str = msg.payload.decode("utf-8")
            agent_data = AgentData.model_validate_json(payload, strict=True)
            processed_data = process_agent_data(agent_data)
            if not self.hub_gateway.save_data(processed_data):
                logging.error("Hub is not available")
        except Exception as e:
            logging.info(f"Error processing MQTT message: {e}")

    def connect(self):
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.broker_host, self.broker_port, 60)

    def start(self):
        self.client.loop_start()

    def stop(self):
        self.client.loop_stop()

if __name__ == "__main__":
    broker_host = "localhost"
    broker_port = 1883
    topic = "agent_data_topic"
    store_gateway = HubGateway()
    adapter = AgentMQTTAdapter(broker_host, broker_port, topic, store_gateway)
    adapter.connect()
    adapter.start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        adapter.stop()
        logging.info("Adapter stopped.")
