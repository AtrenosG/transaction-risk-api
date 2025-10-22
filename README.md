# Transaction Risk Scoring & Financial Behavior Analytics Backend

A comprehensive FastAPI backend that analyzes user transactions to generate detailed risk assessments and financial behavior analytics. This system integrates with Supabase for data storage and provides endpoints for both UI visualization and external service integration.

## 🚀 Features

- **Risk Assessment**: Comprehensive analysis of transaction patterns to generate risk scores (0-100 scale)
- **Financial Analytics**: Detailed insights into spending patterns, income volatility, and savings behavior
- **Behavioral Analysis**: Understanding of user financial habits and stability indicators
- **Loan Eligibility**: Automated assessment based on financial behavior patterns
- **External Integration**: Webhook support for Agentic AI and other backend services
- **Real-time Processing**: Fast analysis of 180 days of transaction history
- **Production Ready**: Containerized deployment with comprehensive error handling

## 🏗️ Architecture

```
├── app.py                      # FastAPI main application
├── transaction_risk_model.py   # ML analysis engine
├── models/
│   └── schemas.py             # Pydantic data models
├── routes/
│   └── api.py                 # API endpoints
├── services/
│   ├── supabase_service.py    # Database operations
│   └── webhook_service.py     # External integrations
├── utils/
│   └── helpers.py             # Utility functions
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container configuration
└── .env.example              # Environment variables template
```

## 📊 Core Metrics

The ML model computes and returns comprehensive financial analytics:

### Overall Risk Assessment
- **Overall Risk Score**: 0-100 scale (lower = better)
- **Risk Category**: Low, Medium, High
- **Loan Eligibility**: Boolean with detailed reasoning

### Financial Summary
- Monthly spending and savings analysis
- Income and spending volatility metrics
- Financial consistency score
- Transaction frequency analysis
- Total savings calculation

### Behavioral Analysis
- Spending pattern distribution by category
- Essential vs discretionary spending ratios
- Weekend vs weekday spending patterns
- High-risk spending identification
- Spending stability indicators

### Risk Assessment Details
- Risk scores for different spending types
- Loan eligibility factors
- Behavioral pattern insights

## 🛠️ Tech Stack

- **FastAPI**: Modern Python web framework
- **Supabase**: PostgreSQL database with real-time capabilities
- **Pydantic**: Data validation and serialization
- **Pandas/NumPy**: Data processing and analysis
- **Scikit-learn**: Machine learning utilities
- **HTTPX**: Async HTTP client for webhooks
- **Uvicorn**: ASGI server for production

## 📋 Database Schema

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    account_no TEXT UNIQUE NOT NULL,
    ifsc_code TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Transactions Table
```sql
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    date TIMESTAMP NOT NULL,
    description TEXT,
    amount DECIMAL(15,2) NOT NULL,
    type TEXT CHECK (type IN ('credit', 'debit')),
    category TEXT,
    upi_app TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### ML Results Table
```sql
CREATE TABLE ml_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    risk_score DECIMAL(5,2) NOT NULL,
    risk_category TEXT CHECK (risk_category IN ('low', 'medium', 'high')),
    eligible BOOLEAN NOT NULL,
    eligibility_reason TEXT,
    metrics JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 🚦 API Endpoints

### GET `/api/analyze`
Analyze user transactions and generate risk assessment.

**Parameters:**
- `account_no` (required): User's bank account number
- `ifsc` (required): Bank IFSC code

**Response:**
```json
{
  "success": true,
  "data": {
    "overall_risk_score": 68.5,
    "risk_category": "Medium",
    "loan_eligibility": true,
    "eligibility_reason": "Stable income and low high-risk spending",
    "financial_summary": { ... },
    "behavioral_analysis": { ... },
    "risk_assessment_details": { ... },
    "created_at": "2024-01-15T10:30:00Z"
  },
  "message": "Analysis completed successfully",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### GET `/api/results/{user_id}`
Retrieve latest analysis results for a specific user.

### POST `/api/webhook`
Manually trigger webhook for external service integration.

### GET `/api/health`
Health check endpoint for monitoring.

### GET `/`
Root endpoint with API information.

## 🔧 Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd transaction-risk-analytics
```

