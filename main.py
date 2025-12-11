import subprocess
import sys

def main():
    print("Running data processing...")
    result = subprocess.run([sys.executable, "dataprocessing.py"], check=True)
    
    if result.returncode == 0:
        print("Data processing completed successfully!")
        print("\nLaunching Streamlit dashboard...")
        subprocess.run(["streamlit", "run", "dash1.py"])
    else:
        print("Data processing failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
