from configparser import ConfigParser
from utils import ConfigLoader, ChatModel

class Agent:
    def __init__(self, system = "You are an helpful AI Assistant!"):
        self.system = system
        self.messages = []

        if system:
            self.messages.append({"role": "system", "content": system})

        self.config_loader = ConfigLoader()

        self.chat_model = ChatModel(self.config_loader)

    def __call__(self, message):
        self.messages.append({"role": "user", "content": message})
        
        result = self.execute(self.messages)

        self.messages.append({"role": "assistant", "content": result})

        return result
    
    def execute(self, messages):
        response = self.chat_model.get_response(messages)
        return response.message.content
    
prompt = """
You run in a loop of Thought, Action, PAUSE, Observation.
At the end of the loop you output an Answer.
Use Thought to describe your thoughts about the question you have been asked.
Use Action to run one of the actions available to you - then return PAUSE.
Observation will be the result of running those actions.

Your available actions are:

calculate:
e.g. calculate: 4 * 7 / 3
Runs a calculation and returns the number - uses Python so be sure to use floating point syntax if necessary

planet_mass:
e.g. planet_mass: Earth
returns the mass of a planet in the solar system

Example session:

Question: What is the combined mass of Earth and Mars?
Thought: I should find the mass of each planet using planet_mass.
Action: planet_mass: Earth
PAUSE

You will be called again with this:

Observation: Earth has a mass of 5.972 × 10^24 kg

You then output:

Answer: Earth has a mass of 5.972 × 10^24 kg

Next, call the agent again with:

Action: planet_mass: Mars
PAUSE

Observation: Mars has a mass of 0.64171 × 10^24 kg

You then output:

Answer: Mars has a mass of 0.64171 × 10^24 kg

Finally, calculate the combined mass.

Action: calculate: 5.972 + 0.64171
PAUSE

Observation: The combined mass is 6.61371 × 10^24 kg

Answer: The combined mass of Earth and Mars is 6.61371 × 10^24 kg
""".strip()    

def calculate(what):
    return eval(what)

def planet_mass(name): 
    masses = {
        'Earth': 5.97,
        'Mars': 0.6417,
        'Jupiter': 1898.19,
        'Saturn': 568.34,
        'Uranus': 86.813,
        'Neptune': 102.413,
    }

    return f"{name} has a mass of {masses.get(name, "Unknown planet")} × 10^24 kg"

known_actions = {
    'calculate': calculate,
    'planet_mass': planet_mass
}

if __name__ == "__main__":

    # Config = ConfigLoader()

    # chat_model = ChatModel(Config)

    # response = chat_model.get_response(messages=[
    #     {"role": "system", "content": "You are an helpful AI Assistant!"},
    #     {"role": "user", "content": "What is the capital of France?"}
    # ])

    # print(response.message.content)

    # Create agent
    agent = Agent(system=prompt)

    # Run agent with initial question
    result = agent("What is the combined mass of Jupyter and Saturn?")

    print(result)
