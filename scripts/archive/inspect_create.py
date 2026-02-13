
from vertexai.preview import reasoning_engines
try:
    help(reasoning_engines.ReasoningEngine.create)
except Exception as e:
    print(e)
