#!/usr/bin/env python3
"""
Real-Time Startup Script for Cheating Surveillance System
Starts all necessary services for real-time monitoring
"""

import os
import sys
import subprocess
import time
import signal
import threading
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        ('django', 'django'),
        ('channels', 'channels'),
        ('daphne', 'daphne'),
        ('websockets', 'websockets'),
        ('opencv-python', 'cv2'),
        ('numpy', 'numpy'),
        ('dlib', 'dlib'),
        ('tensorflow', 'tensorflow'),
        ('celery', 'celery'),
        ('redis', 'redis')
    ]
    
    missing_packages = []
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"   ✅ {package_name}")
        except ImportError:
            missing_packages.append(package_name)
            print(f"   ❌ {package_name}")
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Please install missing packages with: pip install " + " ".join(missing_packages))
        return False
    
    print("\n✅ All dependencies are installed")
    return True

def check_database():
    """Check and setup database"""
    print("🔍 Checking database...")
    
    try:
        # Run migrations
        subprocess.run([sys.executable, 'manage.py', 'migrate'], check=True, capture_output=True)
        print("✅ Database migrations completed")
        
        # Create superuser if needed
        result = subprocess.run([sys.executable, 'manage.py', 'shell', '-c', 
                               'from django.contrib.auth.models import User; print(User.objects.count())'], 
                              capture_output=True, text=True)
        
        if result.stdout.strip() == '0':
            print("⚠️ No users found. Creating test user...")
            subprocess.run([sys.executable, 'manage.py', 'shell', '-c', '''
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("Created admin user: admin/admin123")
'''], check=True)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Database setup failed: {e}")
        return False

def start_redis():
    """Start Redis server if not running"""
    print("🔍 Checking Redis...")
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis is running")
        return True
    except:
        print("⚠️ Redis not running. Please start Redis server manually.")
        print("   On Windows: Download and run Redis server")
        print("   On Linux/Mac: sudo service redis start")
        return False

def start_celery_worker():
    """Start Celery worker"""
    print("🚀 Starting Celery worker...")
    
    try:
        # Start Celery worker in background
        celery_process = subprocess.Popen([
            sys.executable, '-m', 'celery', '-A', 'surveillance_system', 'worker',
            '--loglevel=info', '--pool=solo'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for startup
        time.sleep(3)
        
        if celery_process.poll() is None:
            print("✅ Celery worker started")
            return celery_process
        else:
            print("❌ Celery worker failed to start")
            return None
    except Exception as e:
        print(f"❌ Failed to start Celery worker: {e}")
        return None

def start_daphne_server():
    """Start Daphne ASGI server"""
    print("🚀 Starting Daphne ASGI server...")
    
    try:
        # Start Daphne server
        daphne_process = subprocess.Popen([
            sys.executable, '-m', 'daphne', '-b', '0.0.0.0', '-p', '8000',
            'surveillance_system.asgi:application'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        time.sleep(5)
        
        if daphne_process.poll() is None:
            print("✅ Daphne ASGI server started on http://localhost:8000")
            return daphne_process
        else:
            print("❌ Daphne server failed to start")
            return None
    except Exception as e:
        print(f"❌ Failed to start Daphne server: {e}")
        return None

def run_tests():
    """Run system tests"""
    print("🧪 Running system tests...")
    
    try:
        # Run WebSocket tests
        result = subprocess.run([sys.executable, 'test_websocket.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ WebSocket tests passed")
        else:
            print("❌ WebSocket tests failed")
            print(result.stderr)
        
        # Run real-time tests
        result = subprocess.run([sys.executable, 'test_realtime.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Real-time tests passed")
        else:
            print("❌ Real-time tests failed")
            print(result.stderr)
        
        return True
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False

def cleanup(processes):
    """Cleanup function to stop all processes"""
    print("\n🛑 Shutting down services...")
    
    for process in processes:
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
    
    print("✅ All services stopped")

def main():
    """Main startup function"""
    print("🚀 Starting Cheating Surveillance System (Real-Time Mode)")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Check database
    if not check_database():
        return False
    
    # Check Redis
    if not start_redis():
        print("⚠️ Continuing without Redis (some features may not work)")
    
    processes = []
    
    try:
        # Start Celery worker
        celery_process = start_celery_worker()
        if celery_process:
            processes.append(celery_process)
        
        # Start Daphne server
        daphne_process = start_daphne_server()
        if daphne_process:
            processes.append(daphne_process)
        
        if not processes:
            print("❌ Failed to start required services")
            return False
        
        # Wait a moment for services to fully start
        time.sleep(3)
        
        # Run tests
        run_tests()
        
        print("\n" + "=" * 60)
        print("🎉 SYSTEM STARTUP COMPLETE!")
        print("=" * 60)
        print("📱 Access your system at: http://localhost:8000")
        print("📊 Monitoring dashboard: http://localhost:8000/monitoring/")
        print("📈 Analytics dashboard: http://localhost:8000/analytics/")
        print("🔗 Blockchain explorer: http://localhost:8000/blockchain/")
        print("\n💡 Real-time features enabled:")
        print("   ✅ Live video monitoring with WebSocket")
        print("   ✅ Real-time violation detection")
        print("   ✅ Live statistics updates")
        print("   ✅ Blockchain logging")
        print("   ✅ Performance monitoring")
        print("\n🛑 Press Ctrl+C to stop all services")
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Received shutdown signal...")
    except Exception as e:
        print(f"\n❌ Startup error: {e}")
    finally:
        cleanup(processes)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 