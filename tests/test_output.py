"""Unit tests for the output module."""

import unittest
from unittest.mock import patch, Mock, mock_open
import os
import tempfile
import json
from output import save_to_json, save_to_csv, save_to_excel, generate_all_outputs


class TestOutput(unittest.TestCase):
    """Test cases for output functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_data = [
            {
                'name': 'test-repo-1',
                'description': 'Test repository 1',
                'language': 'Python',
                'stargazers_count': 10,
                'forks_count': 5,
                'open_prs': 2,
                'closed_prs': 8,
                'contributors_count': 3,
                'quality_score': 85
            },
            {
                'name': 'test-repo-2',
                'description': 'Test repository 2',
                'language': 'JavaScript',
                'stargazers_count': 25,
                'forks_count': 12,
                'open_prs': 5,
                'closed_prs': 15,
                'contributors_count': 7,
                'quality_score': 92
            }
        ]

    def test_save_to_json(self):
        """Test saving data to JSON file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            filename = os.path.join(temp_dir, "test_output.json")
            save_to_json(self.sample_data, filename)
            
            # Verify file was created and contains correct data
            self.assertTrue(os.path.exists(filename))
            with open(filename, 'r') as f:
                loaded_data = json.load(f)
            
            self.assertEqual(len(loaded_data), 2)
            self.assertEqual(loaded_data[0]['name'], 'test-repo-1')

    @patch('output.pd.DataFrame.to_csv')
    def test_save_to_csv(self, mock_to_csv):
        """Test saving data to CSV file."""
        filename = "test_output.csv"
        save_to_csv(self.sample_data, filename)
        
        mock_to_csv.assert_called_once_with(filename, index=False)

    @patch('output.pd.DataFrame.to_excel')
    @patch('output.openpyxl.load_workbook')
    def test_save_to_excel(self, mock_load_workbook, mock_to_excel):
        """Test saving data to Excel file."""
        # Mock workbook and worksheet
        mock_workbook = Mock()
        mock_worksheet = Mock()
        mock_workbook.active = mock_worksheet
        mock_load_workbook.return_value = mock_workbook
        
        filename = "test_output.xlsx"
        save_to_excel(self.sample_data, filename)
        
        mock_to_excel.assert_called_once()
        mock_load_workbook.assert_called_once_with(filename)
        mock_workbook.save.assert_called_once_with(filename)

    @patch('output.save_to_json')
    @patch('output.save_to_csv')
    @patch('output.save_to_excel')
    @patch('builtins.print')
    def test_generate_all_outputs(self, mock_print, mock_excel, mock_csv, mock_json):
        """Test generating all output formats."""
        base_filename = "test_output"
        output_dir = "/tmp"
        
        generate_all_outputs(self.sample_data, base_filename, output_dir)
        
        # Verify all three formats were called
        mock_json.assert_called_once_with(
            self.sample_data, 
            os.path.join(output_dir, f"{base_filename}.json")
        )
        mock_csv.assert_called_once_with(
            self.sample_data, 
            os.path.join(output_dir, f"{base_filename}.csv")
        )
        mock_excel.assert_called_once_with(
            self.sample_data, 
            os.path.join(output_dir, f"{base_filename}.xlsx")
        )
        
        # Verify print statements
        self.assertEqual(mock_print.call_count, 3)


if __name__ == '__main__':
    unittest.main()
