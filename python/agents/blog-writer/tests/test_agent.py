import asyncio

from google.adk.runners import Runner
from blogger_agent.agent import root_agent
from google.genai import types as genai_types
from google.adk.sessions import DatabaseSessionService
from blogger_agent.config import config


async def main():

    """Runs the agent with a sample query."""
    session_service = DatabaseSessionService(db_url=config.database_url)

    session_id="session-erwin-3"
    user_id="user-erwin"

    existing_session = await session_service.get_session(
        app_name="app",
        user_id=user_id,
        session_id=session_id,
    )

    if existing_session:
        print("Existing sessions:")
        print(existing_session)
    else:
        await session_service.create_session(
            app_name="app", user_id=user_id, session_id=session_id
        )


    runner = Runner(
        agent=root_agent, app_name="app", session_service=session_service
    )


    queries = [
        "I want to understand seagulls.",
    ]

    for query in queries:
        print(f">>> {query}")
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=genai_types.Content(
                role="user", 
                parts=[genai_types.Part.from_text(text=query)]
            ),
        ):
            if event.is_final_response() and event.content and event.content.parts:
                print(event.content.parts[0].text)


if __name__ == "__main__":
    asyncio.run(main())
