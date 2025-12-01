"""InfoShield AI Runner.

Entry point for running the InfoShield disaster verification system.
Supports both single-agent and multi-agent modes.
"""

import asyncio
import logging
import os
import sys
import warnings
from pathlib import Path

from dotenv import load_dotenv

# Suppress ADK internal warnings
warnings.filterwarnings('ignore', message='.*App name mismatch.*')
warnings.filterwarnings('ignore', message='.*EXPERIMENTAL.*')

# Configure logging
logging.getLogger('google.adk').setLevel(logging.ERROR)
logging.getLogger('google.adk.runners').setLevel(logging.ERROR)
logging.getLogger('httpx').setLevel(logging.WARNING)

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
load_dotenv(override=True)

# Use Google AI Studio (not Vertex AI)
os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'False'

# Default to multi-agent mode
USE_MULTI_AGENT = os.environ.get('INFOSHIELD_MULTI_AGENT', '1') == '1'


def check_api_key() -> bool:
    """Verify that the API key is configured."""
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key or api_key.startswith('your_'):
        print("=" * 60)
        print("ERROR: Google API Key not configured!")
        print("=" * 60)
        print("\nPlease set your Google API key in the .env file:")
        print("  GOOGLE_API_KEY=your_actual_api_key_here")
        print("\nGet a free API key from:")
        print("  https://aistudio.google.com/apikey")
        print("=" * 60)
        return False
    return True


def print_banner():
    """Print the InfoShield AI banner."""
    mode = "Multi-Agent" if USE_MULTI_AGENT else "Single-Agent"
    banner = f"""
================================================================
                                                              
   INFOSHIELD AI - Disaster Information Verification         
                                                              
   Powered by Google ADK + Gemini 2.0 Flash                  
   Mode: {mode}
                                                              
================================================================
"""
    print(banner)


def print_help():
    """Print usage help."""
    mode = "Multi-Agent" if USE_MULTI_AGENT else "Single-Agent"
    print(f"""
Current Mode: {mode}

Available Commands:
  /help     - Show this help message
  /status   - Show pending human reviews
  /health   - Check system health status
  /agents   - Show active agents (multi-agent mode)
  /mode     - Toggle between single/multi agent mode
  /clear    - Clear screen
  /quit     - Exit the application
  
Just type your query to get started!

Example queries:
  - "Is there flooding in Mumbai right now?"
  - "Are there any earthquake alerts in California?"
  - "What's the weather situation in Kerala?"
  - "Is the typhoon warning in Philippines real?"

Response includes:
  - Verification Status (VERIFIED/UNDER REVIEW/UNVERIFIED)
  - Credibility Score (0-100)
  - Urgency Level
  - Sources cited
  - Human review trigger for low credibility scores

Environment Variables:
  INFOSHIELD_MULTI_AGENT=1  Enable multi-agent mode (default)
  INFOSHIELD_MULTI_AGENT=0  Use single-agent mode
""")


