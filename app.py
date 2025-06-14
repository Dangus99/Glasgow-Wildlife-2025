import pandas as pd # Library for data manipulation
from dash import Dash, html, dcc, Input, Output, State, dash_table, no_update # Main Dash library for building web applications
import dash_bootstrap_components as dbc # Bootstrap components for styling
from dash_bootstrap_templates import load_figure_template # Load Bootstrap templates for consistent styling

def is_time_valid(time):
    '''
    Checks whether input time has the correct syntax
    '''
    if (len(time) != 6) or (time[1]!=':') or (time[4]!='.'):
        return False
    else:
        return True

def is_first_time_faster(a,b):
    '''
    Compares whether a is faster than b; a and b are taken as strings
    SYNTAX: 0:00.0
    SYNTAX: M:SS.MS
    '''
    min_a = int(a[0]); min_b = int(b[0])
    sec_a = int(a[2]+a[3]); sec_b = int(b[2]+b[3])
    msec_a = int(a[5]); msec_b = int(b[5])
    if min_a < min_b:
        return True
    elif min_a > min_b:
        return False
    elif min_a == min_b:
        if sec_a < sec_b:
            return True
        elif sec_a > sec_b:
            return False
        elif sec_a == sec_b:
            if msec_a < msec_b:
                return True
            else: # TIE BREAKER! IF TIMES ARE EXACTLY THE SAME, b HAS PRIORITY
                return False
            
def Rank(data):
    rank = 1
    previous_time = None # Initialize previous_time to None for the first comparison
    previous_index = 0
    for count, row in data.iterrows(): # Iterate through the DataFrame to assign ranks
        current_time = row['Time'] # Get the current time for comparison
        if previous_time is None: # If this is the first row, assign rank 1
            data.at[count, 'Rank'] = rank # Assign rank 1 to the first racer
        elif current_time == previous_time: # If the current time is the same as the previous time, assign the same rank
            data.at[count, 'Rank'] = data.at[previous_index, 'Rank'] # Assign the same rank as the previous racer
        else:
            rank += 1 # Increment rank if the current time is different from the previous time
            data.at[count, 'Rank'] = rank # Assign the new rank to the current racer

        previous_time = current_time # Update previous_time for the next iteration
        previous_index = count # Update previous_index to the current index for the next iteration
    return data # Return the DataFrame with updated ranks

def Find_insertion_index(data, time):
    substitution_index = -1 # Default to -1 if no faster time is found
    for count, old_time in enumerate(data.Time): # Iterate through existing times and will stop at the first faster time
        if is_first_time_faster(time, old_time): # Check if the new time is faster than the current time
            substitution_index = count # If it is, we will insert the new racer here and break the loop.
            break

    if substitution_index == -1: # If no faster time was found, we will insert the new racer at the end of the list
        substitution_index = len(data)
    return substitution_index # Return the index where the new racer should be inserted

def Insert_new_racer(data, name, time, substitution_index):
    # Step 2: Insert new racer
    new_row = pd.DataFrame({'Racer': [name], 'Time': [time]}) # Create a new DataFrame for the new racer
    data = pd.concat([data.iloc[:substitution_index], new_row, data.iloc[substitution_index:]]).reset_index(drop=True) # Concatenate the new row into the existing DataFrame
    return data # Return the updated DataFrame with the new racer inserted

def add_remove_buttons(df):
    df['Remove'] = '❌'
    return df

# Load initial data from CSV this needs to be in the same directory as this script and the csv file should be tab-separated. You can use an excel spreadsheet to create it but you'll need to
# alter the code later that updates the file.
data_file = 'rankings.csv'
data = pd.read_csv(data_file, sep='\t')
data = add_remove_buttons(data) # Add a column for remove buttons

# Initialize Dash app with Bootstrap styling
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY]) # This creates the Dash app and applies the Flatly theme from Bootstrap
load_figure_template("FLATLY") # You can see the different themes here: https://www.dash-bootstrap-components.com/docs/themes/explorer/

