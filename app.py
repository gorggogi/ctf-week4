from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import csv
import os
import hashlib
import json
import subprocess
import tempfile

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

# Challenge data
STAGES = {
    1: {
        "name": "Circuit Identification",
        "description": "Analyze the provided circuit diagram and identify the logic gates used.",
        "hint": "Look at how the transistors are connected to identify standard logic gates.",
        "flag": "HTB{",
        "next_stage": 2,
        "correct_gates": ["AND", "AND", "OR"]  # Two AND gates followed by one OR gate
    },
    2: {
        "name": "Logic Gate Implementation",
        "description": "Based on your identified gates, calculate the outputs for these sample inputs.",
        "hint": "Remember: first perform the two AND operations, then combine with OR.",
        "flag": "4_G00d_Cm",
        "next_stage": 3,
        "sample_data": [
            [0, 1, 0, 0],
            [1, 0, 0, 1],
            [0, 0, 1, 1],
            [1, 1, 0, 0],
            [0, 1, 1, 1]
        ],
        "correct_output": "01001"  # Expected output for the sample data
    },
    3: {
        "name": "Circuit Automation",
        "description": "Process the full dataset using your understanding of the circuit.",
        "hint": "Write a script to perform the logical operations on all input rows.",
        "flag": "05_3x4mpl3}",
        "next_stage": None,  # Final stage
        "full_data_path": "static/files/input.csv"
    }
}

# Ensure user has completed previous stages
def check_stage_access(requested_stage):
    user_progress = session.get('completed_stages', [])
    print(f"User progress: {user_progress}")  # Debug print
    if requested_stage == 1 or (requested_stage > 1 and requested_stage - 1 in user_progress):
        return True
    return False

# Function to check if the flag is correct
def validate_flag(stage, submitted_flag):
    return submitted_flag.strip() == STAGES[stage]["flag"]

# Sample input processing function (for reference or server-side validation)
def process_sample_logic(inputs):
    results = []
    for row in inputs:
        input1, input2, input3, input4 = row
        and_output1 = input1 & input2  # First AND operation
        and_output2 = input3 & input4  # Second AND operation
        final_output = and_output1 | and_output2  # Final OR operation
        results.append(str(final_output))
    return ''.join(results)

@app.route('/')
def index():
    return render_template('index.html', stages=STAGES)

@app.route('/stage/<int:stage_id>', methods=['GET', 'POST'])
def stage(stage_id):
    print(f"Accessing stage {stage_id}")  # Debug print
    if not check_stage_access(stage_id):
        print("Access denied")  # Debug print
        return redirect(url_for('index'))
    
    if stage_id not in STAGES:
        return redirect(url_for('index'))
    
    stage_data = STAGES[stage_id]
    message = None
    show_flag_input = session.get('gates_identified', False) if stage_id == 1 else session.get('output_calculated', False)
    
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        
        if form_type == 'gates' and stage_id == 1:
            # Handle gate identification for stage 1
            gate1 = request.form.get('gate1', '').upper()
            gate2 = request.form.get('gate2', '').upper()
            gate3 = request.form.get('gate3', '').upper()
            
            if [gate1, gate2, gate3] == stage_data['correct_gates']:
                session['gates_identified'] = True
                show_flag_input = True
                message = "Correct! The circuit consists of two AND gates followed by an OR gate. Now you can submit the flag."
            else:
                message = "Incorrect gate identification. Try again!"
        elif form_type == 'output' and stage_id == 2:
            # Handle output calculation for stage 2
            submitted_output = request.form.get('output', '')
            
            if submitted_output == stage_data['correct_output']:
                session['output_calculated'] = True
                show_flag_input = True
                message = "Correct! You've successfully calculated the outputs. Now you can submit the flag."
            else:
                message = "Incorrect output calculation. Try again!"
        elif form_type == 'flag':
            # Handle flag submission
            submitted_flag = request.form.get('flag', '')
            print(f"Submitted flag: {submitted_flag}")  # Debug print
            print(f"Expected flag: {stage_data['flag']}")  # Debug print
            
            if validate_flag(stage_id, submitted_flag):
                if 'completed_stages' not in session:
                    session['completed_stages'] = []
                if stage_id not in session['completed_stages']:
                    session['completed_stages'].append(stage_id)
                    session.modified = True  # Ensure session is saved
                
                print(f"Updated completed stages: {session['completed_stages']}")  # Debug print
                
                # Clear the gate/output identification for the next stage
                if stage_id == 1:
                    session.pop('gates_identified', None)
                elif stage_id == 2:
                    session.pop('output_calculated', None)
                
                message = "Correct flag! "
                if stage_data['next_stage']:
                    message += "Moving to the next stage..."
                    return redirect(url_for('stage', stage_id=stage_data['next_stage']))
                else:
                    message += "Congratulations! You've completed all stages!"
                    return redirect(url_for('completion'))
            else:
                message = "Incorrect flag. Try again!"
    
    context = {
        'stage': stage_data,
        'stage_id': stage_id,
        'message': message,
        'show_flag_input': show_flag_input
    }
    
    if stage_id == 2:
        context['sample_data'] = stage_data['sample_data']
    
    return render_template('stage.html', **context)

