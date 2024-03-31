from superduperdb.backends.ibis.data_backend import IbisDataBackend


import typing as t
from warnings import warn

import ibis
import pandas
from ibis.backends.base import BaseBackend

from superduperdb.backends.ibis.db_helper import get_db_helper
from superduperdb.backends.ibis.field_types import FieldType, dtype
from superduperdb.backends.ibis.query import Table
from superduperdb.backends.local.artifacts import FileSystemArtifactStore
from superduperdb.backends.sqlalchemy.metadata import SQLAlchemyMetadata
from superduperdb.components.datatype import DataType
from superduperdb.components.schema import Schema

BASE64_PREFIX = 'base64:'
INPUT_KEY = '_input_id'




class PostgresDataBackend(IbisDataBackend):
    def __init__(self, conn: BaseBackend, name: str, in_memory: bool = False):
        super().__init__(conn=conn, name=name)
        self.in_memory = in_memory
        self.dialect = getattr(conn, 'name', 'base')
        self.db_helper = get_db_helper(self.dialect)

    def url(self):
        return self.conn.con.url + self.name

    def build_artifact_store(self):
        return FileSystemArtifactStore(conn='.superduperdb/artifacts/', name='ibis')

    def build_metadata(self):
        return SQLAlchemyMetadata(conn=self.conn.con, name='ibis')

    def create_ibis_table(self, identifier: str, schema: Schema):
        self.conn.create_table(identifier, schema=schema)

    def insert(self, table_name, raw_documents):
        for doc in raw_documents:
            for k, v in doc.items():
                doc[k] = self.db_helper.convert_data_format(v)
        table_name, raw_documents = self.db_helper.process_before_insert(
            table_name, raw_documents
        )
        if not self.in_memory:
            self.conn.insert(table_name, raw_documents)
        else:
            self.conn.create_table(table_name, pandas.DataFrame(raw_documents))

    def create_output_dest(
        self, predict_id: str, datatype: t.Union[FieldType, DataType]
    ):
        msg = (
            "Model must have an encoder to create with the"
            f" {type(self).__name__} backend."
        )
        assert datatype is not None, msg
        if isinstance(datatype, FieldType):
            output_type = dtype(datatype.identifier)
        else:
            output_type = datatype
        fields = {
            INPUT_KEY: dtype('string'),
            'output': output_type,
        }
        return Table(
            identifier=f'_outputs.{predict_id}',
            schema=Schema(identifier=f'_schema/{predict_id}', fields=fields),
        )

    def create_table_and_schema(self, identifier: str, mapping: dict):
        """
        Create a schema in the data-backend.
        """

        try:
            mapping = self.db_helper.process_schema_types(mapping)
            t = self.conn.create_table(identifier, schema=ibis.schema(mapping))
        except Exception as e:
            if 'exists' in str(e):
                warn("Table already exists, skipping...")
                t = self.conn.table(identifier)
            else:
                raise e
        return t

    def drop(self, force: bool = False):
        raise NotImplementedError(
            "Dropping tables needs to be done in each DB natively"
        )

    def get_table_or_collection(self, identifier):
        return self.conn.table(identifier)

    def disconnect(self):
        """
        Disconnect the client
        """

        # TODO: implement me