# Define app layout: for more information see: https://dash.plotly.com/dash-core-components/layout and https://www.dash-bootstrap-components.com/docs/components/
app.layout = dbc.Container([
    dbc.Card([ # This creates a card component for the header and body
    dbc.CardHeader(html.H1("Race the Rat Track!", className="text-center text-primary")), # Card header with title
    dbc.CardBody([ # Card body with content
        html.H4("Can you solve a maze as fast as a rat?", className="card-title"), # Title inside the card body
        html.P("Can you beat Max Wiskstappen? Can you beat your fellow racers?", className="card-text"), # Description text
        dbc.Alert([ # Alert component for instructions
            html.P("Pick up the maze and get the marble to the finish line by tilting the board!", className="mb-1"), # Instruction text
            html.P("We will time you and record your time. When I shout 'GO!' you can start. When you reach the finish line, tell me so that I can stop the timer. Then, enter your ratty name and time in the form below.")
        ], color="info", className="mt-3"),
        dbc.Alert("⚠️ Please be careful not to throw the marble off the board! If it falls off, place it back where it last fell and continue.", color="warning")
        ])
    ], className="mb-4"),

    dash_table.DataTable( # This creates a data table to display the racers and their times. https://dash.plotly.com/datatable
        id='racer-table', # This is used in the callback to update the table
        data=data.to_dict('records'), 
        columns=[{"name": i, "id": i, "presentation": "markdown"} if i == "Remove" else {"name": i, "id": i} for i in data.columns],
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left'}
    ),
    html.Hr(), # Horizontal rule to separate sections

    dbc.Row([ # This creates a row for the input form
        dbc.Col(dcc.Input(id='input-name', type='text', placeholder='Name', className='form-control'), width=4),
        dbc.Col(dcc.Input(id='input-time', type='text', placeholder='m:ss.ms', className='form-control'), width=4),
        dbc.Col(html.Button('Add Racer', id='add-button', n_clicks=0, className='btn btn-primary w-100'), width=2)
    ], className="mb-3"),
    html.Div(id='confirmation', className='mt-2 text-success'), # This div will show confirmation messages after adding a racer

    html.H2("Additional Information"), # Section for additional information
    html.Ul([
        html.Li(html.A("Do Lab Rats Dream of Running Mazes?", href="https://youtu.be/bkfxpiTmMGw", target="_blank")),
        html.Li(html.A("Dynamics of Awake Hippocampal-Prefrontal Replay for Spatial Learning and Memory-Guided Decision Making", href="https://doi.org/10.1016/j.neuron.2019.09.012", target="_blank")),
        html.Li(html.A("Visit Glasgow Science Festival", href="https://www.gla.ac.uk/events/sciencefestival/gsf2025/", target="_blank"))
    ])

], fluid=True)

# Callback to handle racer addition
@app.callback(
    Output('racer-table', 'data', allow_duplicate=True), # Output to update the data table with new racer information
    Output('confirmation', 'children'), # Output to show confirmation message
    Input('add-button', 'n_clicks'), # Triggered when the button is clicked
    State('input-name', 'value'), # Get the name input value
    State('input-time', 'value'), # Get the time input value
    prevent_initial_call=True
)
def add_racer(n_clicks, name, time):
    if not name or not time: # Check if name or time is empty
        return no_update, "Please enter both name and time."

    if not is_time_valid(time): # Validate time format
        return no_update, "Time not input correctly! Format should be m:ss.s"

    # Load current data
    data = pd.read_csv(data_file, sep='\t')
    # Find substitution index
    substitution_index = Find_insertion_index(data, time)
    # Insert new racer
    data = Insert_new_racer(data, name, time, substitution_index)
    # Step 3: Recalculate ranks
    data = Rank(data).drop(columns=['remove']) # Step 3: Recalculate ranks after adding the new racer

    # Step 4: Save updated data
    data.to_csv(data, index=False, sep='\t') # Save the updated DataFrame back to the CSV file

    return data.to_dict('records'), f"Racer {name} added successfully!" # This returns the updated data and a confirmation message

@app.callback(
    Output('racer-table', 'data', allow_duplicate=True),
    Input('racer-table', 'active_cell'),
    State('racer-table', 'data'),
    prevent_initial_call=True
)
def delete_row(active_cell, table_data):
    if active_cell and active_cell['column_id'] == 'Remove': # Check if the active cell is in the 'Remove' column
        row_index = active_cell['row'] # Get the index of the row to be deleted
        updated_data = table_data[:row_index] + table_data[row_index+1:] # Create a new list excluding the row to be deleted

        df = pd.DataFrame(updated_data).drop(columns=['Remove']) # Convert the updated data back to a DataFrame and drop the 'Remove' column
        df = Rank(df)  # Recalculate ranks after deletion
        df.to_csv(data_file, index=False, sep='\t') # Save the updated DataFrame back to the CSV file
        
        return add_remove_buttons(df).to_dict('records') # Return the updated data with remove buttons added back
    return no_update