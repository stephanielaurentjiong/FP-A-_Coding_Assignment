import pandas as pd
import os

def test_csv_files():
    """Simple test to make sure our CSV files load correctly"""
    # Check if files exist
    files = ['actuals.csv', 'budget.csv', 'cash.csv', 'fx.csv']
    
    for file in files:
        file_path = f'fixtures/{file}'
        if os.path.exists(file_path):
            print(f"✅ {file} exists")
            
            # Try to load it
            try:
                df = pd.read_csv(file_path)
                print(f"   - Loaded {len(df)} rows, {len(df.columns)} columns")
                print(f"   - Columns: {list(df.columns)}")
                print()
            except Exception as e:
                print(f"❌ Error loading {file}: {e}")
        else:
            print(f"❌ {file} not found")

if __name__ == "__main__":
    print("Testing CSV file setup...\n")
    test_csv_files()
    print("Test complete!")