@app.route('/completion')
def completion():
    # Check if user has completed all stages
    if set(session.get('completed_stages', [])) == set([1, 2, 3]):
        full_flag = STAGES[1]['flag'] + STAGES[2]['flag'] + STAGES[3]['flag']
        return render_template('completion.html', full_flag=full_flag)
    return redirect(url_for('index'))

@app.route('/hint/<int:stage_id>')
def get_hint(stage_id):
    if stage_id in STAGES:
        return STAGES[stage_id]['hint']
    return "No hint available"

@app.route('/reset')
def reset_progress():
    session.clear()
    return redirect(url_for('index'))

@app.route('/run_script', methods=['POST'])
def run_script():
    data = request.get_json()
    code = data.get('code', '')
    
    # Create a temporary file for the script
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_script:
        temp_script.write(code)
        temp_script_path = temp_script.name
    
    try:
        # Run the script with the input file
        result = subprocess.run(
            ['python', temp_script_path],
            capture_output=True,
            text=True,
            cwd=os.path.join(app.static_folder, 'files')
        )
        
        # Clean up the temporary file
        os.unlink(temp_script_path)
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'output': result.stdout
            })
        else:
            return jsonify({
                'success': False,
                'output': f"Error: {result.stderr}"
            })
    except Exception as e:
        # Clean up the temporary file in case of error
        if os.path.exists(temp_script_path):
            os.unlink(temp_script_path)
        return jsonify({
            'success': False,
            'output': f"Error: {str(e)}"
        })

@app.route('/submit_script', methods=['POST'])
def submit_script():
    data = request.get_json()
    code = data.get('code', '')
    
    # Create a temporary file for the script
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_script:
        temp_script.write(code)
        temp_script_path = temp_script.name
    
    try:
        # Run the script with the input file
        result = subprocess.run(
            ['python', temp_script_path],
            capture_output=True,
            text=True,
            cwd=os.path.join(app.static_folder, 'files')
        )
        
        # Clean up the temporary file
        os.unlink(temp_script_path)
        
        if result.returncode == 0:
            # Get the expected output from the full dataset
            expected_output = process_sample_logic([
                [0, 1, 0, 0],
                [1, 0, 0, 1],
                [0, 0, 1, 1],
                [1, 1, 0, 0],
                [0, 1, 1, 1]
            ])
            
            if result.stdout.strip() == expected_output:
                session['output_calculated'] = True
                return jsonify({
                    'success': True,
                    'message': "Correct! Your script produced the expected output."
                })
            else:
                return jsonify({
                    'success': False,
                    'message': "Incorrect output. Try again!"
                })
        else:
            return jsonify({
                'success': False,
                'message': f"Error: {result.stderr}"
            })
    except Exception as e:
        # Clean up the temporary file in case of error
        if os.path.exists(temp_script_path):
            os.unlink(temp_script_path)
        return jsonify({
            'success': False,
            'message': f"Error: {str(e)}"
        })

if __name__ == '__main__':
    app.run(debug=True)
