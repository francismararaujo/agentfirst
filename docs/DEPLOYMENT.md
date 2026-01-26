# AgentFirst2 MVP - Deployment Guide

## Overview

AgentFirst2 MVP uses **GitHub Actions** as the single deployment method. This provides consistency across all devices and operating systems, with automatic deployment on every push to the main branch.

## Prerequisites

### For Development (Any Device)
- Git
- GitHub account with repository access
- Text editor/IDE (VS Code, etc.)

### AWS Account (Already Configured)
- AWS Account ID: 373527788609
- Region: us-east-1
- Credentials configured in GitHub Secrets

## Deployment Method: GitHub Actions Only

### Why GitHub Actions?
- ✅ **Multi-device**: Works on Windows, macOS, Linux
- ✅ **No local setup**: No need to install Docker, CDK, AWS CLI
- ✅ **Consistent**: Same build environment every time
- ✅ **Automatic**: Push to main → automatic deployment
- ✅ **Reliable**: Built-in rollback on failure

## Setup (One-time Configuration)

### 1. Configure GitHub Secrets

Go to your GitHub repository: `Settings > Secrets and variables > Actions`

Add these repository secrets:
```
AWS_ACCESS_KEY_ID = AKIAVN575XRAXW7IYL7B
AWS_SECRET_ACCESS_KEY = [your AWS secret access key]
AWS_REGION = us-east-1
AWS_ACCOUNT_ID = 373527788609
```

### 2. Verify Workflow File

The workflow is already configured in `.github/workflows/deploy.yml` and will:
- Run validation on every push/PR
- Deploy automatically on push to `main` branch
- Build Docker image and push to ECR
- Deploy infrastructure with CDK
- Run smoke tests
- Notify on success/failure

## Daily Development Workflow

### From Any Device (Windows/Mac/Linux):

```bash
# 1. Clone repository (first time only)
git clone https://github.com/your-username/AgentFirst.git
cd AgentFirst

# 2. Make your changes
# Edit files with any editor (VS Code, Notepad++, vim, etc.)

# 3. Commit and push
git add .
git commit -m "feat: add new feature"
git push origin main

# 4. Deployment happens automatically!
# Check progress at: https://github.com/your-username/AgentFirst/actions
```

### That's it! No other setup needed on any device.

## Monitoring Deployment

### GitHub Actions Dashboard
- Go to: `https://github.com/your-username/AgentFirst/actions`
- Click on latest workflow run
- Monitor progress in real-time
- View logs for each step

### Deployment Steps (Automatic)
1. **Validate** - Check code quality and imports
2. **Build** - Create Docker image with all dependencies
3. **Push** - Upload image to Amazon ECR
4. **Deploy** - Update Lambda function via CDK
5. **Test** - Run smoke tests on deployed API
6. **Notify** - Report success/failure

### AWS Resources (View Only)
```bash
# If you have AWS CLI installed (optional):
aws lambda get-function --function-name agentfirst-production
aws apigateway get-rest-apis --query 'items[?name==`agentfirst-api`]'
```

## Environments

### Production (Only Environment)
- **Trigger**: Push to `main` branch
- **Lambda**: 512MB memory, 30s timeout
- **DynamoDB**: On-demand billing
- **Monitoring**: Full CloudWatch + X-Ray
- **Auto-rollback**: Enabled on failure

## API Endpoints (After Deployment)

- **Health Check**: `https://d7p93u5agk.execute-api.us-east-1.amazonaws.com/prod/health`
- **Telegram Webhook**: `https://d7p93u5agk.execute-api.us-east-1.amazonaws.com/prod/webhook/telegram`
- **iFood Webhook**: `https://d7p93u5agk.execute-api.us-east-1.amazonaws.com/prod/webhook/ifood`

## Troubleshooting

### Deployment Fails
1. Check GitHub Actions logs
2. Look for error in specific step
3. Common issues:
   - AWS credentials expired
   - Code syntax errors
   - Docker build failures

### Lambda Not Responding
1. Check CloudWatch logs: `/aws/lambda/agentfirst-production`
2. Verify API Gateway endpoint
3. Check X-Ray traces for errors

### Rollback (Automatic)
- GitHub Actions automatically rolls back on failure
- Previous Lambda version is restored
- No manual intervention needed

## Performance Monitoring

### CloudWatch Metrics (Automatic)
- Lambda duration, errors, throttles
- API Gateway latency, 4xx/5xx errors
- DynamoDB read/write capacity

### X-Ray Tracing (Automatic)
- Distributed tracing across services
- Performance bottleneck identification
- Service dependency mapping

## Security

### Secrets Management
- All secrets in AWS Secrets Manager
- GitHub Secrets for CI/CD credentials
- No secrets in code repository

### Network Security
- HTTPS only (API Gateway)
- Lambda in VPC (optional)
- Rate limiting enabled

### Data Encryption
- At rest: DynamoDB, S3, Secrets Manager
- In transit: HTTPS, TLS 1.2+

## Cost Optimization

### AWS Free Tier Usage
- Lambda: 1M requests/month free
- DynamoDB: 25GB storage free
- API Gateway: 1M requests/month free
- CloudWatch: 10 custom metrics free

### Production Costs (Estimated)
- Lambda: ~$5-20/month (depending on usage)
- DynamoDB: ~$2-10/month (on-demand)
- API Gateway: ~$3-15/month
- **Total**: ~$10-45/month for moderate usage

## Support

### Getting Help
1. Check GitHub Actions logs first
2. Review CloudWatch logs
3. Check X-Ray traces
4. Create GitHub issue with error details

### Useful Commands (Optional)
```bash
# Test API endpoint
curl -X GET "https://d7p93u5agk.execute-api.us-east-1.amazonaws.com/prod/health"

# View recent logs (if AWS CLI installed)
aws logs tail /aws/lambda/agentfirst-production --follow

# Check deployment status
aws cloudformation describe-stacks --stack-name agentfirst-lambda-production
```

## Next Steps

1. ✅ Configure GitHub Secrets (one-time)
2. ✅ Push code to main branch
3. ✅ Monitor deployment in GitHub Actions
4. ✅ Test API endpoints
5. ⏭️ Implement Telegram bot features
6. ⏭️ Add iFood integration
7. ⏭️ Implement billing system