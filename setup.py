"""
Trading Bot Setup and Installation Script
Quick setup for Windows, Mac, and Linux
"""

import os
import sys
import subprocess
import platform

def main():
    print("\n" + "=" * 60)
    print("QUOTEX AI TRADING BOT - SETUP")
    print("=" * 60 + "\n")
    
    # Check Python version
    print(f"✓ Python Version: {sys.version}")
    
    if sys.version_info < (3, 8):
        print("✗ Python 3.8+ required!")
        return False
    
    # Install requirements
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed")
    except Exception as e:
        print(f"✗ Error installing dependencies: {e}")
        return False
    
    # Create directories
    print("\n📁 Creating directories...")
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    print("✓ Directories created")
    
    # Check for .env file
    print("\n🔐 Checking configuration...")
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            print("⚠ .env file not found. Creating from template...")
            with open(".env.example", "r") as f:
                env_content = f.read()
            with open(".env", "w") as f:
                f.write(env_content)
            print("✓ .env created - PLEASE EDIT WITH YOUR CREDENTIALS!")
        else:
            print("✗ .env.example not found")
            return False
    else:
        print("✓ .env file exists")
    
    # Print next steps
    print("\n" + "=" * 60)
    print("✓ SETUP COMPLETE!")
    print("=" * 60)
    
    print("\n📝 NEXT STEPS:")
    print("1. Edit .env file with your Quotex credentials:")
    print("   - QUOTEX_EMAIL=your_email@gmail.com")
    print("   - QUOTEX_PASSWORD=your_password")
    
    print("\n2. (Optional) Review config.py for trading settings")
    
    print("\n3. Start the bot:")
    if platform.system() == "Windows":
        print("   python bot.py")
    else:
        print("   python3 bot.py")
    
    print("\n" + "=" * 60)
    print("Happy Trading! 🚀")
    print("=" * 60 + "\n")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
