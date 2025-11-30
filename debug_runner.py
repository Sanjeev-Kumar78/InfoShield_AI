#!/usr/bin/env python
"""InfoShield AI Debug Runner.

Development tool to visualize query flow through the agent.
Shows all events, tool calls, and model interactions in real-time.
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment
load_dotenv(override=True)
os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'False'

# ANSI color codes for terminal output


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    GRAY = '\033[90m'


def print_header(text: str):
    """Print a styled header."""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'═' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}  {text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'═' * 70}{Colors.END}\n")


def print_step(step_num: int, title: str, details: str = ""):
    """Print a workflow step."""
    print(f"{Colors.CYAN}┌─ Step {step_num}: {title}{Colors.END}")
    if details:
        for line in details.split('\n'):
            print(f"{Colors.GRAY}│  {line}{Colors.END}")
    print(f"{Colors.CYAN}└{'─' * 50}{Colors.END}")


def print_event(event_type: str, content: str, color: str = Colors.BLUE):
    """Print an event with styling."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(
        f"{Colors.GRAY}[{timestamp}]{Colors.END} {color}{event_type}{Colors.END}")
    if content:
        # Indent content
        for line in content.split('\n')[:20]:  # Limit lines
            print(f"  {line}")
        if len(content.split('\n')) > 20:
            print(f"  {Colors.GRAY}... (truncated){Colors.END}")


def print_tool_call(tool_name: str, args: dict):
    """Print a tool call with details."""
    print(f"\n{Colors.YELLOW}🔧 TOOL CALL: {tool_name}{Colors.END}")
    print(f"{Colors.GRAY}   Arguments:{Colors.END}")
    for key, value in args.items():
        # Truncate long values
        str_value = str(value)
        if len(str_value) > 100:
            str_value = str_value[:100] + "..."
        print(f"     {key}: {str_value}")


def print_tool_response(tool_name: str, response: str):
    """Print a tool response."""
    print(f"\n{Colors.GREEN}✓ TOOL RESPONSE: {tool_name}{Colors.END}")
    # Show first 500 chars of response
    if len(response) > 500:
        print(f"  {response[:500]}...")
        print(f"  {Colors.GRAY}[{len(response)} total chars]{Colors.END}")
    else:
        print(f"  {response}")


async def run_debug_query(query: str):
    """Run a query with full debug output showing the flow."""

    from google.adk.agents import Agent
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.adk.tools import google_search
    from google.genai import types
    import uuid

    # Import config directly to avoid circular import with agent module
    MODEL_ID = "gemini-2.0-flash"

    print_header("INFOSHIELD AI - DEBUG MODE")

    # Step 1: Query Input
    print_step(1, "QUERY RECEIVED", f"User Query: {query}")

    # Step 2: Agent Configuration
    print_step(2, "AGENT CONFIGURATION", f"""
Model: {MODEL_ID}
Tools: [google_search]
App Name: infoshield_ai""")

    # Create agent with inline instruction (avoid importing from agent.py to prevent circular import)
    from datetime import datetime as dt
    CURRENT_DATE = dt.now().strftime("%B %d, %Y")

    AGENT_INSTRUCTION = f"""You are InfoShield AI, a disaster information verification assistant.
Your job is to help users by verifying disaster-related queries and providing accurate, 
actionable information.

**IMPORTANT: Today's date is {CURRENT_DATE}. Always focus on CURRENT, REAL-TIME information.**

## WORKFLOW:
1. Analyze the query for urgency and location
2. Search for CURRENT information using Google Search
3. Evaluate credibility based on sources
4. Provide verified response with sources

## RESPONSE FORMAT:
1. **Status**: VERIFIED / UNVERIFIED / UNDER REVIEW
2. **Urgency Level**: Low / Medium / High / Critical
3. **Summary**: Brief answer based on CURRENT information
4. **Safety Advice**: If applicable
5. **Sources**: Where the information came from

Always cite sources and remind users to contact emergency services (911, 112) for life-threatening emergencies.
"""

    agent = Agent(
        name="infoshield_ai",
        model=MODEL_ID,
        description="Disaster information verification assistant",
        instruction=AGENT_INSTRUCTION,
        tools=[google_search]
    )

    # Step 3: Session Setup
    session_service = InMemorySessionService()
    session_id = f"debug_{uuid.uuid4().hex[:8]}"
    user_id = "debug_user"

    session = await session_service.create_session(
        app_name=agent.name,
        user_id=user_id,
        session_id=session_id
    )

    print_step(3, "SESSION CREATED", f"""
Session ID: {session_id}
User ID: {user_id}""")

    # Create runner
    runner = Runner(
        agent=agent,
        app_name=agent.name,
        session_service=session_service
    )

    # Prepare message
    content = types.Content(
        role='user',
        parts=[types.Part(text=query)]
    )

    # Step 4: Processing Events
    print_step(4, "PROCESSING QUERY", "Streaming events from model...")
    print()

    event_count = 0
    tool_calls = 0
    final_response = ""

    # Check for verbose mode
    verbose = os.environ.get('DEBUG_VERBOSE', '0') == '1'

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content
    ):
        event_count += 1

        # Verbose mode: show raw event
        if verbose:
            print(
                f"{Colors.GRAY}[Event #{event_count}] {type(event).__name__}{Colors.END}")
            if hasattr(event, '__dict__'):
                for k, v in event.__dict__.items():
                    print(f"  {k}: {str(v)[:100]}...")

        # Get event attributes
        event_type = type(event).__name__

        # Check for different event types
        if hasattr(event, 'content') and event.content:
            content_obj = event.content

            # Check for tool calls in parts
            if hasattr(content_obj, 'parts') and content_obj.parts:
                for part in content_obj.parts:
                    # Tool call
                    if hasattr(part, 'function_call') and part.function_call:
                        tool_calls += 1
                        fc = part.function_call
                        tool_name = fc.name if hasattr(fc, 'name') else str(fc)
                        tool_args = fc.args if hasattr(fc, 'args') else {}
                        print_tool_call(tool_name, dict(
                            tool_args) if tool_args else {})

                    # Tool response
                    elif hasattr(part, 'function_response') and part.function_response:
                        fr = part.function_response
                        tool_name = fr.name if hasattr(
                            fr, 'name') else 'unknown'
                        response_text = str(fr.response) if hasattr(
                            fr, 'response') else str(fr)
                        print_tool_response(tool_name, response_text)

                    # Text content
                    elif hasattr(part, 'text') and part.text:
                        if event.is_final_response():
                            final_response = part.text
                        else:
                            # Intermediate text
                            print_event("MODEL THINKING", part.text[:200] + "..." if len(
                                part.text) > 200 else part.text, Colors.GRAY)

        # Show event marker
        if event.is_final_response():
            print_event("FINAL RESPONSE", "", Colors.GREEN)

    # Step 5: Summary
    print()
    print_step(5, "EXECUTION SUMMARY", f"""
Total Events: {event_count}
Tool Calls: {tool_calls}
Response Length: {len(final_response)} chars""")

    # Step 6: Final Response
    print()
    print(f"{Colors.BOLD}{Colors.GREEN}{'═' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.GREEN}  FINAL RESPONSE{Colors.END}")
    print(f"{Colors.BOLD}{Colors.GREEN}{'═' * 70}{Colors.END}")
    print()
    print(final_response)
    print()
    print(f"{Colors.GRAY}{'─' * 70}{Colors.END}")

    return final_response


