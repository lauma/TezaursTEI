from typing import Generator, Optional
from psycopg2.extras import NamedTupleCursor

from lv.ailab.tezaurs.dbaccess.connection import DbConnection
from lv.ailab.tezaurs.dbaccess.db_config import db_connection_info


class DictSource:
    def __init__(self, abbreviation, title, url=None, details=None):
        self.abbreviation : str = abbreviation
        self.title : str = title
        self.details : Optional[str] = details
        self.url : Optional[str] = url


    @staticmethod
    def fetch_all_sources(connection : DbConnection) -> Generator[DictSource]:
        cursor = connection.cursor(cursor_factory=NamedTupleCursor)
        sql_dict_sources = f"""
            SELECT abbr, title, url
            FROM {db_connection_info['schema']}.sources
            ORDER BY abbr ASC
        """
        cursor.execute(sql_dict_sources)
        while True:
            rows = cursor.fetchmany(1000)
            if not rows:
                break
            for row in rows:
                yield DictSource(row.abbr, row.title, row.url)


    @staticmethod
    def fetch_sources_by_esl_id(connection : DbConnection, entry_id : Optional[int] = None,
                                lexeme_id : Optional[int] = None, sense_id : Optional[int] = None) -> list[DictSource]:
        if not entry_id and not sense_id and not lexeme_id:
            return []
        cursor = connection.cursor(cursor_factory=NamedTupleCursor)
        where_clause = ""
        if entry_id:
            where_clause = f"""entry_id = {entry_id}"""
        if lexeme_id:
            if where_clause:
                where_clause = where_clause + " and "
            where_clause = where_clause + f"""lexeme_id = {lexeme_id}"""
        if sense_id:
            if where_clause:
                where_clause = where_clause + " and "
            where_clause = where_clause + f"""sense_id = {sense_id}"""
        sql_sources = f"""
    SELECT abbr, title, url, data->'sourceDetails' as details
    FROM {db_connection_info['schema']}.source_links scl
    JOIN {db_connection_info['schema']}.sources sc ON scl.source_id = sc.id
    WHERE {where_clause}
    ORDER BY order_no
    """
        cursor.execute(sql_sources)
        sources = cursor.fetchall()
        if not sources:
            return []
        result = []
        for source_row in sources:
            source = DictSource(source_row.abbr, source_row.title, source_row.url, source_row.details)
            result.append(source)
        return result