### 2. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# Required variables:
# - SUPABASE_URL
# - SUPABASE_KEY
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
# Development
python app.py

# Or with uvicorn
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## 🐳 Docker Deployment

### Build Image
```bash
docker build -t transaction-risk-api .
```

### Run Container
```bash
docker run -p 8000:8000 --env-file .env transaction-risk-api
```

### Docker Compose (Optional)
```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
      - WEBHOOK_URL=${WEBHOOK_URL}
    restart: unless-stopped
```

## ☁️ Production Deployment

### Render
1. Connect your GitHub repository
2. Set environment variables in Render dashboard
3. Deploy with Docker or Python runtime

### Railway
1. Connect repository to Railway
2. Configure environment variables
3. Deploy automatically on push

### Heroku
```bash
# Install Heroku CLI and login
heroku create your-app-name
heroku config:set SUPABASE_URL=your-url
heroku config:set SUPABASE_KEY=your-key
git push heroku main
```

## 🔐 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_KEY` | Supabase anon key | Yes |
| `WEBHOOK_URL` | External webhook URL | No |
| `WEBHOOK_SECRET` | Webhook authentication secret | No |
| `FRONTEND_URL` | Frontend domain for CORS | No |
| `HOST` | Server host (default: 0.0.0.0) | No |
| `PORT` | Server port (default: 8000) | No |
| `DEBUG` | Enable debug mode | No |

## 🧪 Testing

### Manual Testing
```bash
# Health check
curl http://localhost:8000/api/health

# Analyze transactions
curl "http://localhost:8000/api/analyze?account_no=1234567890&ifsc=SBIN0001234"

# Get results
curl http://localhost:8000/api/results/{user_id}
```

### Automated Testing (Optional)
```bash
pip install pytest pytest-asyncio
pytest tests/
```

## 📈 ML Model Details

The transaction risk model analyzes multiple factors:

### Risk Factors (Increase Risk Score)
- High income/spending volatility
- Excessive discretionary spending
- High weekend spending ratio
- Low essential spending ratio
- Negative savings rate
- Inconsistent financial behavior

### Protective Factors (Decrease Risk Score)
- Stable income patterns
- High essential spending ratio
- Positive savings rate
- Consistent transaction patterns
- Controlled high-risk spending

### Scoring Algorithm
```python
risk_score = (
    volatility_component +
    behavioral_risk_component +
    savings_risk_component +
    consistency_penalty +
    frequency_adjustment
)
```

## 🔗 Integration Examples

### Frontend Integration (React/Next.js)
```javascript
const analyzeUser = async (accountNo, ifsc) => {
  const response = await fetch(
    `${API_URL}/api/analyze?account_no=${accountNo}&ifsc=${ifsc}`
  );
  const result = await response.json();
  return result.data;
};
```

### Webhook Handler (Node.js/Express)
```javascript
app.post('/webhook', (req, res) => {
  const { user_id, analysis_result, timestamp } = req.body;
  
  // Process the analysis result
  console.log(`Received analysis for user ${user_id}`);
  console.log(`Risk Score: ${analysis_result.overall_risk_score}`);
  
  res.status(200).json({ received: true });
});
```

## 🚨 Error Handling

The API provides comprehensive error responses:

```json
{
  "success": false,
  "data": null,
  "message": "User not found with account_no: 1234567890 and ifsc: SBIN0001234",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

Common error codes:
- `404`: User or data not found
- `422`: Invalid input parameters
- `500`: Internal server error
- `503`: Service unavailable

## 📚 API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the error logs for debugging

## 🔄 Version History

- **v1.0.0**: Initial release with core functionality
  - Transaction analysis engine
  - Risk scoring algorithm
  - Supabase integration
  - Webhook support
  - Docker containerization
