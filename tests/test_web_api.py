import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.agent import run_agent
from api.app import create_app


class WebApiTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_health_endpoint(self):
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['status'], 'ok')

    def test_chat_endpoint_returns_agent_response(self):
        with patch('api.service.run_agent', return_value='Assistant reply'):
            response = self.client.post('/api/chat', json={'message': 'hello there'})
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['data']['response'], 'Assistant reply')
        self.assertTrue(payload['data']['history'])

    def test_research_endpoint_returns_sources(self):
        with patch('api.service.research_and_synthesize') as mock_research:
            mock_research.return_value = type(
                'Result',
                (),
                {
                    'success': True,
                    'result': {
                        'answer': 'AI writing is improving quickly.',
                        'sources': [
                            {'title': 'AI Brief', 'url': 'https://example.com/ai-brief'},
                            {'title': 'Tech Journal', 'url': 'https://example.com/tech-journal'},
                        ],
                    },
                    'error': None,
                },
            )()
            response = self.client.post('/api/research', json={'query': 'latest AI progress'})

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload['success'])
        self.assertIn('AI Brief', payload['data']['sources'][0]['title'])
        self.assertIn('https://example.com/ai-brief', payload['data']['sources'][0]['url'])

    def test_upload_rejects_invalid_extension(self):
        dummy = io.BytesIO(b'hello world')
        response = self.client.post(
            '/api/upload',
            data={'file': (dummy, 'notes.exe')},
            content_type='multipart/form-data',
        )
        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertFalse(payload['success'])

    def test_job_analysis_validation(self):
        response = self.client.post('/api/job-analysis', json={'job_text': ''})
        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertFalse(payload['success'])

    def test_agent_integration_calculator_path(self):
        result = run_agent('What is 2 + 2?')
        self.assertIn('4', result)

    def test_report_endpoint_lists_saved_reports(self):
        with patch('api.app.list_reports', return_value=[{'name': 'sample-report.md', 'path': 'sample-report.md'}]):
            response = self.client.get('/api/reports')
            self.assertEqual(response.status_code, 200)
            payload = response.get_json()
            self.assertTrue(payload['success'])
            self.assertEqual(payload['reports'][0]['name'], 'sample-report.md')


if __name__ == '__main__':
    unittest.main()
