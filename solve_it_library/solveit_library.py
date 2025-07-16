"""
Core module for the SOLVE-IT Knowledge Base Library.

Defines the KnowledgeBase class responsible for loading and providing
access to the SOLVE-IT data (techniques, weaknesses, mitigations).
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Type, Union, Tuple
from pydantic import ValidationError

from .models import (
    Technique, Weakness, Mitigation, Objective,
    TechniqueValidationError, WeaknessValidationError, MitigationValidationError, ObjectiveValidationError,
    ErrorCodes
)

# Set up basic logging for the library
logger = logging.getLogger(__name__)
# Configure logging level (optional, could be configured by application)
# logging.basicConfig(level=logging.INFO)

class KnowledgeBase:
    """
    Provides an interface to load and query the SOLVE-IT knowledge base.

    Attributes:
        base_path (str): The root path of the solve-it repository clone.
        data_path (str): Path to the 'data' directory.
        techniques_path (str): Path to the 'techniques' directory.
        weaknesses_path (str): Path to the 'weaknesses' directory.
        mitigations_path (str): Path to the 'mitigations' directory.
        techniques (Dict[str, Dict[str, Any]]): Dictionary of loaded techniques, keyed by ID.
        weaknesses (Dict[str, Dict[str, Any]]): Dictionary of loaded weaknesses, keyed by ID.
        mitigations (Dict[str, Dict[str, Any]]): Dictionary of loaded mitigations, keyed by ID.
        objective_mappings (Dict[str, List[Dict[str, Any]]]): Dictionary storing loaded
            objective mappings, keyed by mapping filename (e.g., "solve-it.json").
        current_mapping_name (Optional[str]): The name of the currently active objective
            mapping file.
    """
    DEFAULT_MAPPING_FILE = "solve-it.json"

    def __init__(self, base_path: str, mapping_file: str = DEFAULT_MAPPING_FILE):
        """
        Initializes the KnowledgeBase by loading data from the specified path.

        Args:
            base_path (str): The path to the root directory of the solve-it
                repository clone (containing the 'data' folder).

        Raises:
            FileNotFoundError: If the base_path or essential subdirectories
                               (data, techniques, weaknesses, mitigations) do not exist.
        """
        if not os.path.isdir(base_path):
            raise FileNotFoundError(f"Base path not found: {base_path}")

        self.base_path: str = base_path
        # Path to the data directory
        self.data_path: str = os.path.join(self.base_path, 'data')
        self.techniques_path: str = os.path.join(self.data_path, 'techniques')
        self.weaknesses_path: str = os.path.join(self.data_path, 'weaknesses')
        self.mitigations_path: str = os.path.join(self.data_path, 'mitigations')

        # Validate essential paths
        for path in [self.data_path, self.techniques_path, self.weaknesses_path, self.mitigations_path]:
            if not os.path.isdir(path):
                raise FileNotFoundError(f"Required directory not found: {path}")

        # Initialize data storage
        self.techniques: Dict[str, Dict[str, Any]] = {}
        self.weaknesses: Dict[str, Dict[str, Any]] = {}
        self.mitigations: Dict[str, Dict[str, Any]] = {}
        self.objective_mappings: Dict[str, List[Dict[str, Any]]] = {}
        self.current_mapping_name: Optional[str] = None

        # Initialize reverse lookup indices for O(1) performance
        self._weakness_to_techniques: Dict[str, List[str]] = {}
        self._mitigation_to_weaknesses: Dict[str, List[str]] = {}
        self._mitigation_to_techniques: Dict[str, List[str]] = {}

        # Load core data
        self._load_techniques()
        self._load_weaknesses()
        self._load_mitigations()
        
        # Build reverse indices for performance optimization
        self._build_reverse_indices()

        # Load the specified objective mapping
        if not self.load_objective_mapping(mapping_file):
            # Optionally load the default if the specified one failed
            logger.warning(
                "Could not load specified mapping '%s'. Attempting default.",
                mapping_file
            )
            if not self.load_objective_mapping(self.DEFAULT_MAPPING_FILE):
                logger.warning(
                    "Could not load default mapping '%s'. No objective mapping active.",
                    self.DEFAULT_MAPPING_FILE
                )

    def _load_json_files(self, directory_path: str, model_class: Type[Union[Technique, Weakness, Mitigation]]) -> Dict[str, Dict[str, Any]]:
        """
        Loads all JSON files from a specified directory and validates them against a Pydantic model.

        Args:
            directory_path (str): The path to the directory containing JSON files.
            model_class (Type): The Pydantic model class to validate the data against.

        Returns:
            Dict[str, Dict[str, Any]]: A dictionary where keys are the item IDs
                (extracted from JSON 'id' field) and values are the loaded JSON data.

        Logs:
            Warning if a directory is not found.
            Warning if a JSON file is missing the 'id' field.
            Error if a JSON file cannot be decoded.
            Error if a file cannot be read due to IO issues.
            Error if a JSON file fails validation against the model.
        """
        loaded_data: Dict[str, Dict[str, Any]] = {}
        if not os.path.isdir(directory_path):
            logger.warning("Directory not found, skipping load: %s", directory_path)
            return loaded_data

        for filename in os.listdir(directory_path):
            if filename.lower().endswith('.json'):
                file_path = os.path.join(directory_path, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        # Validate the data against the model
                        try:
                            validated_data = model_class.model_validate(data)
                            item_id = validated_data.id
                            # Convert back to dict for compatibility with existing code
                            loaded_data[item_id] = validated_data.model_dump()
                        except ValidationError as e:
                            # Determine the appropriate exception type based on the model class
                            if model_class == Technique:
                                error_class = TechniqueValidationError
                            elif model_class == Weakness:
                                error_class = WeaknessValidationError
                            elif model_class == Mitigation:
                                error_class = MitigationValidationError
                            else:
                                error_class = Exception
                            
                            # Log the validation error with details
                            logger.error(
                                "Validation error in %s: %s",
                                file_path,
                                e.errors()
                            )
                            
                            # Skip this file and continue with the next one
                            continue
                        
                except json.JSONDecodeError as e:
                    logger.error("Could not decode JSON from %s: %s", file_path, e)
                except IOError as e:
                    logger.error("Could not read file %s: %s", file_path, e)
                except Exception as e:
                    logger.error("Unexpected error processing %s: %s", file_path, e)
        
        return loaded_data

    def _load_techniques(self):
        """Loads techniques from the techniques directory."""
        self.techniques = self._load_json_files(self.techniques_path, Technique)
        logger.info("Loaded %d techniques.", len(self.techniques))

    def _load_weaknesses(self):
        """Loads weaknesses from the weaknesses directory."""
        self.weaknesses = self._load_json_files(self.weaknesses_path, Weakness)
        logger.info("Loaded %d weaknesses.", len(self.weaknesses))

    def _load_mitigations(self):
        """Loads mitigations from the mitigations directory."""
        self.mitigations = self._load_json_files(self.mitigations_path, Mitigation)
        logger.info("Loaded %d mitigations.", len(self.mitigations))

    def _build_reverse_indices(self):
        """
        Pre-compute reverse relationship indices for O(1) lookups.
        
        Builds:
        - weakness_id -> [technique_ids] that reference it
        - mitigation_id -> [weakness_ids] that reference it  
        - mitigation_id -> [technique_ids] that reference it (through weaknesses)
        
        This eliminates the need for O(n) iterations in relationship query methods.
        """
        logger.info("Building reverse indices for performance optimization...")
        
        # Initialize empty indices
        self._weakness_to_techniques = {}
        self._mitigation_to_weaknesses = {}
        self._mitigation_to_techniques = {}
        
        # Build weakness -> techniques mapping
        for technique_id, technique in self.techniques.items():
            for weakness_id in technique.get('weaknesses', []):
                if weakness_id not in self._weakness_to_techniques:
                    self._weakness_to_techniques[weakness_id] = []
                self._weakness_to_techniques[weakness_id].append(technique_id)
        
        # Build mitigation -> weaknesses mapping
        for weakness_id, weakness in self.weaknesses.items():
            for mitigation_id in weakness.get('mitigations', []):
                if mitigation_id not in self._mitigation_to_weaknesses:
                    self._mitigation_to_weaknesses[mitigation_id] = []
                self._mitigation_to_weaknesses[mitigation_id].append(weakness_id)
        
        # Build mitigation -> techniques mapping (through weaknesses)
        for mitigation_id, weakness_ids in self._mitigation_to_weaknesses.items():
            technique_ids = set()  # Use set to avoid duplicates
            for weakness_id in weakness_ids:
                technique_ids.update(self._weakness_to_techniques.get(weakness_id, []))
            self._mitigation_to_techniques[mitigation_id] = sorted(list(technique_ids))
        
        # Sort all reverse index lists for consistent output
        for weakness_id in self._weakness_to_techniques:
            self._weakness_to_techniques[weakness_id].sort()
        
        for mitigation_id in self._mitigation_to_weaknesses:
            self._mitigation_to_weaknesses[mitigation_id].sort()
        
        logger.info("Reverse indices built: %d weakness->technique, %d mitigation->weakness, %d mitigation->technique",
                    len(self._weakness_to_techniques), 
                    len(self._mitigation_to_weaknesses),
                    len(self._mitigation_to_techniques))

    def load_objective_mapping(self, mapping_filename: str) -> bool:
        """
        Loads a specific objective mapping file (e.g., "solve-it.json") from the data directory.

        Args:
            mapping_filename (str): The filename of the objective mapping JSON file.

        Returns:
            bool: True if the mapping was loaded successfully, False otherwise.
        """
        mapping_path = os.path.join(self.data_path, mapping_filename)
        if not os.path.isfile(mapping_path):
            logger.error("Objective mapping file not found: %s", mapping_path)
            return False

        try:
            with open(mapping_path, 'r', encoding='utf-8') as f:
                mapping_data = json.load(f)
                if isinstance(mapping_data, list):
                    # Validate each objective in the mapping
                    validated_objectives = []
                    for i, obj in enumerate(mapping_data):
                        try:
                            validated_obj = Objective.model_validate(obj)
                            validated_objectives.append(validated_obj.model_dump())
                        except ValidationError as e:
                            logger.error(
                                "Validation error in objective %d of mapping '%s': %s",
                                i,
                                mapping_filename,
                                e.errors()
                            )
                            # Continue with the next objective
                            continue
                    
                    # Store the validated objectives
                    self.objective_mappings[mapping_filename] = validated_objectives
                    self.current_mapping_name = mapping_filename
                    
                    # Log success message with mapping details
                    logger.info(
                        "Loaded objective mapping '%s' with %d objectives.",
                        mapping_filename,
                        len(validated_objectives)
                    )
                    return True

                logger.error(
                    "Objective mapping file '%s' does not contain a list.",
                    mapping_filename
                )
                return False
        except json.JSONDecodeError as e:
            logger.error("Could not decode JSON from %s: %s", mapping_path, e)
            return False
        except IOError as e:
            logger.error("Could not read file %s: %s", mapping_path, e)
            return False
        except Exception as e:
            logger.error("Unexpected error loading mapping '%s': %s", mapping_filename, e)
            return False

    # --- Public Query Methods ---

    def list_available_mappings(self) -> List[str]:
        """
        Lists the filenames of potential objective mapping JSON files found
        directly within the 'data' directory.

        Returns:
            List[str]: A list of filenames (e.g., ["solve-it.json", "carrier.json"]).
        """
        mapping_files = []
        excluded_dirs = ['techniques', 'weaknesses', 'mitigations']
        try:
            for filename in os.listdir(self.data_path):
                # Check if it's a file, ends with .json, and not in excluded dirs (implicit check)
                full_path = os.path.join(self.data_path, filename)
                if os.path.isfile(full_path) and filename.lower().endswith('.json'):
                    # Basic check to exclude known subdirs - assumes mappings
                    # are top-level in data/
                    is_subdir_file = False
                    for subdir in excluded_dirs:
                        # Unlikely but needed for safety
                        if filename.startswith(subdir + os.path.sep):
                            is_subdir_file = True
                            break
                    # Should always be true if isfile() check passes
                    if not is_subdir_file:
                        mapping_files.append(filename)
        except OSError as e:
            logger.error("Error listing directory %s: %s", self.data_path, e)
        return mapping_files

    def list_objectives(self, mapping_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lists the objectives from the specified or current mapping.

        Args:
            mapping_name (Optional[str]): The filename of the mapping to use.
                                          If None, uses the currently loaded mapping.

        Returns:
            List[Dict[str, Any]]: A list of objective dictionaries (each typically
                containing 'name', 'description', 'techniques'). Returns an empty
                list if no mapping is loaded or the specified mapping doesn't exist.
        """
        active_mapping_name = mapping_name or self.current_mapping_name
        if not active_mapping_name or active_mapping_name not in self.objective_mappings:
            logger.warning("No objective mapping loaded or '%s' not found.", active_mapping_name)
            return []
        # Return a copy to prevent external modification
        return [obj.copy() for obj in self.objective_mappings[active_mapping_name]]

    def get_techniques_for_objective(self, objective_name: str, mapping_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves all techniques associated with a specific objective name
        within the specified or current mapping.

        Args:
            objective_name (str): The name of the objective.
            mapping_name (Optional[str]): The filename of the mapping to use.
                                          If None, uses the currently loaded mapping.

        Returns:
            List[Dict[str, Any]]: A list of technique data dictionaries associated
                with the objective. Returns an empty list if the objective or
                mapping is not found, or the objective has no techniques listed.

        Logs:
            Warning if an objective references a technique ID that doesn't exist.
        """
        active_mapping_name = mapping_name or self.current_mapping_name
        objectives = self.list_objectives(active_mapping_name)
        if not objectives:
            return []

        found_objective = None
        for obj in objectives:
            if obj.get('name') == objective_name:
                found_objective = obj
                break

        if not found_objective:
            return []

        technique_ids = found_objective.get('techniques', [])
        associated_techniques = []
        for t_id in technique_ids:
            technique = self.get_technique(t_id)
            if technique:
                associated_techniques.append(technique)
            else:
                # Log a warning about missing technique
                logger.warning(
                    "Objective '%s' in mapping '%s' references non-existent technique %s",
                    objective_name,
                    active_mapping_name,
                    t_id
                )
        return associated_techniques

    def get_technique(self, technique_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a specific technique by its ID.

        Args:
            technique_id (str): The ID of the technique (e.g., "T1002").

        Returns:
            Optional[Dict[str, Any]]: The technique data dictionary if found, otherwise None.
        """
        return self.techniques.get(technique_id)

    def get_weakness(self, weakness_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a specific weakness by its ID.

        Args:
            weakness_id (str): The ID of the weakness (e.g., "W1006").

        Returns:
            Optional[Dict[str, Any]]: The weakness data dictionary if found, otherwise None.
        """
        return self.weaknesses.get(weakness_id)

    def get_mitigation(self, mitigation_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a specific mitigation by its ID.

        Args:
            mitigation_id (str): The ID of the mitigation (e.g., "M1005").

        Returns:
            Optional[Dict[str, Any]]: The mitigation data dictionary if found, otherwise None.
        """
        return self.mitigations.get(mitigation_id)

    def get_weaknesses_for_technique(self, technique_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all weaknesses associated with a specific technique.

        Args:
            technique_id (str): The ID of the technique.

        Returns:
            List[Dict[str, Any]]: A list of weakness data dictionaries associated with
                the technique. Returns an empty list if the technique is not found or
                has no weaknesses listed.
        """
        technique = self.get_technique(technique_id)
        if not technique:
            return []

        weakness_ids = technique.get('weaknesses', [])
        associated_weaknesses = []
        for w_id in weakness_ids:
            weakness = self.get_weakness(w_id)
            if weakness:
                associated_weaknesses.append(weakness)
            else:
                logger.warning(
                    "Technique %s references non-existent weakness %s",
                    technique_id,
                    w_id
                )
        return associated_weaknesses

    def get_mitigations_for_weakness(self, weakness_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all mitigations associated with a specific weakness.

        Args:
            weakness_id (str): The ID of the weakness.

        Returns:
            List[Dict[str, Any]]: A list of mitigation data dictionaries associated with
                the weakness. Returns an empty list if the weakness is not found or
                has no mitigations listed.
        """
        weakness = self.get_weakness(weakness_id)
        if not weakness:
            return []

        mitigation_ids = weakness.get('mitigations', [])
        associated_mitigations = []
        for m_id in mitigation_ids:
            mitigation = self.get_mitigation(m_id)
            if mitigation:
                associated_mitigations.append(mitigation)
            else:
                logger.warning(
                    "Weakness %s references non-existent mitigation %s",
                    weakness_id,
                    m_id
                )
        return associated_mitigations

    def get_techniques_for_weakness(self, weakness_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all techniques associated with a specific weakness.
        Uses pre-computed reverse index.

        Args:
            weakness_id (str): The ID of the weakness.

        Returns:
            List[Dict[str, Any]]: A list of technique data dictionaries associated with
                the weakness. Returns an empty list if the weakness is not found or
                no techniques reference it.
        """
        # First check if the weakness exists
        if not self.get_weakness(weakness_id):
            logger.warning(
                "Weakness %s not found when searching for associated techniques.",
                weakness_id
            )
            return []

        # O(1) lookup using pre-computed reverse index
        technique_ids = self._weakness_to_techniques.get(weakness_id, [])
        
        # Convert IDs to full technique objects
        associated_techniques = []
        for technique_id in technique_ids:
            technique = self.get_technique(technique_id)
            if technique:
                associated_techniques.append(technique)
            else:
                logger.warning("Index inconsistency: technique %s not found", technique_id)

        if not associated_techniques:
            logger.debug("No techniques found that reference weakness %s.", weakness_id)

        return associated_techniques

    def get_weaknesses_for_mitigation(self, mitigation_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all weaknesses associated with a specific mitigation.
        Uses pre-computed reverse index.

        Args:
            mitigation_id (str): The ID of the mitigation.

        Returns:
            List[Dict[str, Any]]: A list of weakness data dictionaries associated with
                the mitigation. Returns an empty list if the mitigation is not found or
                no weaknesses reference it.
        """
        # First check if the mitigation exists
        if not self.get_mitigation(mitigation_id):
            logger.warning(
                "Mitigation %s not found when searching for associated weaknesses.",
                mitigation_id
            )
            return []

        # O(1) lookup using pre-computed reverse index
        weakness_ids = self._mitigation_to_weaknesses.get(mitigation_id, [])
        
        # Convert IDs to full weakness objects
        associated_weaknesses = []
        for weakness_id in weakness_ids:
            weakness = self.get_weakness(weakness_id)
            if weakness:
                associated_weaknesses.append(weakness)
            else:
                logger.warning("Index inconsistency: weakness %s not found", weakness_id)

        if not associated_weaknesses:
            logger.debug("No weaknesses found that reference mitigation %s.", mitigation_id)

        return associated_weaknesses

    def get_all_weaknesses_with_name_and_id(self) -> List[Dict[str, str]]:
        """
        Retrieves all weaknesses with just their name and ID.

        Returns:
            List[Dict[str, str]]: A list of dictionaries, each containing 'id' and 'name' 
                                 for a weakness.
        """
        return [{'id': w_id, 'name': weakness.get('name', '')} 
                for w_id, weakness in self.weaknesses.items()]

    def get_all_weaknesses_with_full_detail(self) -> List[Dict[str, Any]]:
        """
        Retrieves all weaknesses with their full detail.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each containing the full details
                                 of a weakness.
        """
        return list(self.weaknesses.values())

    def get_all_techniques_with_name_and_id(self) -> List[Dict[str, str]]:
        """
        Retrieves all techniques with just their name and ID.

        Returns:
            List[Dict[str, str]]: A list of dictionaries, each containing 'id' and 'name'
                                 for a technique.
        """
        return [{'id': t_id, 'name': technique.get('name', '')} 
                for t_id, technique in self.techniques.items()]

    def get_all_techniques_with_full_detail(self) -> List[Dict[str, Any]]:
        """
        Retrieves all techniques with their full detail.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each containing the full details
                                 of a technique.
        """
        return list(self.techniques.values())

    def get_all_mitigations_with_name_and_id(self) -> List[Dict[str, str]]:
        """
        Retrieves all mitigations with just their name and ID.

        Returns:
            List[Dict[str, str]]: A list of dictionaries, each containing 'id' and 'name'
                                 for a mitigation.
        """
        return [{'id': m_id, 'name': mitigation.get('name', '')} 
                for m_id, mitigation in self.mitigations.items()]

    def get_all_mitigations_with_full_detail(self) -> List[Dict[str, Any]]:
        """
        Retrieves all mitigations with their full detail.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each containing the full details
                                 of a mitigation.
        """
        return list(self.mitigations.values())

    def search(self,
              keywords: str,
              item_types: Optional[List[str]] = None,
              substring_match: bool = False,
              search_logic: str = "AND") -> Dict[str, List[Dict[str, Any]]]:
        """
        Search for techniques, weaknesses, or mitigations matching specified keywords.

        Performs a case-insensitive search across name and description fields.
        Supports quoted phrases and configurable search logic (AND/OR).

        Args:
            keywords (str): Keywords to search for. Use quotes for exact phrases.
                          Examples: 'network forensics', '"memory analysis"', 'disk imaging'
            item_types (Optional[List[str]]): Types of items to search
                ('techniques', 'weaknesses', 'mitigations'). If None, searches all types.
            substring_match (bool): If True, uses substring matching instead of word boundaries.
                                  Default is False (word boundary matching for precision).
            search_logic (str): Search logic to use. 'AND' requires all terms to match,
                              'OR' requires any term to match. Default is 'AND'.

        Returns:
            Dict[str, List[Dict[str, Any]]]: Dictionary with keys for each item type
                                             and values as lists of matching items, sorted by relevance.
        
        Raises:
            ValueError: If search_logic is not 'AND' or 'OR'.
        """
        # Validate search parameters
        self._validate_search_parameters(search_logic)
        
        # Initialize result dictionary
        results = self._initialize_search_results()

        # Determine which collections to search
        collections_to_search = self._determine_search_collections(item_types)

        # Parse search terms (handle quoted phrases)
        search_terms, phrases = self._parse_search_query(keywords)
        if not search_terms and not phrases:
            return results

        # Search each collection and sort results
        return self._search_collections(collections_to_search, search_terms, phrases, substring_match, search_logic, results)

    def _validate_search_parameters(self, search_logic: str) -> None:
        """
        Validate search parameters and raise appropriate errors.
        
        Args:
            search_logic (str): Search logic to validate
            
        Raises:
            ValueError: If search_logic is not 'AND' or 'OR'
        """
        if search_logic.upper() not in ["AND", "OR"]:
            raise ValueError("search_logic must be 'AND' or 'OR'")

    def _initialize_search_results(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Initialize empty search results dictionary.
        
        Returns:
            Dict[str, List[Dict[str, Any]]]: Empty results dictionary
        """
        return {
            "techniques": [],
            "weaknesses": [],
            "mitigations": []
        }

    def _determine_search_collections(self, item_types: Optional[List[str]]) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        Determine which collections to search based on item_types parameter.
        
        Args:
            item_types (Optional[List[str]]): Types of items to search
            
        Returns:
            Dict[str, Dict[str, Dict[str, Any]]]: Dictionary mapping collection names to collections
        """
        collections_to_search = {}
        if item_types is None or "techniques" in item_types:
            collections_to_search["techniques"] = self.techniques
        if item_types is None or "weaknesses" in item_types:
            collections_to_search["weaknesses"] = self.weaknesses
        if item_types is None or "mitigations" in item_types:
            collections_to_search["mitigations"] = self.mitigations
        return collections_to_search

    def _search_collections(self, 
                          collections_to_search: Dict[str, Dict[str, Dict[str, Any]]], 
                          search_terms: List[str], 
                          phrases: List[str], 
                          substring_match: bool, 
                          search_logic: str, 
                          results: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search each collection and sort results by relevance.
        
        Args:
            collections_to_search: Dictionary of collections to search
            search_terms: List of individual search terms
            phrases: List of quoted phrases
            substring_match: Whether to use substring matching
            search_logic: Search logic ('AND' or 'OR')
            results: Results dictionary to populate
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: Search results sorted by relevance
        """
        search_logic = search_logic.upper()
        
        for collection_name, collection in collections_to_search.items():
            scored_results = []
            
            for _, item in collection.items():
                score = self._calculate_search_score(item, search_terms, phrases, substring_match, search_logic)
                if score > 0:
                    scored_results.append((item, score))
            
            # Sort by score (highest first) and extract items
            results[collection_name] = self._sort_search_results(scored_results)

        return results

    def _sort_search_results(self, scored_results: List[Tuple[Dict[str, Any], int]]) -> List[Dict[str, Any]]:
        """
        Sort search results by relevance score.
        
        Args:
            scored_results: List of tuples containing (item, score)
            
        Returns:
            List[Dict[str, Any]]: Sorted list of items (highest score first)
        """
        scored_results.sort(key=lambda x: x[1], reverse=True)
        return [item for item, _ in scored_results]

    def _parse_search_query(self, keywords: str) -> Tuple[List[str], List[str]]:
        """
        Parse search query to extract individual terms and quoted phrases.
        
        Args:
            keywords (str): The search query string
            
        Returns:
            tuple: (list of individual terms, list of quoted phrases)
        """
        import re
        
        terms = []
        phrases = []
        
        # Extract quoted phrases first
        phrase_pattern = r'"([^"]+)"'
        quoted_matches = re.findall(phrase_pattern, keywords)
        phrases.extend([phrase.lower().strip() for phrase in quoted_matches])
        
        # Remove quoted phrases from the original string
        keywords_without_phrases = re.sub(phrase_pattern, '', keywords)
        
        # Extract individual words (excluding common boolean operators for now)
        word_pattern = r'\b\w+\b'
        word_matches = re.findall(word_pattern, keywords_without_phrases.lower())
        
        # Filter out very short words and common stop words
        stop_words = {'and', 'or', 'not', 'the', 'a', 'an', 'is', 'are', 'was', 'were'}
        terms.extend([word for word in word_matches if len(word) > 2 and word not in stop_words])
        
        return terms, phrases

    def _calculate_search_score(self, item: Dict[str, Any], terms: List[str], phrases: List[str], substring_match: bool = False, search_logic: str = "AND") -> int:
        """
        Calculate relevance score for a search result.
        
        Scoring:
        - Name + Description matches: 100+ points
        - Name only matches: 50+ points  
        - Description only matches: 10+ points
        - No matches: 0 points
        
        For OR logic, scores are adjusted based on match percentage.
        
        Args:
            item: The item to score
            terms: List of search terms
            phrases: List of quoted phrases
            substring_match: If True, uses substring matching instead of word boundaries
            search_logic: 'AND' requires all terms to match, 'OR' requires any term to match
            
        Returns:
            int: Relevance score (0 = no match)
        """
        # Extract and normalize text fields
        name = str(item.get("name", "")).lower()
        description = str(item.get("description", "")).lower()
        
        # Find all term and phrase matches
        match_results = self._find_term_matches(name, description, terms, phrases, substring_match)
        
        # Apply search logic filtering
        if not self._apply_search_logic(match_results, terms, phrases, search_logic):
            return 0
        
        # Calculate final score
        return self._calculate_final_score(match_results, terms, phrases, search_logic)

    def _find_term_matches(self, name: str, description: str, terms: List[str], phrases: List[str], substring_match: bool) -> Dict[str, Any]:
        """
        Find which terms and phrases match in name and description fields.
        
        Args:
            name: Normalized name text
            description: Normalized description text
            terms: List of search terms
            phrases: List of quoted phrases
            substring_match: Whether to use substring matching
            
        Returns:
            Dict[str, Any]: Dictionary containing match results
        """
        import re
        
        found_terms = set()
        found_phrases = set()
        name_matches = 0
        desc_matches = 0
        
        # Check individual terms
        for term in terms:
            pattern = re.escape(term) if substring_match else r'\b' + re.escape(term) + r'\b'
            
            found_in_name = bool(re.search(pattern, name))
            found_in_desc = bool(re.search(pattern, description))
            
            if found_in_name or found_in_desc:
                found_terms.add(term)
                
            if found_in_name:
                name_matches += 1
            if found_in_desc:
                desc_matches += 1
        
        # Check phrases (worth more points)
        for phrase in phrases:
            escaped_phrase = re.escape(phrase)
            pattern = escaped_phrase if substring_match else r'\b' + escaped_phrase + r'\b'
            
            found_in_name = bool(re.search(pattern, name))
            found_in_desc = bool(re.search(pattern, description))
            
            if found_in_name or found_in_desc:
                found_phrases.add(phrase)
                
            if found_in_name:
                name_matches += 2  # Phrases worth more
            if found_in_desc:
                desc_matches += 2
        
        return {
            'found_terms': found_terms,
            'found_phrases': found_phrases,
            'name_matches': name_matches,
            'desc_matches': desc_matches
        }

    def _apply_search_logic(self, match_results: Dict[str, Any], terms: List[str], phrases: List[str], search_logic: str) -> bool:
        """
        Apply search logic (AND/OR) to determine if item should be included.
        
        Args:
            match_results: Dictionary containing match results
            terms: List of search terms
            phrases: List of quoted phrases
            search_logic: 'AND' or 'OR'
            
        Returns:
            bool: True if item passes search logic, False otherwise
        """
        total_search_items = len(terms) + len(phrases)
        total_found = len(match_results['found_terms']) + len(match_results['found_phrases'])
        
        if search_logic == "AND":
            # Must match ALL terms/phrases
            return total_found >= total_search_items
        else:  # OR logic
            # Must match AT LEAST ONE term/phrase
            return total_found > 0

    def _calculate_final_score(self, match_results: Dict[str, Any], terms: List[str], phrases: List[str], search_logic: str) -> int:
        """
        Calculate final weighted score based on match results.
        
        Args:
            match_results: Dictionary containing match results
            terms: List of search terms
            phrases: List of quoted phrases
            search_logic: 'AND' or 'OR'
            
        Returns:
            int: Final relevance score
        """
        name_matches = match_results['name_matches']
        desc_matches = match_results['desc_matches']
        
        # Calculate base score based on where matches were found
        if name_matches > 0 and desc_matches > 0:
            base_score = 100 + name_matches + desc_matches
        elif name_matches > 0:
            base_score = 50 + name_matches
        elif desc_matches > 0:
            base_score = 10 + desc_matches
        else:
            base_score = 0
        
        # For OR logic, apply multiplier based on match percentage
        if search_logic == "OR" and len(terms) + len(phrases) > 1:
            total_search_items = len(terms) + len(phrases)
            total_found = len(match_results['found_terms']) + len(match_results['found_phrases'])
            match_percentage = total_found / total_search_items
            # Scale score: 100% match gets full score, partial matches get reduced score
            # But ensure at least some score for any match
            score_multiplier = max(0.3, match_percentage)
            base_score = int(base_score * score_multiplier)
        
        return base_score

    def get_mit_list_for_technique(self, technique_id: str) -> List[str]:
        """
        Get all mitigation IDs for a technique by traversing its weaknesses.
        
        This method replicates the behavior of the original solveitcore.py method.
        It returns a deduplicated list of mitigation IDs associated with the technique.
        
        Args:
            technique_id (str): The ID of the technique
            
        Returns:
            List[str]: List of unique mitigation IDs associated with the technique
        """
        mit_list_for_this_technique = []
        technique = self.get_technique(technique_id)
        if not technique:
            return mit_list_for_this_technique
            
        for weakness_id in technique.get('weaknesses', []):
            weakness_info = self.get_weakness(weakness_id)
            if weakness_info:
                for mitigation_id in weakness_info.get('mitigations', []):
                    if mitigation_id not in mit_list_for_this_technique:
                        mit_list_for_this_technique.append(mitigation_id)
        
        return mit_list_for_this_technique

    def get_max_mitigations_per_technique(self) -> int:
        """
        Returns the maximum number of mitigations across all techniques.
        Used by Excel generation for column sizing.
        
        Returns:
            int: Maximum number of mitigations for any single technique
        """
        max_mits = 0
        for technique_id in self.techniques.keys():
            mits = self.get_mit_list_for_technique(technique_id)
            if len(mits) > max_mits:
                max_mits = len(mits)
        return max_mits

    def list_tactics(self) -> List[str]:
        """
        Compatibility method - returns list of objective names.
        Maintains compatibility with original solveitcore.py API.
        
        Returns:
            List[str]: List of objective names from current mapping
        """
        objectives = self.list_objectives()
        return [obj.get('name') for obj in objectives]

    @property 
    def tactics(self) -> List[Dict[str, Any]]:
        """
        Compatibility property - returns current objectives mapping.
        Maintains compatibility with original solveitcore.py API.
        
        Returns:
            List[Dict[str, Any]]: Current objective mapping data
        """
        return self.list_objectives()

    def list_techniques(self) -> List[str]:
        """
        Returns a sorted list of all technique IDs.
        
        Returns:
            List[str]: Sorted list of technique IDs
        """
        return sorted(self.techniques.keys())

    def list_weaknesses(self) -> List[str]:
        """
        Returns a sorted list of all weakness IDs.
        
        Returns:
            List[str]: Sorted list of weakness IDs
        """
        return sorted(self.weaknesses.keys())

    def list_mitigations(self) -> List[str]:
        """
        Returns a sorted list of all mitigation IDs.
        
        Returns:
            List[str]: Sorted list of mitigation IDs
        """
        return sorted(self.mitigations.keys())

    def get_techniques_for_mitigation(self, mitigation_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all techniques associated with a specific mitigation.
        Uses pre-computed reverse index.

        Args:
            mitigation_id (str): The ID of the mitigation.

        Returns:
            List[Dict[str, Any]]: A list of technique data dictionaries associated with
                the mitigation. Returns an empty list if the mitigation is not found or
                no techniques reference it.
        """
        # First check if the mitigation exists
        if not self.get_mitigation(mitigation_id):
            logger.warning(
                "Mitigation %s not found when searching for associated techniques.",
                mitigation_id
            )
            return []

        # O(1) lookup using pre-computed reverse index
        technique_ids = self._mitigation_to_techniques.get(mitigation_id, [])
        
        # Convert IDs to full technique objects
        associated_techniques = []
        for technique_id in technique_ids:
            technique = self.get_technique(technique_id)
            if technique:
                associated_techniques.append(technique)
            else:
                logger.warning("Index inconsistency: technique %s not found", technique_id)

        if not associated_techniques:
            logger.debug("No techniques found that reference mitigation %s.", mitigation_id)

        return associated_techniques
