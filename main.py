#!/usr/bin/env python3
"""
IFC Graph Database - Main Entry Point

Processes IFC files and stores building elements in a Neo4j graph database.
Supports configuration via YAML file and command-line arguments.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv
import os

from graph_processor.element_filter import (
    filter_physical_elements,
    IFCLoadError,
    IFCValidationError,
)
from graph_processor.neo4j_store import (
    save_to_neo4j,
    DatabaseConnectionError,
    DatabaseOperationError,
)

# Module logger
logger = logging.getLogger(__name__)


def setup_logging(level: str = "INFO", log_format: Optional[str] = None) -> None:
    """
    Configure logging for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_format: Custom log format string
    """
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def load_config(config_path: str) -> dict:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the configuration file
    
    Returns:
        Configuration dictionary
    
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
    """
    path = Path(config_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    logger.info(f"Loaded configuration from: {config_path}")
    return config or {}


def get_default_config() -> dict:
    """
    Get default configuration when no config file is provided.
    
    Returns:
        Default configuration dictionary
    """
    return {
        'element_types': [
            'IfcWall',
            'IfcDoor',
            'IfcWindow',
            'IfcStair',
            'IfcSlab',
            'IfcRoof',
            'IfcColumn',
            'IfcBeam'
        ],
        'extraction': {
            'include_property_sets': True,
            'include_materials': True,
            'include_geometry': False,
            'max_properties_per_element': 50,
        },
        'logging': {
            'level': 'INFO',
        }
    }


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Process IFC files and store building elements in Neo4j graph database.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Use defaults from .env and config.yaml
  %(prog)s --ifc-file model.ifc      # Process specific IFC file
  %(prog)s --clear-db                # Clear database before import
  %(prog)s --config custom.yaml      # Use custom configuration file
        """
    )
    
    parser.add_argument(
        '--ifc-file',
        type=str,
        help='Path to the IFC file to process (overrides .env setting)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to the configuration file (default: config.yaml)'
    )
    
    parser.add_argument(
        '--clear-db',
        action='store_true',
        help='Clear the database before importing (WARNING: deletes all existing data)'
    )
    
    parser.add_argument(
        '--neo4j-uri',
        type=str,
        help='Neo4j connection URI (overrides .env setting)'
    )
    
    parser.add_argument(
        '--neo4j-user',
        type=str,
        help='Neo4j username (overrides .env setting)'
    )
    
    parser.add_argument(
        '--neo4j-password',
        type=str,
        help='Neo4j password (overrides .env setting)'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (overrides config file setting)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Parse IFC file and show what would be imported, but do not connect to database'
    )
    
    return parser.parse_args()


def main() -> int:
    """
    Main entry point for the IFC graph database processor.
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Parse command-line arguments
    args = parse_arguments()
    
    # Load environment variables
    load_dotenv()
    
    # Load configuration
    try:
        if Path(args.config).exists():
            config = load_config(args.config)
        else:
            logger.warning(f"Config file not found: {args.config}. Using defaults.")
            config = get_default_config()
    except yaml.YAMLError as e:
        print(f"Error: Invalid configuration file: {e}", file=sys.stderr)
        return 1
    
    # Setup logging
    log_level = args.log_level or config.get('logging', {}).get('level', 'INFO')
    log_format = config.get('logging', {}).get('format')
    setup_logging(log_level, log_format)
    
    # Get IFC file path (CLI > .env)
    ifc_file_path = args.ifc_file or os.getenv("IFC_FILE_PATH")
    if not ifc_file_path:
        logger.error("No IFC file specified. Use --ifc-file or set IFC_FILE_PATH in .env")
        return 1
    
    # Get Neo4j connection settings (CLI > .env)
    neo4j_uri = args.neo4j_uri or os.getenv('NEO4J_URI')
    neo4j_user = args.neo4j_user or os.getenv('NEO4J_USER')
    neo4j_password = args.neo4j_password or os.getenv('NEO4J_PASSWORD')
    
    if not args.dry_run and not all([neo4j_uri, neo4j_user, neo4j_password]):
        logger.error("Missing Neo4j connection settings. Set NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD")
        return 1
    
    # Get element types from config
    element_types = config.get('element_types', get_default_config()['element_types'])
    extraction_config = config.get('extraction', get_default_config()['extraction'])
    
    try:
        # Filter elements from IFC file
        logger.info(f"Processing IFC file: {ifc_file_path}")
        logger.info(f"Filtering element types: {', '.join(element_types)}")
        
        filtered_elements, ifc_file = filter_physical_elements(
            ifc_file_path,
            element_types=element_types,
            config=extraction_config
        )
        
        total_elements = sum(len(elems) for elems in filtered_elements.values())
        logger.info(f"Found {total_elements} elements across {len(filtered_elements)} types")
        
        # Dry run - just show what would be imported
        if args.dry_run:
            print("\n=== DRY RUN - No database changes made ===")
            print(f"IFC File: {ifc_file_path}")
            print(f"Total elements: {total_elements}")
            print("\nElements by type:")
            for elem_type, elements in filtered_elements.items():
                print(f"  {elem_type}: {len(elements)}")
            return 0
        
        # Warn about database clear
        if args.clear_db:
            logger.warning("--clear-db flag set: All existing data will be deleted!")
        
        # Save to Neo4j
        stats = save_to_neo4j(
            filtered_elements,
            ifc_file,
            neo4j_uri,
            neo4j_user,
            neo4j_password,
            clear_db=args.clear_db,
            config=extraction_config
        )
        
        logger.info("=" * 50)
        logger.info("Process completed successfully!")
        logger.info(f"  Elements created: {stats['elements']}")
        logger.info(f"  Structures created: {stats['structures']}")
        logger.info(f"  Materials linked: {stats['materials']}")
        logger.info("=" * 50)
        
        return 0
        
    except IFCValidationError as e:
        logger.error(f"IFC file validation error: {e}")
        return 1
        
    except IFCLoadError as e:
        logger.error(f"Failed to load IFC file: {e}")
        return 1
        
    except DatabaseConnectionError as e:
        logger.error(f"Database connection error: {e}")
        logger.error("Check that Neo4j is running and credentials are correct")
        return 1
        
    except DatabaseOperationError as e:
        logger.error(f"Database operation failed: {e}")
        return 1
        
    except KeyboardInterrupt:
        logger.warning("Operation cancelled by user")
        return 1
        
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())


    