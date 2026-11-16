# Quick troubleshooting

## OpenSearch will not start
- Make sure Docker Desktop is running.
- Give Docker Desktop at least 4 GB memory (6 GB is safer for this demo).
- On Windows, OpenSearch may require `vm.max_map_count` support through Docker Desktop/WSL2.
- Check: `docker compose logs opensearch`.

## API says index does not exist / no results
- Generate contracts: `python scripts/generate_contracts.py`
- Wait for OpenSearch: open `http://localhost:9200`
- Run ingestion again: `python scripts/ingest.py`
- Confirm the index exists: `http://localhost:9200/_cat/indices?v`

## Azure OpenAI errors
- Check the endpoint ends with `/` and the key is current.
- `AZURE_OPENAI_CHAT_DEPLOYMENT` must be your deployment name.
- Check `AZURE_OPENAI_API_VERSION` matches the API version enabled for your resource.
- Without Azure values, local extractive mode is expected and clearly labelled.

## First embedding run is slow
The Sentence Transformers model is downloaded on first use. Keep internet access available for the first run and allow a few minutes.

## Docker API cannot reach OpenSearch
Inside Docker Compose, the API must use host `opensearch`, not `localhost`. The Compose file sets this automatically.

## Shut down local resources
`docker compose down` stops containers.
`docker compose down -v` also deletes the local OpenSearch index data.