async def interactive_mode():
    """Run InfoShield AI in interactive mode."""
    global USE_MULTI_AGENT

    from infoshield_ai.tools import get_pending_reviews

    print_banner()

    if not check_api_key():
        sys.exit(1)

    print("\nInitializing InfoShield AI...")

    # Initialize the appropriate runner based on mode
    if USE_MULTI_AGENT:
        from infoshield_ai.agents.runner import MultiAgentRunner
        runner = MultiAgentRunner(enable_human_review=True, verbose=False)
        print("✓ Multi-Agent System initialized")
        print("  Agents: Orchestrator → Analyzer → Search → Credibility")
    else:
        from infoshield_ai.agent import InfoShieldRunner
        runner = InfoShieldRunner(enable_human_review=True)
        print("✓ Single-Agent System initialized")

    print("\nReady! Type /help for commands.\n")
    print("-" * 60)

    while True:
        try:
            user_input = input("\nQuery: ").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.lower() == '/quit':
                print("\nThank you for using InfoShield AI. Stay safe!")
                break

            elif user_input.lower() == '/help':
                print_help()
                continue

            elif user_input.lower() == '/clear':
                os.system('cls' if os.name == 'nt' else 'clear')
                print_banner()
                continue

            elif user_input.lower() == '/mode':
                USE_MULTI_AGENT = not USE_MULTI_AGENT
                mode = "Multi-Agent" if USE_MULTI_AGENT else "Single-Agent"
                print(f"\n🔄 Switching to {mode} mode...")
                print("Please restart the application for changes to take effect.")
                print(
                    f"Or set: INFOSHIELD_MULTI_AGENT={'1' if USE_MULTI_AGENT else '0'}")
                continue

            elif user_input.lower() == '/agents':
                if USE_MULTI_AGENT and hasattr(runner, 'get_status'):
                    status = runner.get_status()
                    print("\n🤖 Active Agents:")
                    print("-" * 40)
                    for agent in status.get('agents', []):
                        print(f"  • {agent}")
                    print(
                        f"\nQueries processed: {status.get('query_count', 0)}")
                else:
                    print("\n🤖 Single-Agent Mode")
                    print("  • infoshield_ai (with google_search)")
                continue

            elif user_input.lower() == '/status':
                reviews = get_pending_reviews()
                if reviews["status"] == "error":
                    print(
                        f"\nError fetching reviews: {reviews.get('message', 'Unknown error')}")
                elif reviews["count"] == 0:
                    print("\n✓ No pending human reviews.")
                else:
                    print(f"\n📋 Pending Human Reviews ({reviews['count']}):")
                    print("-" * 50)
                    for entry in reviews["entries"]:
                        status_icon = "🔄" if entry.get(
                            'status') == 'pending' else "✓"
                        query_preview = entry.get('query', '')[:40]
                        cred_score = entry.get('credibility_score', 'N/A')
                        print(
                            f"  {status_icon} [{entry.get('session_id', 'N/A')}]")
                        print(f"     Query: {query_preview}...")
                        print(f"     Credibility: {cred_score}/100")
                        print()
                continue

            elif user_input.lower() == '/health':
                if hasattr(runner, 'get_status'):
                    status = runner.get_status()
                    if status.get("healthy", True):
                        print("\n✓ System healthy - No issues detected")
                        print(f"  Session: {status.get('session_id', 'N/A')}")
                        print(f"  Queries: {status.get('query_count', 0)}")
                    else:
                        print(
                            f"\n⚠ System experiencing issues ({status.get('error_count', 0)} errors)")
                elif hasattr(runner, 'get_error_status'):
                    status = runner.get_error_status()
                    if status["healthy"]:
                        print("\n✓ System healthy - No issues detected")
                    else:
                        print(
                            f"\n⚠ System experiencing issues ({status['consecutive_errors']} consecutive errors)")
                continue

            # Process the query
            print("\n🔍 Processing your query...")
            if USE_MULTI_AGENT:
                print("  [Orchestrator → Analyzer → Search → Credibility]")
            print()

            # Different handling for multi vs single agent
            if USE_MULTI_AGENT:
                result = await runner.process_query_async(user_input)
                response = result["response"]

                # Show agents used
                if result.get("agents_used"):
                    agents = result["agents_used"]
                    print(f"Agents used: {' → '.join(agents)}")

                # Show metadata
                if result.get("metadata"):
                    meta = result["metadata"]
                    if meta.get("processing_time"):
                        print(
                            f"Processing time: {meta['processing_time']:.2f}s")
            else:
                response = await runner.process_query_async(user_input)

            print("=" * 60)
            print(response)
            print("=" * 60)

            # Show health status if there were errors
            status = runner.get_error_status()
            if not status["healthy"]:
                print(
                    f"\n⚠ Note: System has experienced {status['consecutive_errors']} recent errors")

        except KeyboardInterrupt:
            print("\n\nThank you for using InfoShield AI. Stay safe!")
            break
        except Exception as e:
            logging.error(
                f"Interactive mode error: {type(e).__name__}: {str(e)}")
            print(f"\n⚠ An unexpected error occurred. Please try again.")
            print("For emergencies, contact local emergency services (911/112) directly.")
            print("Type /help for assistance.")


async def single_query_mode(query: str):
    """Process a single query and exit."""
    import io

    if not check_api_key():
        sys.exit(1)

    print(f"Processing: {query}")
    mode = "Multi-Agent" if USE_MULTI_AGENT else "Single-Agent"
    print(f"Mode: {mode}\n")

    # Capture and filter ADK diagnostic messages
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()

    try:
        if USE_MULTI_AGENT:
            from infoshield_ai.agents.runner import MultiAgentRunner
            runner = MultiAgentRunner(enable_human_review=True)
            result = await runner.process_query_async(query)
            response = result["response"]
            agents_used = result.get("agents_used", [])
            metadata = result.get("metadata", {})
        else:
            from infoshield_ai.agent import run_query_async
            response = await run_query_async(query)
            agents_used = []
            metadata = {}
    finally:
        # Restore stdout and filter out ADK messages
        sys.stdout = old_stdout
        output = buffer.getvalue()
        # Filter out the app name mismatch message
        for line in output.split('\n'):
            if 'App name mismatch' not in line and 'implies app name' not in line:
                if line.strip():
                    print(line)

    # Show agent info for multi-agent mode
    if USE_MULTI_AGENT and agents_used:
        print(f"Agents used: {' → '.join(agents_used)}")
        if metadata.get("processing_time"):
            print(f"Processing time: {metadata['processing_time']:.2f}s")

    print("\nRESPONSE:")
    print("-" * 60)
    print(response)
    print("-" * 60)


def main():
    """Main entry point."""
    # Ensure data directory exists
    from infoshield_ai.config import DATA_DIR
    DATA_DIR.mkdir(exist_ok=True)

    # Check for command line query
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        asyncio.run(single_query_mode(query))
    else:
        # Interactive mode
        asyncio.run(interactive_mode())


if __name__ == "__main__":
    main()
