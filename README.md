# Billing Records Archival System

A comprehensive solution for archiving billing records from Azure Cosmos DB to Azure Blob Storage to reduce storage costs while maintaining seamless API access to archived data.

## 🏗️ Architecture Overview

![Billing Archival System Architecture](Screenshot%202025-07-04%20at%2011.09.10%20AM.png)

*Architecture diagram showing the complete billing archival system flow*

### System Components:

```
                 ┌────────────────────┐
                 │  Client / API      │
                 └────────┬───────────┘
                          │
                          ▼
            ┌──────────────────────────┐
            │  Billing Read/Write API  │  (FastAPI)
            └───────┬──────────────────┘
                    │
        ┌───────────▼────────────┐
        │ Azure Cosmos DB (Live) │  <-- Recent records (≤ 3 months)
        └──────┬─────────────────┘
               │
     ┌─────────▼──────────┐
     │ Check Record Age   │
     └─────────┬──────────┘
               │
     ┌─────────▼─────────────┐
     │ Azure Blob Storage    │  <-- Archived records (> 3 months)
     └───────────────────────┘
               ▲
       ┌───────┴─────────┐
       │ Archival Logic  │
       │ Azure Function  │ (scheduled daily)
       └─────────────────┘
```

## ✨ Features

- **Automatic Archival**: Scheduled archival of records older than 3 months
- **Seamless API Access**: Records are retrieved from either Cosmos DB or Blob Storage transparently
- **Cost Optimization**: Significant cost savings by moving cold data to cheaper Blob Storage
- **Multi-Tier Storage**: Automatic lifecycle management (Hot → Cool → Archive → Delete)
- **Data Integrity**: Archive index maintains references to archived records
- **Restoration Capability**: Ability to restore archived records back to Cosmos DB
- **Monitoring**: Statistics and health check endpoints
- **Batch Processing**: Efficient processing of large datasets
- **Production Ready**: Comprehensive error handling, logging, and deployment scripts

## 📁 Project Structure

```
├── api.py                 # FastAPI application with billing endpoints
├── archival_service.py    # Main archival orchestration logic
├── cosmos_client.py       # Cosmos DB operations wrapper
├── blob_client.py         # Azure Blob Storage operations wrapper
├── models.py              # Pydantic models for data validation
├── config.py              # Configuration management
├── azure_function.py      # Azure Function for scheduled archival
├── function_app.json      # Azure Function configuration
├── blob_lifecycle_policy.json  # Blob storage lifecycle policy
├── deploy_blob_policy.py  # Script to deploy lifecycle policy
├── requirements.txt       # Python dependencies
├── env.example           # Environment variables template
├── test_example.py       # Comprehensive test suite
├── deploy.py             # Automated deployment script
└── README.md             # This file
```

## 🚀 Implementation Steps

### 1. Archival Process (Timer Trigger Function)
Run daily or weekly to move records older than 3 months to Azure Blob Storage.

Delete records from Cosmos DB after successful archival.

**Pseudocode:**
```python
def archive_old_records():
    # Query old records
    old_records = cosmos_db.query("SELECT * FROM billing WHERE timestamp < GETDATE() - 90")

    for record in old_records:
        # Store record in Blob Storage
        blob_client.upload_blob(record['id'] + ".json", json.dumps(record))

        # Delete record from Cosmos DB
        cosmos_db.delete(record['id'])
```

**Azure Function Timer Trigger Example:**
```yaml
schedule: "0 0 * * * *"  # Runs daily at midnight
```

### 2. Read Routing Logic (Seamless Access via API Layer)
API first checks Cosmos DB.

If not found, fetches from Blob Storage via Azure Function.

**Pseudocode:**
```python
def get_billing_record(record_id):
    record = cosmos_db.find(record_id)
    
    if record:
        return record
    else:
        # Fallback to Blob Storage
        blob_data = blob_client.download_blob(f"{record_id}.json")
        return json.loads(blob_data)
```

### 3. Write Operations
Continue writing all new records to Cosmos DB.

No changes needed.

### 4. Blob Storage Configuration
Use Cool Tier for optimal cost since older records are infrequently accessed.

Enable lifecycle management policies to further move older blobs to the Archive Tier if needed.

**Deploy Lifecycle Policy:**
```bash
python deploy_blob_policy.py
```

**Cost Optimization Tiers:**
- **Hot tier**: ~$0.0184 per GB per month (for active data)
- **Cool tier**: ~$0.01 per GB per month (46% savings for archived data)
- **Archive tier**: ~$0.00099 per GB per month (95% savings for long-term storage)

**Lifecycle Policy Rules:**
- Move to Cool tier after 30 days
- Move to Archive tier after 90 days  
- Delete after 7 years (2555 days)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `env.example` to `.env` and fill in your Azure credentials:

```bash
cp env.example .env
```

Required environment variables:
- `COSMOS_ENDPOINT`: Your Cosmos DB endpoint URL
- `COSMOS_KEY`: Your Cosmos DB primary key
- `BLOB_CONNECTION_STRING`: Your Azure Storage connection string

