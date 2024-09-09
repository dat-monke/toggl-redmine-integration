""" Tanner Bolt Montauk + ASI INFOR || These are pending creation for Project Name in Toggl"""

import tkinter as tk
from tkinter import ttk, filedialog
import csv
import pandas as pd
import requests

# Redmine API configuration
REDMINE_API_URL = "https://redmineb2b.silksoftware.com/"
REDMINE_API_KEY = "REPLACE WITH YOU API KEY HERE"
PROJECT_MAP = {
    "CMC Rescue": {"project_id": 3779},  # Replace with actual Redmine project IDs and activity IDs
    "HNR": {"project_id": 3503},
    "Pacific Research Laboratory": {"project_id": 3463},
    "Infinity Foil": {"project_id": 3829}, 
    "MISC": {"project_id": 17}, 
    "Tanner Bolt": {"project_id": 3229},
    "Tanner Bolt Montauk": {"project_id": 3620},
    "Vibration Mountings & Controls": {"project_id": 3794},
    "Wenger": {"project_id": 3479},
    "American Specialties": {"project_id": 3244},
    "ASI INFOR": {"project_id": 3523},
    "Aramsco": {"project_id": 3361},
    "Canarm": {"project_id": 3357},
    "P&R Electrical": {"project_id": 3790},
    "Travis Tile": {"project_id": 3722},
    "Duncan Supply": {"project_id": 3728}, 
    "Internal": {"project_id": 17},
    "SKC": {"project_id": 3752},
    # Add other projects as needed
}
ACTIVITY_ID = 9  # Default activity ID for logging time

def open_csv_file():
    file_path = filedialog.askopenfilename(title="Open CSV File", filetypes=[("CSV files", "*.csv")])
    if file_path:
        display_csv_data(file_path)

def round_up_15min(duration):
    # Convert string duration to a pandas Timedelta object
    duration = pd.to_timedelta(duration)
    
    # Add 15 minutes minus 1 second, then floor to 15-minute interval
    rounded_duration = (duration + pd.Timedelta(minutes=14, seconds=59)).floor('15T')
    
    # Convert to total seconds, then convert to hours in decimal (15-minute increments)
    total_seconds = rounded_duration.total_seconds()
    decimal_hours = total_seconds / 3600  # 3600 seconds in an hour
    
    return round(decimal_hours, 2)  # Round to 2 decimal places


def categorize_description(description):
    keywords = {
        'Ticket': 'Ticket',
        'Management': 'Management',
        'Meeting': 'Meeting'
    }
    for keyword, category in keywords.items():
        if keyword.lower() in description.lower():
            return category
    return 'Other'

def adjust_category(category):
    if category in ['Management', 'Ticket']:
        return 'Management'
    return category

def log_time_to_redmine(project_name, hours, description, date, category):
    """Logs time to Redmine using the provided data, with ACTIVITY_ID based on category."""
    project_info = PROJECT_MAP.get(project_name)
    if not project_info:
        print(f"Project {project_name} not found in Redmine project map.")
        return False

    project_id = project_info['project_id']

    # Determine the correct ACTIVITY_ID based on the 'Adjusted Category'
    if category in ['Management', 'Other']:
        activity_id = 13
    elif category == 'Meeting':
        activity_id = 15
    else:
        activity_id = project_info.get('activity_id', 13)  # Default activity ID if not specified

    payload = {
        "time_entry": {
            "project_id": project_id,
            "hours": hours,
            "comments": description,
            "spent_on": date,  # Date on which time was spent
            "activity_id": activity_id  # Redmine activity ID based on category
        }
    }

    headers = {
        "X-Redmine-API-Key": REDMINE_API_KEY,
        "Content-Type": "application/json"
    }

    response = requests.post(f"{REDMINE_API_URL}/time_entries.json", json=payload, headers=headers)

    if response.status_code == 200:
        print(f"Time logged successfully for project {project_name}: {hours} hours")
        return True
    else:
        print(f"Failed to log time for project {project_name}: {response.status_code} - {response.text}")
        return False


def display_csv_data(file_path):
    try:
        df = pd.read_csv(file_path)
        
        if 'Duration' not in df.columns:
            status_label.config(text="Error: 'Duration' column not found in CSV")
            return

        if 'Description' in df.columns:
            df['Category'] = df['Description'].apply(categorize_description)
        
        df['Adjusted Category'] = df['Category'].apply(adjust_category)

        columns_to_drop = ['Client', 'Task', 'Billable', 'Start Time', 'End Time', 'Tags']
        df.drop(columns=[col for col in columns_to_drop if col in df.columns], inplace=True)

        df['Duration'] = pd.to_timedelta(df['Duration'])

        grouped_df = df.groupby(['Start date', 'Project', 'Adjusted Category']).agg({
            'Duration': 'sum',  
            'Description': lambda x: '; '.join(sorted(set(x)))  
        }).reset_index()

        grouped_df['Converted Time'] = grouped_df['Duration'].apply(round_up_15min)

        grouped_df.drop(columns=['Duration'], inplace=True)

        for _, row in grouped_df.iterrows():
            project_name = row['Project']
            hours = row['Converted Time']
            description = row['Description']
            date = row['Start date']
            category = row['Adjusted Category']  # Get the 'Adjusted Category' for activity ID determination

            # Log time to Redmine with the category
            log_time_to_redmine(project_name, hours, description, date, category)

        tree.delete(*tree.get_children())

        tree["columns"] = list(grouped_df.columns)
        for col in grouped_df.columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)

        for _, row in grouped_df.iterrows():
            tree.insert("", "end", values=list(row))

        status_label.config(text=f"CSV file loaded: {file_path}")

    except Exception as e:
        status_label.config(text=f"Error: {str(e)}")

# Create the main tkinter window
root = tk.Tk()
root.title("CSV File Viewer")

# Button to open a CSV file
open_button = tk.Button(root, text="Open CSV File", command=open_csv_file)
open_button.pack(padx=20, pady=10)

# Treeview widget to display CSV data
tree = ttk.Treeview(root, show="headings")
tree.pack(padx=20, pady=20, fill="both", expand=True)

# Label to display the status of the application
status_label = tk.Label(root, text="", padx=20, pady=10)
status_label.pack()

# Run the tkinter main loop
root.mainloop()
