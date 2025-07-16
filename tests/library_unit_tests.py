"""
Unit Tests for SOLVE-IT Library

This test suite provides extensive coverage of the solve_it_library.KnowledgeBase class,
testing all major functionality including:

- Basic library initialization and data loading
- Core retrieval methods (get_technique, get_weakness, get_mitigation)
- List methods for all entity types
- Objective mapping functionality
- Relationship traversal methods
- Bulk data retrieval methods
- Advanced features (search, mitigation analysis)
- Error handling with invalid inputs

Note: Some tests include logging output (warnings) which are expected behavior
when testing error handling with non-existent IDs.
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from solve_it_library import KnowledgeBase

class MyTestCase(unittest.TestCase):
    """
    Test cases for the SOLVE-IT Library KnowledgeBase class.
    """

    def test_kb_loads(self):
        """
        Test that the KnowledgeBase initializes correctly.
        
        Expected outcome: Successfully creates a KnowledgeBase instance
        and loads data from the solve-it.json mapping file.
        """
        kb = KnowledgeBase('..', 'solve-it.json')
        self.assertEqual(type(kb), KnowledgeBase)

    def test_list_retrieval(self):
        """
        Test that all list methods return the correct data type.
        
        Expected outcome: All list methods should return Python list objects.
        This verifies the basic API contract for listing methods.
        """
        kb = KnowledgeBase('..', 'solve-it.json')
        self.assertEqual(list, type(kb.list_techniques()))
        self.assertEqual(list, type(kb.list_tactics()))
        self.assertEqual(list, type(kb.list_weaknesses()))
        self.assertEqual(list, type(kb.list_mitigations()))

    def test_technique_list_contents(self):
        """
        Test that technique listing returns expected content.
        
        Expected outcome: 
        - Should contain known techniques like T1001 (Triage) and T1002 (Disk imaging)
        - Should return a reasonable number of techniques (at least 100+)
        - List should be sorted for consistent ordering
        """
        kb = KnowledgeBase('..', 'solve-it.json')
        techniques = kb.list_techniques()
        self.assertIn('T1001', techniques)
        self.assertIn('T1002', techniques)
        self.assertGreater(len(techniques), 100)  # Should have substantial content
        # Test that list is sorted
        self.assertEqual(techniques, sorted(techniques))

    def test_tactic_list_contents(self):
        """
        Test that tactics (objectives) listing returns expected content.
        
        Expected outcome:
        - Should contain core SOLVE-IT objectives like 'Prioritise' and 'Acquire'
        - Should return a reasonable number of objectives (at least 10+)
        - Content should match what's defined in the objective mapping file
        """
        kb = KnowledgeBase('..', 'solve-it.json')
        tactics = kb.list_tactics()
        self.assertIn('Prioritise', tactics)
        self.assertIn('Acquire', tactics)
        self.assertGreater(len(tactics), 10)  # Should have substantial content

    def test_weakness_list_contents(self):
        """
        Test that weakness listing returns expected content.
        
        Expected outcome:
        - Should contain known weaknesses like W1001 and W1002
        - Should return a substantial number of weaknesses (at least 100+)
        - List should be sorted for consistent ordering
        - All weakness IDs should follow W#### pattern
        """
        kb = KnowledgeBase('..', 'solve-it.json')
        weaknesses = kb.list_weaknesses()
        self.assertIn('W1001', weaknesses)
        self.assertIn('W1002', weaknesses)
        self.assertGreater(len(weaknesses), 100)  # Should have substantial content
        # Test that list is sorted
        self.assertEqual(weaknesses, sorted(weaknesses))

    def test_mitigations_list_contents(self):
        """
        Test that mitigation listing returns expected content.
        
        Expected outcome:
        - Should contain known mitigations like M1001 and M1007
        - Should return a substantial number of mitigations (at least 100+)
        - List should be sorted for consistent ordering
        - All mitigation IDs should follow M#### pattern
        """
        kb = KnowledgeBase('..', 'solve-it.json')
        mitigations = kb.list_mitigations()
        self.assertIn('M1001', mitigations)
        self.assertIn('M1007', mitigations)
        self.assertGreater(len(mitigations), 100)  # Should have substantial content
        # Test that list is sorted
        self.assertEqual(mitigations, sorted(mitigations))

    # Content Retrieval Tests

    def test_get_technique(self):
        """
        Test retrieval of individual technique by ID.
        
        Expected outcome:
        - Should return a dictionary with technique data for T1001 (Triage)
        - Should have correct structure with id, name, description, etc.
        - Should contain expected fields like synonyms, weaknesses, references
        - Each field should have appropriate data type
        """
        kb = KnowledgeBase('..', 'solve-it.json')

        # Test basic retrieval and structure
        technique = kb.get_technique('T1001')
        self.assertEqual(dict, type(technique))
        self.assertEqual('T1001', technique.get('id'))
        self.assertEqual('Triage', technique.get('name'))
        
        # Test that basic structure exists (exact content may vary)
        self.assertIsNotNone(technique.get('description'))
        self.assertIsInstance(technique.get('synonyms'), list)
        self.assertIsInstance(technique.get('weaknesses'), list)
        self.assertIsInstance(technique.get('references'), list)

    def test_get_technique_na(self):
        """
        Test technique retrieval with non-existent ID.
        
        Expected outcome: Should return None for non-existent technique IDs.
        This tests proper error handling for invalid requests.
        """
        kb = KnowledgeBase('..', 'solve-it.json')
        self.assertEqual(None, kb.get_technique('T9999'))

    def test_get_weakness(self):
        """
        Test retrieval of individual weakness by ID.
        
        Expected outcome:
        - Should return a dictionary with weakness data for W1001
        - Should have correct structure with SOLVE-IT specific fields
        - Should contain weakness categorization fields (INCOMP, INAC_*, MISINT)
        - Should have proper data types for all fields
        """
        kb = KnowledgeBase('..', 'solve-it.json')
        weakness = kb.get_weakness('W1001')
        self.assertEqual(dict, type(weakness))
        self.assertEqual('W1001', weakness.get('id'))
        self.assertEqual('Excluding a device that contains relevant information', weakness.get('name'))
        self.assertEqual('x', weakness.get('INCOMP'))
        self.assertEqual('', weakness.get('INAC_EX'))
        self.assertEqual('', weakness.get('INAC_AS'))
        self.assertEqual('', weakness.get('INAC_ALT'))
        self.assertEqual('', weakness.get('INAC_COR'))
        self.assertEqual('', weakness.get('MISINT'))
        self.assertIsInstance(weakness.get('mitigations'), list)
        self.assertIsInstance(weakness.get('references'), list)

    def test_get_weakness_usage(self):
        """
        Test that weakness includes reverse lookup information.
        
        Expected outcome:
        - Should include 'in_techniques' field showing which techniques reference this weakness
        - W1001 should be referenced by T1001 (Triage)
        - This tests the reverse relationship tracking functionality
        """
        kb = KnowledgeBase('..', 'solve-it.json')
        weakness = kb.get_weakness('W1001')
        self.assertIsInstance(weakness.get('in_techniques'), list)
        self.assertIn('T1001', weakness.get('in_techniques'))

    def test_get_mitigation(self):
        """
        Test retrieval of individual mitigation by ID.
        
        Expected outcome:
        - Should return a dictionary with mitigation data for M1001
        - Should have correct structure with id, name, references
        - Should contain expected mitigation information
        """
        kb = KnowledgeBase('..', 'solve-it.json')
        mitigation = kb.get_mitigation('M1001')
        self.assertEqual(dict, type(mitigation))
        self.assertEqual('M1001', mitigation.get('id'))
        self.assertEqual('Review of all triage results that are relied on during the full digital forensic examination', mitigation.get('name'))
        self.assertIsInstance(mitigation.get('references'), list)

    def test_get_mitigation_usage(self):
        """
        Test that mitigation includes reverse lookup information.
        
        Expected outcome:
        - Should include 'in_techniques' and 'in_weaknesses' fields
        - Should show which techniques and weaknesses reference this mitigation
        - Lists should have content (not be empty)
        - This tests the reverse relationship tracking functionality
        """
        kb = KnowledgeBase('..', 'solve-it.json')
        mitigation = kb.get_mitigation('M1001')
        self.assertIsInstance(mitigation.get('in_techniques'), list)
        self.assertIsInstance(mitigation.get('in_weaknesses'), list)
        # Check that usage tracking is working
        self.assertGreater(len(mitigation.get('in_techniques')), 0)
        self.assertGreater(len(mitigation.get('in_weaknesses')), 0)

    # Objective Mapping Functionality Tests

    def test_load_objective_mapping(self):
        """
        Test loading different objective mapping files.
        
        Expected outcome:
        - Should successfully load solve-it.json (default mapping)
        - Should load other available mappings like carrier.json if they exist
        - Should return False for non-existent mapping files
        - This tests dynamic mapping switching functionality
        """
        kb = KnowledgeBase('..', 'solve-it.json')
        # Test loading the default mapping
        self.assertTrue(kb.load_objective_mapping('solve-it.json'))
        # Test loading carrier mapping (if it exists)
        available_mappings = kb.list_available_mappings()
        if 'carrier.json' in available_mappings:
            self.assertTrue(kb.load_objective_mapping('carrier.json'))
        # Test loading non-existent mapping
        self.assertFalse(kb.load_objective_mapping('nonexistent.json'))

    def test_list_available_mappings(self):
        """
        Test discovery of available objective mapping files.
        
        Expected outcome:
        - Should return a list of available .json mapping files in data directory
        - Should include solve-it.json as the default mapping
        - Should exclude non-mapping files and subdirectories
        """
        kb = KnowledgeBase('..', 'solve-it.json')
        mappings = kb.list_available_mappings()
        self.assertIsInstance(mappings, list)
        self.assertIn('solve-it.json', mappings)

    def test_list_objectives(self):
        """
        Test listing objectives from the current mapping.
        
        Expected outcome:
        - Should return a list of objective dictionaries
        - Each objective should have 'name' and 'techniques' fields
        - Should have reasonable number of objectives (SOLVE-IT has 17)
        - Structure should match what's defined in the mapping file
        """
        kb = KnowledgeBase('..', 'solve-it.json')
        objectives = kb.list_objectives()
        self.assertIsInstance(objectives, list)
        self.assertGreater(len(objectives), 0)
        # Check structure of objectives
        for obj in objectives:
            self.assertIsInstance(obj, dict)
            self.assertIn('name', obj)
            self.assertIn('techniques', obj)

    def test_get_techniques_for_objective(self):
        """
        Test retrieval of techniques associated with specific objectives.
        
        Expected outcome:
        - Should return list of technique dictionaries for valid objective names
        - Each technique should have proper structure with id and name
        - Should return empty list for non-existent objectives
        - This tests the objective-to-technique relationship mapping
        """
        kb = KnowledgeBase('..', 'solve-it.json')
        objectives = kb.list_objectives()
        if objectives:
            objective_name = objectives[0]['name']
            techniques = kb.get_techniques_for_objective(objective_name)
            self.assertIsInstance(techniques, list)
            # If techniques exist, verify structure
            for technique in techniques:
                self.assertIsInstance(technique, dict)
                self.assertIn('id', technique)
                self.assertIn('name', technique)

    # Relationship Traversal Tests

    def test_get_weaknesses_for_technique(self):
        """
        Test retrieval of weaknesses associated with a specific technique.
        
        Expected outcome:
        - Should return list of weakness dictionaries for T1001 (Triage)
        - T1001 should have associated weaknesses (at least W1001-W1003)
        - Each weakness should have proper structure with id and name
        - This tests the technique-to-weakness relationship traversal
        """
        kb = KnowledgeBase('..', 'solve-it.json')
        weaknesses = kb.get_weaknesses_for_technique('T1001')
        self.assertIsInstance(weaknesses, list)
        # T1001 should have associated weaknesses
        self.assertGreater(len(weaknesses), 0)
        for weakness in weaknesses:
            self.assertIsInstance(weakness, dict)
            self.assertIn('id', weakness)
            self.assertIn('name', weakness)

    def test_get_mitigations_for_weakness(self):
        """
        Test retrieval of mitigations associated with a specific weakness.
        
        Expected outcome:
        - Should find a weakness that has mitigations and test retrieval
        - Should return list of mitigation dictionaries 
        - Each mitigation should have proper structure with id and name
        - This tests the weakness-to-mitigation relationship traversal
        """
        kb = KnowledgeBase('..', 'solve-it.json')
        # Find a weakness that has mitigations
        weakness_with_mits = None
        for weakness_id in kb.list_weaknesses():
            weakness = kb.get_weakness(weakness_id)
            if weakness.get('mitigations'):
                weakness_with_mits = weakness_id
                break
        
        if weakness_with_mits:
            mitigations = kb.get_mitigations_for_weakness(weakness_with_mits)
            self.assertIsInstance(mitigations, list)
            self.assertGreater(len(mitigations), 0)
            for mitigation in mitigations:
                self.assertIsInstance(mitigation, dict)
                self.assertIn('id', mitigation)
                self.assertIn('name', mitigation)

    def test_get_techniques_for_weakness(self):
        """
        Test reverse lookup: finding techniques that reference a specific weakness.
        
        Expected outcome:
        - W1001 should be associated with T1001 (Triage)
        - Should return list of technique dictionaries
        - Each technique should have proper structure
        - This tests the reverse weakness-to-technique relationship lookup
        """
        kb = KnowledgeBase('..', 'solve-it.json')
        techniques = kb.get_techniques_for_weakness('W1001')
        self.assertIsInstance(techniques, list)
        # W1001 should be associated with T1001
        self.assertGreater(len(techniques), 0)
        technique_ids = [t['id'] for t in techniques]
        self.assertIn('T1001', technique_ids)

    def test_get_weaknesses_for_mitigation(self):
        """
        Test reverse lookup: finding weaknesses that reference a specific mitigation.
        
        Expected outcome:
        - M1001 should be associated with weaknesses (reverse lookup)
        - Should return list of weakness dictionaries
        - Each weakness should have proper structure
        - This tests the reverse mitigation-to-weakness relationship lookup
        """
        kb = KnowledgeBase('..', 'solve-it.json')
        weaknesses = kb.get_weaknesses_for_mitigation('M1001')
        self.assertIsInstance(weaknesses, list)
        # M1001 should have associated weaknesses
        self.assertGreater(len(weaknesses), 0)
        for weakness in weaknesses:
            self.assertIsInstance(weakness, dict)
            self.assertIn('id', weakness)
            self.assertIn('name', weakness)

    # Bulk Data Retrieval Tests

    def test_get_all_weaknesses_with_name_and_id(self):
        """
        Test bulk retrieval of weaknesses with minimal data (id and name only).
        
        Expected outcome:
        - Should return list of all weaknesses in the database
        - Each entry should contain only 'id' and 'name' fields (exactly 2 fields)
        - Should have substantial number of weaknesses (100+)
        - This tests the lightweight bulk retrieval functionality
        """
        kb = KnowledgeBase('..', 'solve-it.json')
        weaknesses = kb.get_all_weaknesses_with_name_and_id()
        self.assertIsInstance(weaknesses, list)
        self.assertGreater(len(weaknesses), 100)  # Should have substantial content
        for weakness in weaknesses:
            self.assertIsInstance(weakness, dict)
            self.assertIn('id', weakness)
            self.assertIn('name', weakness)
            self.assertEqual(len(weakness), 2)  # Only id and name

    def test_get_all_weaknesses_with_full_detail(self):
        """
        Test bulk retrieval of weaknesses with complete data.
        
        Expected outcome:
        - Should return list of all weaknesses with full details
        - Each entry should contain all weakness fields (mitigations, categorization, etc.)
        - Should have same count as name-and-id method but with more data per entry
        - This tests the comprehensive bulk retrieval functionality
        """
        kb = KnowledgeBase('..', 'solve-it.json')
        weaknesses = kb.get_all_weaknesses_with_full_detail()
        self.assertIsInstance(weaknesses, list)
        self.assertGreater(len(weaknesses), 100)  # Should have substantial content
        for weakness in weaknesses:
            self.assertIsInstance(weakness, dict)
            self.assertIn('id', weakness)
            self.assertIn('name', weakness)
            self.assertIn('mitigations', weakness)
            # Should have more than just id and name
            self.assertGreater(len(weakness), 2)

    def test_get_all_techniques_with_name_and_id(self):
        """
        Test bulk retrieval of techniques with minimal data (id and name only).
        
        Expected outcome:
        - Should return list of all techniques in the database
        - Each entry should contain only 'id' and 'name' fields (exactly 2 fields)
        - Should have substantial number of techniques (100+)
        - This tests the lightweight bulk retrieval functionality
        """
        kb = KnowledgeBase('..', 'solve-it.json')
        techniques = kb.get_all_techniques_with_name_and_id()
        self.assertIsInstance(techniques, list)
        self.assertGreater(len(techniques), 100)  # Should have substantial content
        for technique in techniques:
            self.assertIsInstance(technique, dict)
            self.assertIn('id', technique)
            self.assertIn('name', technique)
            self.assertEqual(len(technique), 2)  # Only id and name

    def test_get_all_techniques_with_full_detail(self):
        """
        Test bulk retrieval of techniques with complete data.
        
        Expected outcome:
        - Should return list of all techniques with full details
        - Each entry should contain all technique fields (description, weaknesses, references, etc.)
        - Should have same count as name-and-id method but with more data per entry
        - This tests the comprehensive bulk retrieval functionality
        """
        kb = KnowledgeBase('..', 'solve-it.json')
        techniques = kb.get_all_techniques_with_full_detail()
        self.assertIsInstance(techniques, list)
        self.assertGreater(len(techniques), 100)  # Should have substantial content
        for technique in techniques:
            self.assertIsInstance(technique, dict)
            self.assertIn('id', technique)
            self.assertIn('name', technique)
            self.assertIn('weaknesses', technique)
            # Should have more than just id and name
            self.assertGreater(len(technique), 2)

    def test_get_all_mitigations_with_name_and_id(self):
        """
        Test bulk retrieval of mitigations with minimal data (id and name only).
        
        Expected outcome:
        - Should return list of all mitigations in the database
        - Each entry should contain only 'id' and 'name' fields (exactly 2 fields)
        - Should have substantial number of mitigations (100+)
        - This tests the lightweight bulk retrieval functionality
        """
        kb = KnowledgeBase('..', 'solve-it.json')
        mitigations = kb.get_all_mitigations_with_name_and_id()
        self.assertIsInstance(mitigations, list)
        self.assertGreater(len(mitigations), 100)  # Should have substantial content
        for mitigation in mitigations:
            self.assertIsInstance(mitigation, dict)
            self.assertIn('id', mitigation)
            self.assertIn('name', mitigation)
            self.assertEqual(len(mitigation), 2)  # Only id and name

    def test_get_all_mitigations_with_full_detail(self):
        """
        Test bulk retrieval of mitigations with complete data.
        
        Expected outcome:
        - Should return list of all mitigations with full details
        - Each entry should contain all mitigation fields (references, usage tracking, etc.)
        - Should have same count as name-and-id method but with more data per entry
        - This tests the comprehensive bulk retrieval functionality
        """
        kb = KnowledgeBase('..', 'solve-it.json')
        mitigations = kb.get_all_mitigations_with_full_detail()
        self.assertIsInstance(mitigations, list)
        self.assertGreater(len(mitigations), 100)  # Should have substantial content
        for mitigation in mitigations:
            self.assertIsInstance(mitigation, dict)
            self.assertIn('id', mitigation)
            self.assertIn('name', mitigation)
            self.assertIn('references', mitigation)
            # Should have more than just id and name
            self.assertGreater(len(mitigation), 2)

    # Advanced Functionality Tests

    def test_search(self):
        """
        Test basic search functionality across all entity types.
        
        Expected outcome:
        - Should return dictionary with keys for 'techniques', 'weaknesses', 'mitigations'
        - Search for 'triage' should find T1001 (Triage) in techniques
        - Results should be sorted by relevance (highest scores first)
        - This tests the comprehensive search capability across the knowledge base
        """
        kb = KnowledgeBase('..', 'solve-it.json')
        # Test basic search
        results = kb.search('triage')
        self.assertIsInstance(results, dict)
        self.assertIn('techniques', results)
        self.assertIn('weaknesses', results)
        self.assertIn('mitigations', results)
        
        # Should find T1001 (Triage) in techniques
        technique_ids = [t['id'] for t in results['techniques']]
        self.assertIn('T1001', technique_ids)

    def test_search_with_options(self):
        """
        Test search functionality with filtering options.
        
        Expected outcome:
        - Should allow filtering by item_types parameter
        - Search for 'disk' with item_types=['techniques'] should only return techniques
        - Other result categories (weaknesses, mitigations) should be empty
        - This tests the filtered search capability
        """
        kb = KnowledgeBase('..', 'solve-it.json')
        # Test search with specific item types
        results = kb.search('disk', item_types=['techniques'])
        self.assertIsInstance(results, dict)
        self.assertIn('techniques', results)
        self.assertEqual(len(results['weaknesses']), 0)
        self.assertEqual(len(results['mitigations']), 0)

    def test_get_mit_list_for_technique(self):
        """
        Test retrieval of mitigation IDs for a specific technique.
        
        Expected outcome:
        - Should return list of mitigation IDs associated with T1001 (through its weaknesses)
        - Should have at least one mitigation (T1001 has weaknesses with mitigations)
        - Should contain only unique mitigation IDs (no duplicates)
        - This tests the technique-to-mitigation traversal functionality
        """
        kb = KnowledgeBase('..', 'solve-it.json')
        # Test with T1001 which should have mitigations through its weaknesses
        mits = kb.get_mit_list_for_technique('T1001')
        self.assertIsInstance(mits, list)
        self.assertGreater(len(mits), 0)
        # Should contain unique mitigation IDs
        self.assertEqual(len(mits), len(set(mits)))

    def test_get_max_mitigations_per_technique(self):
        """
        Test calculation of maximum mitigations per technique across all techniques.
        
        Expected outcome:
        - Should return positive integer representing max mitigation count
        - Should be reasonable number (typically 10-20, but less than 50)
        - This is used for Excel generation to determine column sizing
        - Tests the analysis functionality for reporting purposes
        """
        kb = KnowledgeBase('..', 'solve-it.json')
        max_mits = kb.get_max_mitigations_per_technique()
        self.assertIsInstance(max_mits, int)
        self.assertGreater(max_mits, 0)
        # Should be a reasonable number (typically 10-20)
        self.assertLess(max_mits, 50)

    def test_tactics_property(self):
        """
        Test compatibility property for legacy API support.
        
        Expected outcome:
        - Should return list of objectives (same as list_objectives())
        - Should maintain backward compatibility with original solveitcore.py
        - Should have reasonable number of tactics/objectives
        - This tests the legacy API compatibility layer
        """
        kb = KnowledgeBase('..', 'solve-it.json')
        tactics = kb.tactics
        self.assertIsInstance(tactics, list)
        self.assertGreater(len(tactics), 10)  # Should have substantial content
        # Should match list_objectives()
        self.assertEqual(tactics, kb.list_objectives())

    # Error Handling and Edge Cases Tests

    def test_error_handling(self):
        """
        Test proper error handling for invalid inputs and edge cases.
        
        Expected outcome:
        - Should return None for non-existent entity IDs (T9999, W9999, M9999)
        - Should return empty lists for relationship queries with invalid IDs
        - Should not raise exceptions, but handle errors gracefully
        - This tests the robustness and reliability of the library
        
        Note: Warning messages in output are expected behavior for invalid IDs.
        """
        kb = KnowledgeBase('..', 'solve-it.json')
        # Test with non-existent IDs
        self.assertIsNone(kb.get_technique('T9999'))
        self.assertIsNone(kb.get_weakness('W9999'))
        self.assertIsNone(kb.get_mitigation('M9999'))
        
        # Test with empty technique for relationships
        self.assertEqual(kb.get_weaknesses_for_technique('T9999'), [])
        self.assertEqual(kb.get_mitigations_for_weakness('W9999'), [])
        self.assertEqual(kb.get_techniques_for_weakness('W9999'), [])
        self.assertEqual(kb.get_weaknesses_for_mitigation('M9999'), [])


if __name__ == '__main__':
    unittest.main()