### 3. Run the API

```bash
python api.py
```

The API will be available at `http://localhost:8000`

## 📚 API Endpoints

### Billing Records

- `GET /billing/{record_id}` - Retrieve a billing record (from Cosmos DB or archive)
- `POST /billing` - Create a new billing record
- `PUT /billing/{record_id}` - Update an existing billing record
- `DELETE /billing/{record_id}` - Delete a billing record

### Archival Management

- `POST /archive` - Trigger archival process (background)
- `POST /archive/sync` - Trigger archival process (synchronous)
- `POST /restore/{record_id}` - Restore archived record to Cosmos DB
- `GET /stats` - Get archival system statistics

### System

- `GET /health` - Health check endpoint

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `COSMOS_ENDPOINT` | Cosmos DB endpoint URL | Required |
| `COSMOS_KEY` | Cosmos DB primary key | Required |
| `COSMOS_DATABASE` | Database name | `billingdb` |
| `COSMOS_CONTAINER` | Main container name | `records` |
| `COSMOS_ARCHIVE_INDEX_CONTAINER` | Archive index container | `archive_index` |
| `BLOB_CONNECTION_STRING` | Azure Storage connection string | Required |
| `BLOB_CONTAINER` | Blob container name | `billing-archive` |
| `ARCHIVAL_DAYS_THRESHOLD` | Days before archival | `90` |
| `BATCH_SIZE` | Records per batch | `100` |
| `API_HOST` | API host | `0.0.0.0` |
| `API_PORT` | API port | `8000` |

## 📊 Usage Examples

### Create a Billing Record

```bash
curl -X POST "http://localhost:8000/billing" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "customer123",
    "amount": 299.99,
    "currency": "USD",
    "status": "pending",
    "description": "Monthly subscription",
    "due_date": "2024-02-15T00:00:00Z"
  }'
```

### Retrieve a Billing Record

```bash
curl "http://localhost:8000/billing/record-id-here"
```

### Trigger Archival

```bash
curl -X POST "http://localhost:8000/archive/sync"
```

### Get System Statistics

```bash
curl "http://localhost:8000/stats"
```

## 🔄 Azure Function Deployment

### 1. Create Azure Function App

```bash
# Install Azure Functions Core Tools
npm install -g azure-functions-core-tools@4

# Create function app
func init billing-archival --python
cd billing-archival

# Copy the function files
cp ../azure_function.py .
cp ../function_app.json .
```

### 2. Configure Timer Schedule

The function is configured to run daily at midnight UTC. Modify `function_app.json` to change the schedule:

```json
{
  "schedule": "0 0 0 * * *"  // Cron expression: daily at midnight UTC
}
```

### 3. Deploy to Azure

```bash
# Login to Azure
az login

# Deploy function app
func azure functionapp publish your-function-app-name
```

## 💰 Cost Optimization Deployment

### 1. Deploy Blob Lifecycle Policy

```bash
# Deploy automatic tier management
python deploy_blob_policy.py
```

This will automatically:
- Move archived records to Cool tier after 30 days (46% cost savings)
- Move to Archive tier after 90 days (95% cost savings)
- Delete after 7 years (automatic cleanup)

### 2. Monitor Cost Savings

Track your cost savings with the statistics endpoint:

```bash
curl http://localhost:8000/stats
```

## 🧪 Testing

### Manual Testing

1. Create test records with old dates
2. Trigger archival process
3. Verify records are moved to blob storage
4. Test API retrieval from both sources

### Sample Test Data

```python
from datetime import datetime, timedelta
from models import BillingRecord

# Create a record that will be archived
old_record = BillingRecord(
    id="test-old-record",
    customer_id="test-customer",
    amount=100.00,
    status="paid",
    created_at=datetime.utcnow() - timedelta(days=100),  # 100 days old
    due_date=datetime.utcnow() - timedelta(days=70)
)
```

## 📈 Monitoring

### Health Checks

- `GET /health` - Basic health check
- `GET /stats` - System statistics

### Logging

The system uses structured logging with different levels:
- `INFO`: Normal operations
- `WARNING`: Non-critical issues
- `ERROR`: Errors that need attention

### Metrics to Monitor

- Number of records in Cosmos DB vs archived
- Archival success rate
- API response times
- Storage costs

## 🔒 Security Considerations

- Store sensitive credentials in Azure Key Vault
- Use managed identities for Azure resources
- Implement proper authentication for the API
- Enable audit logging
- Use private endpoints for Cosmos DB and Storage

## 🚨 Troubleshooting

### Common Issues

1. **Configuration Errors**: Ensure all environment variables are set
2. **Permission Issues**: Verify Azure service principal permissions
3. **Network Issues**: Check firewall rules and network connectivity
4. **Storage Quotas**: Monitor blob storage quotas and limits

### Debug Mode

Enable debug logging by setting the log level:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs
3. Open an issue in the repository 