import pandas as pd
from pybaseball import batting_stats

def export_player_data(filename: str):

    try:
        # Fetch batting stats using PyBaseball
        print(f"Fetching batting stats")
        data = batting_stats(2010, 2023, qual=1)
        
        # Export data to CSV
        print(f"Exporting data to {filename}...")
        data.to_csv(filename, index=False)
        print(f"Data successfully exported to {filename}.")
    
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    output_file = "batting_stats_2023.csv"  
    export_player_data(output_file)
    
