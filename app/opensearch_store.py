
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
import boto3

from app.config import get_settings


def get_client():
    """
    Create and return an OpenSearch client.

    Supports:
    1. AWS OpenSearch with username/password authentication.
    2. AWS OpenSearch with IAM authentication.
    3. Local OpenSearch for development.
    """
    s = get_settings()

    host = s.search_host

    use_aws_auth = (
        s.aws_opensearch_use_aws_auth
        and bool(s.aws_opensearch_host)
    )

    auth = None

    if use_aws_auth:
        credentials = boto3.Session().get_credentials()

        service = (
            "aoss"
            if "aoss.amazonaws.com" in host
            else "es"
        )

        auth = AWSV4SignerAuth(
            credentials,
            s.aws_region,
            service
        )

    elif s.search_username and s.search_password:
        auth = (
            s.search_username,
            s.search_password
        )

    return OpenSearch(
        hosts=[
            {
                "host": host,
                "port": 443 if s.use_ssl else s.opensearch_port
            }
        ],
        http_auth=auth,
        use_ssl=s.use_ssl,
        verify_certs=(
            s.opensearch_verify_certs
            if s.use_ssl
            else False
        ),
        connection_class=RequestsHttpConnection,
        timeout=60,
        max_retries=3,
        retry_on_timeout=True,
    )


def create_index(client=None):
    """
    Create the supplier contract vector index
    if it does not already exist.
    """

    s = get_settings()

    if client is None:
        client = get_client()

    index_name = s.opensearch_index

    if client.indices.exists(index=index_name):
        print(f"Index '{index_name}' already exists.")
        return

    body = {
        "settings": {
            "index": {
                "knn": True,
                "number_of_shards": 1,
                "number_of_replicas": 2
            }
        },

        "mappings": {
            "properties": {

                "chunk_id": {
                    "type": "keyword"
                },

                "text": {
                    "type": "text"
                },

                "embedding": {
                    "type": "knn_vector",
                    "dimension": 384,
                    "method": {
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                        "engine": "faiss",
                        "parameters": {
                            "ef_construction": 128,
                            "m": 16
                        }
                    }
                },

                "supplier": {
                    "type": "keyword"
                },

                "category": {
                    "type": "keyword"
                },

                "start_date": {
                    "type": "date"
                },

                "end_date": {
                    "type": "date"
                },

                "contract_value": {
                    "type": "float"
                },

                "auto_renew": {
                    "type": "boolean"
                },

                "notice_days": {
                    "type": "integer"
                },

                "clause": {
                    "type": "keyword"
                },

                "clause_type": {
                    "type": "keyword"
                },

                "source": {
                    "type": "keyword"
                },

                "contract_id": {
                    "type": "keyword"
                }
            }
        }
    }

    client.indices.create(
        index=index_name,
        body=body
    )

    print(f"Created OpenSearch index: {index_name}")


def index_chunks(chunks: list[dict]):
    """
    Index contract chunks and their embeddings
    into Amazon OpenSearch.
    """

    from opensearchpy.helpers import bulk

    s = get_settings()

    client = get_client()

    create_index(client)

    actions = []

    for chunk in chunks:

        actions.append({
            "_index": s.opensearch_index,
            "_id": chunk["chunk_id"],
            "_source": chunk
        })

    if actions:

        success, errors = bulk(
            client,
            actions,
            request_timeout=120,
            raise_on_error=False
        )

        if errors:
            raise RuntimeError(
                f"OpenSearch indexing errors: {errors[:5]}"
            )

        client.indices.refresh(
            index=s.opensearch_index
        )

        print(f"Successfully indexed {success} chunks.")

    return len(actions)
