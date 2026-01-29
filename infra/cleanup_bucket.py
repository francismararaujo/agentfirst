import boto3
import sys

def nuke_bucket(bucket_name):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    
    print(f"Nuking bucket: {bucket_name}")
    
    try:
        # Delete all object versions
        print("Deleting object versions...")
        bucket.object_versions.delete()
        
        # Delete all objects
        print("Deleting objects...")
        bucket.objects.all().delete()
        
        # Delete bucket
        print("Deleting bucket...")
        bucket.delete()
        print("Done!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cleanup_bucket.py <bucket_name>")
        sys.exit(1)
    
    nuke_bucket(sys.argv[1])
