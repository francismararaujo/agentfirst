"""
Unit tests for User Documentation (Phase 13.2)

Tests the user documentation files and content:
- User guide completeness
- Telegram tutorial accuracy
- Upgrade guide structure
- Documentation consistency
"""

import pytest
import os
import re
from pathlib import Path


@pytest.mark.unit
class TestUserDocumentation:
    """Unit tests for User Documentation"""

    def test_user_guide_exists(self):
        """Test that user guide file exists"""
        user_guide_path = "docs/USER_GUIDE.md"
        assert os.path.exists(user_guide_path), "User guide should exist"

    def test_telegram_tutorial_exists(self):
        """Test that Telegram tutorial file exists"""
        telegram_tutorial_path = "docs/TELEGRAM_TUTORIAL.md"
        assert os.path.exists(telegram_tutorial_path), "Telegram tutorial should exist"

    def test_upgrade_guide_exists(self):
        """Test that upgrade guide file exists"""
        upgrade_guide_path = "docs/UPGRADE_GUIDE.md"
        assert os.path.exists(upgrade_guide_path), "Upgrade guide should exist"

    def test_user_guide_structure(self):
        """Test user guide has proper structure"""
        user_guide_path = "docs/USER_GUIDE.md"
        
        with open(user_guide_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for required sections
        required_sections = [
            "O que é o AgentFirst2?",
            "Como Começar",
            "Como Usar - Linguagem Natural",
            "Tiers e Limites",
            "Canais Disponíveis",
            "Contexto Unificado",
            "Supervisão Humana (H.I.T.L.)",
            "Monitoramento e Uso",
            "Configurações",
            "Perguntas Frequentes (FAQ)",
            "Suporte",
            "Próximos Passos"
        ]
        
        for section in required_sections:
            assert section in content, f"User guide should contain section: {section}"

    def test_user_guide_examples(self):
        """Test user guide contains practical examples"""
        user_guide_path = "docs/USER_GUIDE.md"
        
        with open(user_guide_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for example patterns
        example_patterns = [
            r"✅.*Quantos pedidos tenho",
            r"✅.*Qual foi meu faturamento",
            r"❌.*comandos como /pedidos",
            r"Você:.*Bot:",
            r"📧 Email:.*@.*\.com"
        ]
        
        for pattern in example_patterns:
            assert re.search(pattern, content), f"User guide should contain example pattern: {pattern}"

    def test_user_guide_tier_information(self):
        """Test user guide contains accurate tier information"""
        user_guide_path = "docs/USER_GUIDE.md"
        
        with open(user_guide_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check tier details
        tier_info = [
            "100 mensagens/mês",  # Free tier
            "10.000 mensagens/mês",  # Pro tier
            "R$ 99/mês",  # Pro price
            "ilimitado",  # Enterprise
            "Sob consulta"  # Enterprise price
        ]
        
        for info in tier_info:
            assert info in content, f"User guide should contain tier info: {info}"

    def test_telegram_tutorial_structure(self):
        """Test Telegram tutorial has proper structure"""
        telegram_tutorial_path = "docs/TELEGRAM_TUTORIAL.md"
        
        with open(telegram_tutorial_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for required sections
        required_sections = [
            "Primeiros Passos",
            "Como Conversar com o Bot",
            "Notificações Automáticas",
            "Supervisão Humana (H.I.T.L.)",
            "Monitoramento de Uso",
            "Configurações",
            "Comandos Especiais",
            "Dicas de Uso Eficiente",
            "Resolução de Problemas",
            "Recursos Avançados",
            "Exemplos Práticos"
        ]
        
        for section in required_sections:
            assert section in content, f"Telegram tutorial should contain section: {section}"

    def test_telegram_tutorial_bot_reference(self):
        """Test Telegram tutorial references correct bot"""
        telegram_tutorial_path = "docs/TELEGRAM_TUTORIAL.md"
        
        with open(telegram_tutorial_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for bot references
        bot_references = [
            "@AgentFirst2Bot",
            "https://t.me/AgentFirst2Bot"
        ]
        
        for reference in bot_references:
            assert reference in content, f"Telegram tutorial should reference: {reference}"

    def test_telegram_tutorial_commands(self):
        """Test Telegram tutorial contains command examples"""
        telegram_tutorial_path = "docs/TELEGRAM_TUTORIAL.md"
        
        with open(telegram_tutorial_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for command patterns
        command_patterns = [
            r"/approve esc_[a-z0-9]+",
            r"/reject esc_[a-z0-9]+",
            r"/start",
            r"/help"
        ]
        
        for pattern in command_patterns:
            assert re.search(pattern, content), f"Telegram tutorial should contain command: {pattern}"

    def test_upgrade_guide_structure(self):
        """Test upgrade guide has proper structure"""
        upgrade_guide_path = "docs/UPGRADE_GUIDE.md"
        
        with open(upgrade_guide_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for required sections
        required_sections = [
            "Por que Fazer Upgrade?",
            "Comparação de Planos",
            "Planos Disponíveis",
            "Como Fazer Upgrade",
            "Formas de Pagamento",
            "Processo de Ativação",
            "Novos Canais Disponíveis",
            "Analytics Avançado",
            "ROI do Upgrade",
            "Gestão da Assinatura",
            "Suporte Pós-Upgrade",
            "Próximos Passos"
        ]
        
        for section in required_sections:
            assert section in content, f"Upgrade guide should contain section: {section}"

    def test_upgrade_guide_pricing(self):
        """Test upgrade guide contains accurate pricing"""
        upgrade_guide_path = "docs/UPGRADE_GUIDE.md"
        
        with open(upgrade_guide_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check pricing information
        pricing_info = [
            "R$ 99/mês",  # Pro price
            "Sob consulta",  # Enterprise price
            "100 mensagens/mês",  # Free limit
            "10.000 mensagens/mês",  # Pro limit
            "Ilimitado"  # Enterprise limit
        ]
        
        for info in pricing_info:
            assert info in content, f"Upgrade guide should contain pricing: {info}"

    def test_upgrade_guide_payment_methods(self):
        """Test upgrade guide lists payment methods"""
        upgrade_guide_path = "docs/UPGRADE_GUIDE.md"
        
        with open(upgrade_guide_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check payment methods
        payment_methods = [
            "Cartão de Crédito",
            "PIX",
            "Boleto Bancário",
            "Transferência Bancária"
        ]
        
        for method in payment_methods:
            assert method in content, f"Upgrade guide should mention payment method: {method}"

    def test_documentation_consistency(self):
        """Test consistency across documentation files"""
        files = [
            "docs/USER_GUIDE.md",
            "docs/TELEGRAM_TUTORIAL.md", 
            "docs/UPGRADE_GUIDE.md"
        ]
        
        # Common elements that should be consistent
        consistent_elements = {
            "bot_username": "@AgentFirst2Bot",
            "pro_price": "R$ 99/mês",
            "free_limit": "100 mensagens/mês",
            "pro_limit": "10.000 mensagens/mês",
            "support_email": "support@agentfirst.com"
        }
        
        for file_path in files:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for element_name, element_value in consistent_elements.items():
                    assert element_value in content, f"{file_path} should contain consistent {element_name}: {element_value}"

    def test_documentation_links(self):
        """Test documentation contains valid link formats"""
        files = [
            "docs/USER_GUIDE.md",
            "docs/TELEGRAM_TUTORIAL.md",
            "docs/UPGRADE_GUIDE.md"
        ]
        
        # Link patterns to check
        link_patterns = [
            r"https://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",  # HTTPS URLs
            r"@[a-zA-Z0-9_]+",  # Telegram usernames
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"  # Email addresses
        ]
        
        for file_path in files:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check that file contains at least some links
                has_links = any(re.search(pattern, content) for pattern in link_patterns)
                assert has_links, f"{file_path} should contain valid links"

    def test_documentation_emojis(self):
        """Test documentation uses emojis appropriately"""
        files = [
            "docs/USER_GUIDE.md",
            "docs/TELEGRAM_TUTORIAL.md",
            "docs/UPGRADE_GUIDE.md"
        ]
        
        # Common emojis that should appear
        expected_emojis = ["🍔", "💰", "📱", "✅", "❌", "🎯", "📊"]
        
        for file_path in files:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check that file uses emojis
                emoji_count = sum(1 for emoji in expected_emojis if emoji in content)
                assert emoji_count > 0, f"{file_path} should use emojis for better readability"

    def test_documentation_code_blocks(self):
        """Test documentation contains proper code block formatting"""
        files = [
            "docs/USER_GUIDE.md",
            "docs/TELEGRAM_TUTORIAL.md",
            "docs/UPGRADE_GUIDE.md"
        ]
        
        for file_path in files:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for code blocks
                code_block_patterns = [
                    r"```[\s\S]*?```",  # Fenced code blocks
                    r"`[^`]+`"  # Inline code
                ]
                
                has_code_blocks = any(re.search(pattern, content) for pattern in code_block_patterns)
                # Not all files need code blocks, but if they have them, they should be properly formatted
                if has_code_blocks:
                    # Check that code blocks are properly closed
                    triple_backticks = content.count("```")
                    assert triple_backticks % 2 == 0, f"{file_path} should have properly closed code blocks"

    def test_documentation_headers(self):
        """Test documentation has proper header hierarchy"""
        files = [
            "docs/USER_GUIDE.md",
            "docs/TELEGRAM_TUTORIAL.md",
            "docs/UPGRADE_GUIDE.md"
        ]
        
        for file_path in files:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for proper header structure
                lines = content.split('\n')
                header_levels = []
                
                for line in lines:
                    if line.startswith('#'):
                        level = len(line) - len(line.lstrip('#'))
                        header_levels.append(level)
                
                # Should have at least some headers
                assert len(header_levels) > 0, f"{file_path} should have headers"
                
                # Should start with h1
                if header_levels:
                    assert header_levels[0] == 1, f"{file_path} should start with h1 header"

    def test_documentation_file_sizes(self):
        """Test documentation files are substantial but not too large"""
        files = [
            "docs/USER_GUIDE.md",
            "docs/TELEGRAM_TUTORIAL.md",
            "docs/UPGRADE_GUIDE.md"
        ]
        
        for file_path in files:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                
                # Should be substantial (at least 10KB)
                assert file_size > 10000, f"{file_path} should be substantial (>10KB), got {file_size} bytes"
                
                # Should not be too large (less than 500KB)
                assert file_size < 500000, f"{file_path} should not be too large (<500KB), got {file_size} bytes"


@pytest.mark.unit
class TestDocumentationContent:
    """Unit tests for documentation content accuracy"""

    def test_user_guide_contact_info(self):
        """Test user guide contains correct contact information"""
        user_guide_path = "docs/USER_GUIDE.md"
        
        with open(user_guide_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check contact information
        contact_info = [
            "support@agentfirst.com",
            "@AgentFirstSupport",
            "+55 11"  # Phone number pattern
        ]
        
        for info in contact_info:
            assert info in content, f"User guide should contain contact info: {info}"

    def test_telegram_tutorial_conversation_examples(self):
        """Test Telegram tutorial has realistic conversation examples"""
        telegram_tutorial_path = "docs/TELEGRAM_TUTORIAL.md"
        
        with open(telegram_tutorial_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for conversation patterns
        conversation_patterns = [
            r"👤 Você:.*",
            r"🤖 Bot:.*",
            r"Quantos pedidos",
            r"Confirme",
            r"Faturamento"
        ]
        
        for pattern in conversation_patterns:
            assert re.search(pattern, content), f"Telegram tutorial should contain conversation pattern: {pattern}"

    def test_upgrade_guide_roi_calculation(self):
        """Test upgrade guide contains ROI calculations"""
        upgrade_guide_path = "docs/UPGRADE_GUIDE.md"
        
        with open(upgrade_guide_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for ROI-related content
        roi_elements = [
            "ROI",
            "Retorno",
            "Investimento",
            "Payback",
            "Economia",
            "%"  # Percentage symbol
        ]
        
        for element in roi_elements:
            assert element in content, f"Upgrade guide should contain ROI element: {element}"

    def test_documentation_language_consistency(self):
        """Test documentation uses consistent Portuguese language"""
        files = [
            "docs/USER_GUIDE.md",
            "docs/TELEGRAM_TUTORIAL.md",
            "docs/UPGRADE_GUIDE.md"
        ]
        
        # Portuguese-specific words that should appear
        portuguese_words = [
            "você",
            "mensagem",
            "pedido",
            "restaurante",
            "configuração"
        ]
        
        for file_path in files:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                
                # Check for Portuguese words
                portuguese_count = sum(1 for word in portuguese_words if word in content)
                assert portuguese_count >= 3, f"{file_path} should use Portuguese language consistently"

    def test_documentation_feature_coverage(self):
        """Test documentation covers all major features"""
        files = [
            "docs/USER_GUIDE.md",
            "docs/TELEGRAM_TUTORIAL.md",
            "docs/UPGRADE_GUIDE.md"
        ]
        
        # Major features that should be documented
        major_features = [
            "iFood",
            "Telegram",
            "WhatsApp",
            "H.I.T.L",
            "Supervisão",
            "Analytics",
            "Billing",
            "Freemium"
        ]
        
        # Check that features are covered across all documentation
        all_content = ""
        for file_path in files:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    all_content += f.read()
        
        for feature in major_features:
            assert feature in all_content, f"Documentation should cover feature: {feature}"