def show_usage():
    """Show usage information."""
    print(f"""
{Colors.BOLD}InfoShield AI - Debug Runner{Colors.END}
{Colors.GRAY}Development tool to visualize query flow through the agent.{Colors.END}

{Colors.CYAN}Usage:{Colors.END}
  python debug_runner.py [query]        Run a query with debug output
  python debug_runner.py --web          Start ADK Web UI (best for visualization)
  python debug_runner.py --verbose      Enable verbose mode (show raw events)

{Colors.CYAN}Examples:{Colors.END}
  python debug_runner.py "Is there flooding in India?"
  python debug_runner.py --web
  DEBUG_VERBOSE=1 python debug_runner.py "earthquake in Japan"

{Colors.CYAN}Environment Variables:{Colors.END}
  DEBUG_VERBOSE=1    Show raw event details
""")


def start_adk_web():
    """Start the ADK Web UI for visual debugging."""
    import subprocess

    print(f"{Colors.BOLD}Starting ADK Web UI...{Colors.END}")
    print(f"{Colors.GRAY}This provides a visual interface to see agent flow.{Colors.END}")
    print()
    print(f"{Colors.YELLOW}Open http://localhost:8000 in your browser{Colors.END}")
    print(f"{Colors.GRAY}Press Ctrl+C to stop{Colors.END}")
    print()

    # Run adk web command using Python module
    subprocess.run(
        [sys.executable, "-m", "google.adk.cli", "web", "infoshield_ai"],
        cwd=str(Path(__file__).parent)
    )


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == '--help' or arg == '-h':
            show_usage()
            return

        if arg == '--web':
            start_adk_web()
            return

        if arg == '--verbose':
            os.environ['DEBUG_VERBOSE'] = '1'
            if len(sys.argv) > 2:
                query = ' '.join(sys.argv[2:])
            else:
                query = input(
                    f"{Colors.CYAN}Enter your query: {Colors.END}").strip()
        else:
            query = ' '.join(sys.argv[1:])
    else:
        show_usage()
        print()
        query = input(
            f"{Colors.CYAN}Enter your query (or 'web' for Web UI): {Colors.END}").strip()

        if query.lower() == 'web':
            start_adk_web()
            return

        if not query:
            print("No query provided. Exiting.")
            return

    asyncio.run(run_debug_query(query))


if __name__ == "__main__":
    main()
