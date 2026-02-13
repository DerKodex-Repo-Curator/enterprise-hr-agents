
import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add src to path to import agent
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from hr_agent.agent import HRPolicyAgent

class TestHRPolicyAgent(unittest.TestCase):
    
    @patch('hr_agent.agent.vertexai')
    @patch('hr_agent.agent.GenerativeModel')
    @patch('hr_agent.agent.BigQueryLogger')
    @patch('hr_agent.agent.Tool')
    def test_query_success(self, mock_tool, mock_bq_logger, mock_gen_model, mock_vertexai):
        # Setup
        agent_instance = HRPolicyAgent(
            project_id="test-project",
            location="us-central1",
            datastore_id="test-datastore",
            dataset_id="test-dataset",
            table_id="test-table",
            model_name="gemini-3.0-pro-preview"
        )
        
        # Mock the model and chat session
        mock_chat = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "This is a grounded answer."
        # Mock grounding metadata
        mock_candidate = MagicMock()
        mock_candidate.grounding_metadata.grounding_chunks = ["chunk1"]
        mock_response.candidates = [mock_candidate]
        
        mock_chat.send_message.return_value = mock_response
        
        mock_model_instance = MagicMock()
        mock_model_instance.start_chat.return_value = mock_chat
        mock_gen_model.return_value = mock_model_instance
        
        # Action
        response = agent_instance.query("What is the leave policy?")
        
        # Assertions
        self.assertEqual(response, "This is a grounded answer.")
        mock_gen_model.assert_called_with(
            "gemini-3.0-pro-preview",
            tools=unittest.mock.ANY,
            system_instruction=unittest.mock.ANY
        )
        mock_chat.send_message.assert_called_with("What is the leave policy?")
        
        # Verify logging
        # The logger is initialized inside set_up which is called by query
        # We need to dig into the instance's bq_logger
        self.assertTrue(agent_instance.bq_logger is not None)
        agent_instance.bq_logger.log_interaction.assert_called_with(
            "What is the leave policy?", 
            "This is a grounded answer.", 
            reason="Success"
        )

    @patch('hr_agent.agent.vertexai')
    @patch('hr_agent.agent.GenerativeModel')
    @patch('hr_agent.agent.BigQueryLogger')
    @patch('hr_agent.agent.Tool')
    def test_query_ungrounded(self, mock_tool, mock_bq_logger, mock_gen_model, mock_vertexai):
        # Setup
        agent_instance = HRPolicyAgent("p", "l", "ds", "d", "t", "m")
        
        mock_chat = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Some ungrounded answer."
        # Mock NO grounding metadata
        mock_candidate = MagicMock()
        mock_candidate.grounding_metadata.grounding_chunks = [] # Empty list
        mock_candidate.grounding_metadata = MagicMock()
        mock_candidate.grounding_metadata.grounding_chunks = None # or None
        mock_response.candidates = [mock_candidate]
        
        mock_chat.send_message.return_value = mock_response
        
        mock_model_instance = MagicMock()
        mock_model_instance.start_chat.return_value = mock_chat
        mock_gen_model.return_value = mock_model_instance
        
        # Action
        response = agent_instance.query("Fake question")
        
        # Assertions
        # Should return "I don't know" fallback
        self.assertIn("I don't know", response)
        
        # Verify logging
        agent_instance.bq_logger.log_interaction.assert_called_with(
            "Fake question", 
            response, 
            reason="Low Grounding / No Citations"
        )

if __name__ == '__main__':
    unittest.main()
