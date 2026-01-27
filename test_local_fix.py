#!/usr/bin/env python3
"""
Local test to verify omnichannel fixes before deployment.
"""

import asyncio
import sys
import os

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Set test environment
os.environ['ENVIRONMENT'] = 'test'
os.environ['AWS_REGION'] = 'us-east-1'
os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'

async def test_channel_mapping_repository():
    """Test ChannelMappingRepository methods"""
    print("🧪 Testing ChannelMappingRepository...")
    
    try:
        from omnichannel.database.repositories import ChannelMappingRepository
        
        repo = ChannelMappingRepository()
        
        # Test get_by_email (should return empty list for non-existent user)
        mappings = await repo.get_by_email('test@example.com')
        print(f"✅ get_by_email works: {mappings}")
        
        # Test create_mapping
        mapping = await repo.create_mapping('telegram', '123456', 'test@example.com')
        print(f"✅ create_mapping works: {mapping}")
        
        return True
        
    except Exception as e:
        print(f"❌ ChannelMappingRepository error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_channel_mapping_service():
    """Test ChannelMappingService methods"""
    print("\n🧪 Testing ChannelMappingService...")
    
    try:
        from omnichannel.channel_mapping_service import ChannelMappingService
        from omnichannel.database.repositories import ChannelMappingRepository
        from omnichannel.models import ChannelType
        
        repo = ChannelMappingRepository()
        service = ChannelMappingService(repo)
        
        # Test get_channels_for_email
        channels = await service.get_channels_for_email('test@example.com')
        print(f"✅ get_channels_for_email works: {channels}")
        
        # Test create_mapping with metadata
        result = await service.create_mapping(
            email='test@example.com',
            channel='telegram',
            channel_user_id='123456',
            metadata={'test': 'data'}
        )
        print(f"✅ create_mapping with metadata works: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ ChannelMappingService error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting local omnichannel tests...\n")
    
    results = []
    
    # Test repository
    results.append(await test_channel_mapping_repository())
    
    # Test service
    results.append(await test_channel_mapping_service())
    
    # Summary
    print(f"\n📊 Test Results:")
    print(f"✅ Passed: {sum(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}")
    
    if all(results):
        print("\n🎉 All tests passed! Ready for deployment.")
        return True
    else:
        print("\n💥 Some tests failed. Fix errors before deployment.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)