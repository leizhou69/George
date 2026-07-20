#!/usr/bin/env python3
"""
Automated Biomni agent runner with configurable parameters
Runs agent with different combinations of LLM models and temperatures.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import base64
import re
from itertools import count

# NOTE: `biomni` is an editable install of the patched fork (../biomni-fork) —
# no sys.path shadowing. Run this harness from the George project root:
#   python harness/run_biomni.py s5 o4.8
# so the relative paths below (data/, output/, queries/, biomni_data_cache)
# resolve against the project root.

from biomni.agent import A1
from biomni.config import default_config
from biomni.llm import _anthropic_rejects_sampling_params


def _model_ignores_temperature(model_name: str) -> bool:
    """Whether sweeping temperature is meaningless for this model.

    Newer Anthropic models (Opus 4.7+, Sonnet 5+) reject temperature outright,
    and gpt-5* models have it dropped from the request in biomni/llm.py. For
    these, all temperature values produce identical runs, so we run only once.
    """
    return _anthropic_rejects_sampling_params(model_name) or model_name.startswith("gpt-5")

# ============================================================================
# CONFIGURATION SECTION - Modify these parameters
# ============================================================================

# Model name mapping dictionary (short_key: full_model_name)
MODEL_NAMES = {
    "s3.5": "claude-3-5-sonnet-20241022",
    "s3.7": "claude-3-7-sonnet-20250219",
    "s4": "claude-4-sonnet-latest",
    "s4.5": "claude-sonnet-4-5-20250929",
    "s4.6": "claude-sonnet-4-6",
    "s5": "claude-sonnet-5",
    "o4.5": "claude-opus-4-5-20251101",
    "gem2": "gemini-2.0-flash-exp",
    "gem3f": "gemini-3-flash-preview",
    "gem3p": "gemini-3-pro-preview",
    "gpt4o": "gpt-4o",
    "gpt5": "gpt-5",
    "gpt5.2": "gpt-5.2",
    "gpt5.4": "gpt-5.4",
    "grk4": "grok-4",
    "o4.6": "claude-opus-4-6",
    "o4.8": "claude-opus-4-8",
}

# Query configuration
QUERY_FILE = "queries/query_05_b.txt"  # Path to query text file (project-root-relative)
QUERY_ID = "q05b"  # Short ID for output filename

# LLM configurations (model_name: short_id)
# Used as fallback when no models are specified on the command line
LLM_CONFIGS = {
    #"claude-sonnet-4-5-20250929": "s4.5",
    # "claude-opus-4-5-20251101": "o4.5",
    # "gemini-3-flash-preview": "gem3f",
    # "gpt-5": "gpt5",
    # "grok-4": "grk4",
    # "gemini-3-pro-preview": "gem3p",  # Fixed: Gemini 3 models need "-preview" suffix
    # "claude-sonnet-4-6": "s4.6",
    "claude-sonnet-5": "s5",
    "claude-opus-4-8": "o4.8",
}

# Temperature values to test
TEMPERATURES = [0.5,0.7, 0.9]

# Time limit in seconds (200 minutes = 12000 seconds)
TIMEOUT_SECONDS = 12000
TIMEOUT_ID = "200m"  # Short ID for output filename

# Data files to register with agent
DATA_FILES = {
    "Pathogenic_repeats": "data/5UTR/B_5UTR_Pathogenic_GCN.txt",
    "All_5UTR_GCN_catalog": "data/5UTR/B_Cat_5UTR_GCNs_masked.tsv",
    "AG_Predicted_2x_expansion": "data/5UTR/B_5UTR_all_GCN_2xAG.tsv",
    "AG_Predicted_5x_expansion": "data/5UTR/B_5UTR_all_GCN_5xAG.tsv",
    "AG_Predicted_20x_expansion": "data/5UTR/B_5UTR_all_GCN_20xAG.tsv",
}

# ============================================================================
# END CONFIGURATION SECTION
# ============================================================================


def run_single_experiment(llm_name, llm_id, temperature, query_path, prompt, output_dir="output"):
    """Run a single agent experiment with specified parameters."""
    
    # Configure agent
    default_config.temperature = temperature
    data_root = Path("./biomni_data_cache").resolve()

    # Use the local data lake and skip all S3 downloads. Passing a non-None
    # expected_data_lake_files makes A1 take its "skip datalake download" branch,
    # so it never contacts biomni-release.s3.amazonaws.com. The lake at
    # <data_root>/biomni_data/data_lake is already complete (76/76 files); the
    # 403s in older runs were the custom DATA_FILES leaking into the shared
    # data_lake_dict across experiments, not the real lake failing.
    data_lake_dir = data_root / "biomni_data" / "data_lake"
    local_data_lake_files = (
        sorted(p.name for p in data_lake_dir.iterdir()) if data_lake_dir.is_dir() else []
    )
    
    print(f"\n{'='*80}")
    print(f"Starting experiment: {QUERY_ID}_{llm_id}_Tmp{temperature}_{TIMEOUT_ID}")
    print(f"LLM: {llm_name}")
    print(f"Temperature: {temperature}")
    print(f"Timeout: {TIMEOUT_SECONDS}s")
    print(f"{'='*80}\n")
    
    try:
        # Create output directory first
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        prefix = f"{QUERY_ID}_{llm_id}_Tmp{temperature}_{TIMEOUT_ID}_{timestamp}"
        
        log_dir = Path(output_dir) / prefix
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Change to output directory so all agent-generated files go there
        original_cwd = os.getcwd()
        os.chdir(log_dir)
        
        try:
            agent = A1(
                path=str(data_root),
                llm=llm_name,
                timeout_seconds=TIMEOUT_SECONDS,
                expected_data_lake_files=local_data_lake_files,
            )
            
            # Register data files (use absolute paths)
            agent.add_data({
                name: f"Custom dataset at {(Path(original_cwd) / path).resolve()}"
                for name, path in DATA_FILES.items()
            })
            
            # Run query
            print("Starting agent query execution...")
            agent.go(prompt)
            print("Query execution complete\n")
            
            # Save raw trace (while still in log_dir)
            print(f"Saving trace with {len(agent.log)} log entries...")
            trace_path = Path(f"{prefix}.log")
            trace_path.write_text("\n".join(agent.log), encoding="utf-8")
            print(f"Wrote trace to {log_dir / trace_path}")
            
            # Generate markdown with images
            markdown_content = agent._generate_markdown_content(include_images=True)
            image_dir = Path("media")
            image_dir.mkdir(parents=True, exist_ok=True)
            
            image_counter = count(1)
            saved_images = []
            
            def store_data_uri(data_uri: str) -> str | None:
                if not data_uri.startswith("data:image/") or "," not in data_uri:
                    return None
                _, encoded = data_uri.split(",", 1)
                image_bytes = base64.b64decode(encoded)
                idx = next(image_counter)
                image_path = image_dir / f"plot_{idx}.png"
                image_path.write_bytes(image_bytes)
                saved_images.append(image_path)
                return f"media/{image_path.name}"
            
            def replace_md_image(match):
                rel_path = store_data_uri(match.group(2))
                if rel_path is None:
                    return "".join(match.groups())
                return f"{match.group(1)}{rel_path}{match.group(3)}"
            
            def replace_html_image(match):
                rel_path = store_data_uri(match.group(2))
                if rel_path is None:
                    return "".join(match.groups())
                return f"{match.group(1)}{rel_path}{match.group(3)}"
            
            md_pattern = r'(!\[[^\]]*\]\()(data:image/[^)]+)(\))'
            html_pattern = r'(src=["\'])(data:image/[^"\']+)(["\'])'
            
            markdown_content = re.sub(md_pattern, replace_md_image, markdown_content, flags=re.IGNORECASE)
            markdown_content = re.sub(html_pattern, replace_html_image, markdown_content, flags=re.IGNORECASE)
            
            md_path = Path(f"{prefix}.md")
            md_path.write_text(markdown_content, encoding="utf-8")
            
            print(f"Saved {len(saved_images)} image(s) to {log_dir / image_dir}")
            print(f"Wrote markdown to {log_dir / md_path}")
            print(f"\n✓ Experiment {prefix} completed successfully")
            
        finally:
            # Always restore original directory
            os.chdir(original_cwd)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Experiment failed with error: {e}")
        import traceback
        traceback.print_exc()
        
        # Try to restore directory even on error
        try:
            os.chdir(original_cwd)
        except:
            pass
        
        return False


def main():
    """Main function to run all experiment combinations."""
    import argparse

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Run Biomni agent with specified model(s)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Available model keys:
{chr(10).join(f'  {key:8} -> {value}' for key, value in MODEL_NAMES.items())}

Examples:
  python run_biomni.py s4.5           # Run with Sonnet 4.5
  python run_biomni.py s4.5 o4.5      # Run with Sonnet 4.5 and Opus 4.5
  python run_biomni.py gpt5           # Run with GPT-5
"""
    )
    parser.add_argument(
        'models',
        nargs='*',
        help='Model key(s) to run (e.g., s4.5, o4.5, gpt5). If not specified, uses LLM_CONFIGS.'
    )
    parser.add_argument(
        '--output-dir',
        default='output',
        help='Base output directory for experiment folders (default: output).'
    )
    parser.add_argument(
        '--temperatures',
        nargs='+',
        type=float,
        default=None,
        metavar='T',
        help='Temperatures to run (e.g., --temperatures 0.9). Defaults to all temperatures in TEMPERATURES.'
    )

    args = parser.parse_args()

    # Determine which models to run
    if args.models:
        # Use models from command line
        llm_configs = {}
        for model_key in args.models:
            if model_key not in MODEL_NAMES:
                print(f"Error: Unknown model key '{model_key}'")
                print(f"Available keys: {', '.join(MODEL_NAMES.keys())}")
                sys.exit(1)
            llm_configs[MODEL_NAMES[model_key]] = model_key
    else:
        # Use default LLM_CONFIGS
        llm_configs = LLM_CONFIGS

    # Apply temperature filter if specified
    temperatures = args.temperatures if args.temperatures else TEMPERATURES

    # Load query
    query_path = Path(QUERY_FILE)
    if not query_path.exists():
        print(f"Error: Query file not found: {QUERY_FILE}")
        sys.exit(1)

    prompt = query_path.read_text(encoding="utf-8")

    # Calculate total experiments (models that ignore temperature run only once)
    total_experiments = sum(
        1 if _model_ignores_temperature(llm_name) else len(temperatures)
        for llm_name in llm_configs
    )
    current_experiment = 0
    successful = 0
    failed = 0

    print(f"\n{'='*80}")
    print(f"BIOMNI BATCH EXPERIMENT RUNNER")
    print(f"{'='*80}")
    print(f"Query: {QUERY_FILE} ({QUERY_ID})")
    print(f"Output dir: {args.output_dir}")
    print(f"LLMs: {len(llm_configs)} models - {', '.join(llm_configs.values())}")
    print(f"Temperatures: {temperatures}")
    print(f"Timeout: {TIMEOUT_SECONDS}s ({TIMEOUT_ID})")
    print(f"Total experiments: {total_experiments}")
    print(f"{'='*80}\n")

    # Run all combinations
    for llm_name, llm_id in llm_configs.items():
        # Models that ignore temperature run once at the first requested value
        if _model_ignores_temperature(llm_name):
            model_temps = temperatures[:1]
            print(f"\nNote: '{llm_name}' ignores temperature; running once at {model_temps[0]}.")
        else:
            model_temps = temperatures

        for temperature in model_temps:
            current_experiment += 1
            print(f"\n[{current_experiment}/{total_experiments}] ", end="")

            success = run_single_experiment(llm_name, llm_id, temperature, query_path, prompt, args.output_dir)

            if success:
                successful += 1
            else:
                failed += 1

    # Summary
    print(f"\n{'='*80}")
    print(f"BATCH COMPLETION SUMMARY")
    print(f"{'='*80}")
    print(f"Total experiments: {total_experiments}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
