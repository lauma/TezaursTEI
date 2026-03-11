from typing import Optional

from psycopg2.extras import NamedTupleCursor

from lv.ailab.tezaurs.dbaccess.connection import DbConnection
from lv.ailab.tezaurs.dbaccess.db_config import db_connection_info


class Example:
    def __init__(self, db_id, text, hidden, source = None, token_location = None):
        self.dbID : int = db_id
        self.text : str = text
        self.hidden : bool = hidden
        self.source : Optional[str] = source
        self.tokenLocation : Optional[int] = token_location

    @staticmethod
    def fetch_examples(connection : DbConnection, parent_id : int,
                       entry_level_samples : bool = False) -> list[Example]:
        if not parent_id:
            return []
        where_clause = "sense_id"
        if entry_level_samples:
            where_clause = 'entry_id'
        cursor = connection.cursor(cursor_factory=NamedTupleCursor)
        sql_samples = f"""
    SELECT id, content, data->>'CitedSource' as source, (data->>'TokenLocation')::int as location, hidden, reason_for_hiding
    FROM {db_connection_info['schema']}.examples
    WHERE {where_clause} = {parent_id} and (NOT hidden or reason_for_hiding='not-public')
    ORDER BY hidden, order_no
    """
        cursor.execute(sql_samples)
        samples = cursor.fetchall()
        if not samples:
            return []
        result = []
        for db_sample in samples:
            sample = Example(db_sample.id, db_sample.content, db_sample.hidden,
                             db_sample.source, db_sample.location)
            result.append(sample)
        return result
