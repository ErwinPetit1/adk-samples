import asyncio

import aiohttp
from google.adk.artifacts import InMemoryArtifactService

from google.adk.runners import Runner
from blogger_agent.agent import root_agent
from google.genai import types as genai_types
from google.adk.sessions import DatabaseSessionService
from blogger_agent.config import config

async def fetch_image(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.read()
            else:
                raise Exception(f"Erreur lors du téléchargement : {response.status}")

async def build_parts(query, artifact_service=None, app_name=None, user_id=None, session_id=None):
    """Build parts from query object with content and optional image URL"""
    parts = [genai_types.Part.from_text(text=query['content'])]

    if 'url' in query and query['url']:
        # Sauver l'image comme artifact si le service est fourni
        if artifact_service and app_name and user_id and session_id:


            print(">>> File uploading on artifact service")
            filename = "test-erwin.jpg"#f"query_image_{hash(query['url']) % 10000}.jpg"
            image_data = await fetch_image(query['url'])

            # Créer le Part pour sauver (avec inline_data)
            temp_artifact = genai_types.Part(
                inline_data=genai_types.Blob(
                    data=image_data,
                    mime_type="image/jpeg"
                )
            )

            # Sauver dans l'artifact service
            #await artifact_service.save_artifact(
            #    filename=filename,
            #    artifact=temp_artifact,
            #    session_id=session_id,
            #    app_name=app_name,
            #    user_id=user_id,
            #)
            #print(">>> File uploaded successfully")

            parts.append(temp_artifact)  # temp_artifact a inline_data
        else :
            print(">>> Using inline_data file")
            inline_image_data = await fetch_image(query['url'])
            inline_image_part = genai_types.Part(
                inline_data=genai_types.Blob(
                    data=inline_image_data,
                    mime_type="image/jpeg"
                )
            )
            parts.append(inline_image_part)

    #print(parts)
    return parts


async def main():

    """Runs the agent with a sample query."""
    session_service = DatabaseSessionService(db_url=config.database_url)
    artifact_service = InMemoryArtifactService()

    app_name="app"
    session_id="session-erwin-10"
    user_id="user-erwin"

    existing_session = await session_service.get_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )

    if existing_session:
        print(">>> Use existing session")
    else:
        await session_service.create_session(
            app_name=app_name, user_id=user_id, session_id=session_id
        )

    runner = Runner(
        agent=root_agent, app_name=app_name, session_service=session_service, artifact_service=artifact_service
    )


    queries = [
        {
            "content": "Describe the image.",
            "url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR4c1y_7gy2crn2Ll_ZSWzcqb0WDZFuBnFTeQ&s"
        }
    ]


    for query in queries:
        print(f">>> {query['content']}")

        # Construire les parts avec content + image éventuelle (et sauver comme artifact)
        parts = await build_parts(
            query,
            artifact_service=artifact_service,
            app_name=app_name,
            user_id=user_id,
            session_id=session_id
        )

        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=genai_types.Content(
                role="user",
                parts=parts
            ),
        ):
            if event.is_final_response() and event.content and event.content.parts:
                print(event.content.parts[0].text)


if __name__ == "__main__":
    asyncio.run(main())
