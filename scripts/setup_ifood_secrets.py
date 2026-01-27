#!/usr/bin/env python3
"""
Setup iFood Secrets - Configura credenciais do iFood no AWS Secrets Manager

Este script configura as credenciais necessárias para homologação com iFood:
- Client ID e Client Secret (OAuth 2.0)
- Merchant ID (ID do restaurante)
- Webhook Secret (para validação HMAC-SHA256)

IMPORTANTE: Execute este script ANTES da homologação
"""

import boto3
import json
import sys
from botocore.exceptions import ClientError


def setup_ifood_secrets():
    """
    Configura secrets do iFood no AWS Secrets Manager
    """
    print("🔐 Configurando credenciais do iFood...")
    
    # Credenciais de exemplo (SUBSTITUA pelas credenciais reais)
    ifood_credentials = {
        "client_id": "YOUR_IFOOD_CLIENT_ID",
        "client_secret": "YOUR_IFOOD_CLIENT_SECRET", 
        "merchant_id": "YOUR_IFOOD_MERCHANT_ID",
        "webhook_secret": "YOUR_IFOOD_WEBHOOK_SECRET"
    }
    
    # Verificar se são credenciais de exemplo
    if ifood_credentials["client_id"] == "YOUR_IFOOD_CLIENT_ID":
        print("❌ ERRO: Credenciais de exemplo detectadas!")
        print("\n📋 Para configurar as credenciais reais:")
        print("1. Acesse o Portal do Parceiro iFood")
        print("2. Vá em 'Integrações' > 'API'")
        print("3. Copie as credenciais:")
        print("   - Client ID")
        print("   - Client Secret")
        print("   - Merchant ID")
        print("   - Webhook Secret")
        print("4. Substitua os valores em setup_ifood_secrets.py")
        print("5. Execute novamente este script")
        return False
    
    try:
        # Criar cliente do Secrets Manager
        secrets_client = boto3.client('secretsmanager', region_name='us-east-1')
        
        secret_name = "AgentFirst/ifood-credentials"
        
        # Tentar criar o secret
        try:
            response = secrets_client.create_secret(
                Name=secret_name,
                Description="Credenciais do iFood para homologação",
                SecretString=json.dumps(ifood_credentials),
                Tags=[
                    {
                        'Key': 'Project',
                        'Value': 'AgentFirst2'
                    },
                    {
                        'Key': 'Environment',
                        'Value': 'production'
                    },
                    {
                        'Key': 'Service',
                        'Value': 'ifood-connector'
                    }
                ]
            )
            print(f"✅ Secret criado: {secret_name}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceExistsException':
                # Secret já existe, atualizar
                response = secrets_client.update_secret(
                    SecretId=secret_name,
                    SecretString=json.dumps(ifood_credentials)
                )
                print(f"✅ Secret atualizado: {secret_name}")
            else:
                raise e
        
        # Configurar rotação automática (opcional)
        try:
            secrets_client.update_secret(
                SecretId=secret_name,
                Description="Credenciais do iFood para homologação - Rotação automática habilitada"
            )
            print("🔄 Rotação automática configurada")
        except Exception as e:
            print(f"⚠️  Aviso: Não foi possível configurar rotação automática: {e}")
        
        print("\n🎉 Credenciais do iFood configuradas com sucesso!")
        print("\n📋 Próximos passos:")
        print("1. Verificar se as credenciais estão corretas")
        print("2. Testar autenticação com iFood")
        print("3. Executar testes de homologação")
        print("4. Agendar chamada de homologação com iFood")
        
        return True
        
    except ClientError as e:
        print(f"❌ Erro ao configurar secrets: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False


def verify_ifood_secrets():
    """
    Verifica se as credenciais do iFood estão configuradas
    """
    try:
        secrets_client = boto3.client('secretsmanager', region_name='us-east-1')
        
        secret_name = "AgentFirst/ifood-credentials"
        
        response = secrets_client.get_secret_value(SecretId=secret_name)
        credentials = json.loads(response['SecretString'])
        
        print("🔍 Verificando credenciais do iFood...")
        
        required_fields = ['client_id', 'client_secret', 'merchant_id', 'webhook_secret']
        missing_fields = []
        
        for field in required_fields:
            if field not in credentials or not credentials[field]:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Campos obrigatórios ausentes: {', '.join(missing_fields)}")
            return False
        
        # Verificar se não são valores de exemplo
        example_values = ['YOUR_IFOOD_CLIENT_ID', 'YOUR_IFOOD_CLIENT_SECRET', 
                         'YOUR_IFOOD_MERCHANT_ID', 'YOUR_IFOOD_WEBHOOK_SECRET']
        
        for field, value in credentials.items():
            if value in example_values:
                print(f"❌ Campo '{field}' ainda contém valor de exemplo")
                return False
        
        print("✅ Todas as credenciais estão configuradas corretamente")
        print(f"📋 Client ID: {credentials['client_id'][:8]}...")
        print(f"📋 Merchant ID: {credentials['merchant_id']}")
        
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print("❌ Credenciais do iFood não encontradas")
            print("Execute: python scripts/setup_ifood_secrets.py")
        else:
            print(f"❌ Erro ao verificar secrets: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False


def main():
    """
    Função principal
    """
    if len(sys.argv) > 1 and sys.argv[1] == 'verify':
        # Verificar credenciais existentes
        success = verify_ifood_secrets()
    else:
        # Configurar credenciais
        success = setup_ifood_secrets()
    
    if success:
        print("\n🚀 Sistema pronto para homologação com iFood!")
        sys.exit(0)
    else:
        print("\n❌ Configuração incompleta. Verifique os erros acima.")
        sys.exit(1)


if __name__ == "__main__":
    main()