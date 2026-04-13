from unittest.mock import patch

from django.test import SimpleTestCase
from sqlalchemy.exc import IntegrityError

from apps.search import vectorstore


class VectorStoreTests(SimpleTestCase):
    def tearDown(self):
        vectorstore._VECTOR_STORE = None

    @patch("apps.search.vectorstore.time.sleep")
    @patch("apps.search.vectorstore.build_vector_store")
    def test_get_vector_store_retries_when_schema_already_exists(
        self,
        mock_build_vector_store,
        mock_sleep,
    ):
        retry_error = IntegrityError(
            "CREATE TABLE langchain_pg_collection",
            {},
            Exception(
                'duplicate key value violates unique constraint "pg_type_typname_nsp_index"'
            ),
        )
        created_store = object()
        mock_build_vector_store.side_effect = [retry_error, created_store]

        store = vectorstore.get_vector_store()

        self.assertIs(store, created_store)
        self.assertEqual(mock_build_vector_store.call_count, 2)
        mock_sleep.assert_called_once_with(0.5)

    def test_should_retry_vector_store_initialization_matches_duplicate_schema_error(self):
        retry_error = IntegrityError(
            "CREATE TABLE langchain_pg_collection",
            {},
            Exception("duplicate key value violates unique constraint pg_type_typname_nsp_index"),
        )

        self.assertTrue(vectorstore.should_retry_vector_store_initialization(retry_error))
