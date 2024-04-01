from edge.app.entities.agent_data import AgentData
from edge.app.entities.processed_agent_data import ProcessedAgentData


def process_agent_data(agent_data: AgentData) -> ProcessedAgentData:
    """
    Process agent data and classify the state of the road surface.
    Parameters:
        agent_data (AgentData): Agent data that containing accelerometer, GPS, and timestamp.
    Returns:
        processed_data_batch (ProcessedAgentData): Processed data containing the classified state of the road surface and agent data.
    """
    # Placeholder implementation for demonstration
    # Replace with your actual data processing logic
    road_state = classify_road_state(agent_data)
    processed_data = ProcessedAgentData(road_state=road_state, agent_data=agent_data)
    return processed_data

def classify_road_state(agent_data: AgentData) -> str:
    """
    Placeholder function to classify the state of the road surface based on agent data.
    Parameters:
        agent_data (AgentData): Agent data that containing accelerometer, GPS, and timestamp.
    Returns:
        str: Classified state of the road surface.
    """
    # Implement your road state classification logic here
    # For demonstration, let's assume a simple classification based on accelerometer data
    if agent_data.accelerometer.z > 0:
        return "Smooth"
    else:
        return "Rough"
