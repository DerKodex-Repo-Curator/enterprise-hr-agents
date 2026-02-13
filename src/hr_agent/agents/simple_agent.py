class MockAgent:
    def query(self, prompt, **kwargs):
        # Allow iteration (streaming)
        yield {
            "author": "mock_agent",
            "content": {
                "parts": [{"text": "Hello from Mock Agent"}]
            }
        }

simple_agent = MockAgent()
