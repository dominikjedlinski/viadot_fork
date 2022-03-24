from .base import SQL
from typing import List


class SQLServer(SQL):
    DEFAULT_SCHEMA = "dbo"

    def __init__(
        self,
        config_key="SQL_SERVER",
        driver="ODBC Driver 17 for SQL Server",
        *args,
        **kwargs,
    ):
        super().__init__(*args, driver=driver, config_key=config_key, **kwargs)

    @property
    def schemas(self) -> List[str]:
        """Returns list of schemas"""
        schemas_tuples = self.run("SELECT s.name as schema_name from sys.schemas s")
        return [schema_tuple[0] for schema_tuple in schemas_tuples]

    @property
    def tables(self) -> List[str]:
        """Returns list of tables"""
        tables_tuples = self.run(
            "SELECT schema_name(t.schema_id), t.name FROM sys.tables t"
        )
        return [".".join(row) for row in tables_tuples]

    def exists(self, table: str, schema: str = None) -> bool:
        """Check whether a table exists.
        Args:
            table (str): The table to be checked.
            schema (str, optional): The schema whethe the table is located. Defaults to 'dbo'.
        Returns:
            bool: Whether the table exists.
        """

        if not schema:
            schema = self.DEFAULT_SCHEMA

        list_table_info_query = f"""
            SELECT *
            FROM sys.tables t
            JOIN sys.schemas s
                ON t.schema_id = s.schema_id
            WHERE s.name = '{schema}' AND t.name = '{table}'
        """
        exists = bool(self.run(list_table_info_query))
        return exists
