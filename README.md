# SuperKart Sales Forecasting - Containerized Deployment

Flask REST API (backend) + Streamlit UI (frontend) serving a tuned Random Forest that forecasts
`Product_Store_Sales_Total` for a product in a SuperKart store.

| Folder / file          | Purpose                                             |
|------------------------|-----------------------------------------------------|
| `backend_files/`       | Flask API, serialized model, requirements, Dockerfile |
| `frontend_files/`      | Streamlit app, requirements, Dockerfile              |
| `docker-compose.yml`   | Runs both containers on the `superkart-net` network  |
| `deploy_containers.sh` | Same as compose, with plain `docker` commands        |

## Run in a GitHub Codespace
```bash
docker compose up --build -d     # or: bash deploy_containers.sh
```
- Backend API: port **7860** (`GET /`, `GET /v1/schema`, `POST /v1/predict`, `POST /v1/predictbatch`)
- Frontend UI: port **8501**

Set port 7860 to *Public* in the Ports tab to call the API from outside the Codespace.
