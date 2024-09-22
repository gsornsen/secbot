import json
from typing import Optional

from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from chainlit.user import PersistedUser


class CustomSQLAlchemyDataLayer(SQLAlchemyDataLayer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def get_user(self, identifier: str) -> Optional[PersistedUser]:
        query = "SELECT * FROM users WHERE identifier = :identifier"
        parameters = {"identifier": identifier}
        result = await self.execute_sql(query=query, parameters=parameters)
        if result and isinstance(result, list):
            user_data = result[0]

            metadata = user_data.get("metadata", {})
            if isinstance(metadata, str):
                metadata = json.loads(metadata)

            assert isinstance(metadata, dict)
            assert isinstance(user_data["id"], str)
            assert isinstance(user_data["identifier"], str)
            assert isinstance(user_data["createdAt"], str)

            return PersistedUser(
                id=user_data["id"],
                identifier=user_data["identifier"],
                createdAt=user_data["createdAt"],
                metadata=metadata,
            )
        return None
