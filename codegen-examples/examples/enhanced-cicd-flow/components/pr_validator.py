"""
PR Validator Component

This component performs automated checks on pull requests to ensure code quality.
It detects import cycles and other code quality issues and comments on PRs.
"""

import logging
from typing import Dict, List, Optional

import networkx as nx
from codegen import CodegenApp, Codebase
from codegen.extensions.github.types.events.pull_request import PullRequestLabeledEvent
from codegen.extensions.tools.github.create_pr_comment import create_pr_comment

from config import get_component_config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_graph_from_codebase(codebase: Codebase) -> nx.MultiDiGraph:
    """Create a directed graph representing import relationships in a codebase."""
    G = nx.MultiDiGraph()

    for imp in codebase.imports:
        if imp.from_file and imp.to_file:
            G.add_edge(
                imp.to_file.filepath,
                imp.from_file.filepath,
                color="red" if getattr(imp, "is_dynamic", False) else "black",
                label="dynamic" if getattr(imp, "is_dynamic", False) else "static",
                is_dynamic=getattr(imp, "is_dynamic", False),
            )
    return G


def find_import_cycles(G: nx.MultiDiGraph) -> List[List[str]]:
    """Identify strongly connected components (cycles) in the import graph."""
    cycles = [scc for scc in nx.strongly_connected_components(G) if len(scc) > 1]
    logger.info(f"🔄 Found {len(cycles)} import cycles.")

    for i, cycle in enumerate(cycles, 1):
        logger.info(f"\nCycle #{i}: Size {len(cycle)} files")
        logger.info(f"Total number of imports in cycle: {G.subgraph(cycle).number_of_edges()}")

        logger.info("\nFiles in this cycle:")
        for file in cycle:
            logger.info(f"  - {file}")

    return cycles


def find_problematic_import_loops(G: nx.MultiDiGraph, cycles: List[List[str]]) -> List[Dict]:
    """Identify cycles with both static and dynamic imports between files."""
    problematic_cycles = []

    for i, scc in enumerate(cycles):
        mixed_imports = {}
        for from_file in scc:
            for to_file in scc:
                if G.has_edge(from_file, to_file):
                    edges = G.get_edge_data(from_file, to_file)
                    dynamic_count = sum(1 for e in edges.values() if e["color"] == "red")
                    static_count = sum(1 for e in edges.values() if e["color"] == "black")

                    if dynamic_count > 0 and static_count > 0:
                        mixed_imports[(from_file, to_file)] = {
                            "dynamic": dynamic_count,
                            "static": static_count,
                            "edges": edges,
                        }

        if mixed_imports:
            problematic_cycles.append({"files": scc, "mixed_imports": mixed_imports, "index": i})

    logger.info(f"Found {len(problematic_cycles)} cycles with potentially problematic imports.")

    for i, cycle in enumerate(problematic_cycles):
        logger.info(f"\n⚠️ Problematic Cycle #{i + 1} (Index {cycle['index']}): Size {len(cycle['files'])} files")
        logger.info("\nFiles in cycle:")
        for file in cycle["files"]:
            logger.info(f"  - {file}")
        logger.info("\nMixed imports:")
        for (from_file, to_file), imports in cycle["mixed_imports"].items():
            logger.info(f"\n  From: {from_file}")
            logger.info(f"  To:   {to_file}")
            logger.info(f"  Static imports: {imports['static']}")
            logger.info(f"  Dynamic imports: {imports['dynamic']}")

    return problematic_cycles


def register_pr_validators(app: CodegenApp) -> None:
    """Register PR validator functions with the CodegenApp."""
    config = get_component_config("pr_validator")
    
    @app.github.event("pull_request:labeled")
    def handle_pr_labeled(event: PullRequestLabeledEvent) -> Dict:
        """Handle PR labeled events and run import cycle checks."""
        # Check if the label is "Codegen"
        if event.label.name.lower() != "codegen":
            return {"status": "ignored", "reason": "Not a Codegen label"}
        
        logger.info(f"Processing PR #{event.pull_request.number} with Codegen label")
        
        # Get the codebase at the PR head commit
        codebase = Codebase.from_repo(
            event.repository.get("full_name"), 
            commit=event.pull_request.head.sha
        )
        
        # Run import cycle analysis if enabled
        if config.get("check_import_cycles", True):
            G = create_graph_from_codebase(codebase)
            cycles = find_import_cycles(G)
            problematic_loops = find_problematic_import_loops(G, cycles)
            
            # Build comment message
            message = ["### Import Cycle Analysis - GitHub Check\n"]
            
            if problematic_loops:
                message.append("\n### ⚠️ Potentially Problematic Import Cycles")
                message.append("Cycles with mixed static and dynamic imports, which might require attention.")
                for i, cycle in enumerate(problematic_loops, 1):
                    message.append(f"\n#### Problematic Cycle {i}")
                    for (from_file, to_file), imports in cycle["mixed_imports"].items():
                        message.append(f"\nFrom: `{from_file}`")
                        message.append(f"To: `{to_file}`")
                        message.append(f"- Static imports: {imports['static']}")
                        message.append(f"- Dynamic imports: {imports['dynamic']}")
            else:
                message.append("\nNo problematic import cycles found! 🎉")
            
            # Post comment on PR
            create_pr_comment(
                codebase,
                event.pull_request.number,
                "\n".join(message),
            )
        
        return {
            "status": "success",
            "pr_number": event.pull_request.number,
            "num_files": len(codebase.files),
            "num_functions": len(codebase.functions),
        }
    
    @app.github.event("pull_request:opened")
    def handle_pr_opened(event: Dict) -> Dict:
        """Handle PR opened events and run basic code quality checks."""
        logger.info(f"Processing newly opened PR #{event['pull_request']['number']}")
        
        # Get the codebase at the PR head commit
        codebase = Codebase.from_repo(
            event["repository"]["full_name"], 
            commit=event["pull_request"]["head"]["sha"]
        )
        
        # Run code quality checks if enabled
        if config.get("check_code_quality", True):
            # Get the changed files
            changed_files = []
            for file in codebase.files:
                if file.is_changed:
                    changed_files.append(file)
            
            # Build comment message
            message = ["### Code Quality Check - GitHub Check\n"]
            message.append(f"\nAnalyzed {len(changed_files)} changed files in this PR.\n")
            
            # Add a welcome message
            message.append("To run a full import cycle analysis, add the `Codegen` label to this PR.")
            
            # Post comment on PR
            create_pr_comment(
                codebase,
                event["pull_request"]["number"],
                "\n".join(message),
            )
        
        return {
            "status": "success",
            "pr_number": event["pull_request"]["number"],
            "num_files": len(codebase.files),
        }


# For standalone usage
if __name__ == "__main__":
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Create a standalone app
    app = CodegenApp(name="pr-validator")
    
    # Register handlers
    register_pr_validators(app)
    
    # Run the app
    import uvicorn
    uvicorn.run(app.app, host="0.0.0.0", port=8000)