import csv

def validate_stage1_answer(answer):
    """
    Stage 1 expects users to identify the logic gates correctly
    """
    # We're looking for identification of two AND gates and one OR gate
    answer = answer.lower().strip()
    
    # Basic validation - this could be made more sophisticated
    required_terms = ['and', 'or']
    if all(term in answer for term in required_terms):
        return True
    return False

def validate_stage2_sample_outputs(sample_inputs):
    """
    Calculate the expected outputs for the sample inputs in stage 2
    """
    expected_outputs = []
    for row in sample_inputs:
        in0, in1, in2, in3 = row
        
        # Calculate expected output based on circuit logic
        and1_output = in0 & in1     # First AND gate
        and2_output = in2 & in3     # Second AND gate
        or_output = and1_output | and2_output  # OR gate
        
        expected_outputs.append(or_output)
        
    return expected_outputs

def validate_stage2_answer(answer, sample_inputs):
    """
    Stage 2 expects users to manually calculate outputs for sample inputs
    """
    # Get the expected outputs
    expected_outputs = validate_stage2_sample_outputs(sample_inputs)
    expected_string = ''.join(map(str, expected_outputs))
    
    # Compare with user's answer (allowing for some formatting differences)
    answer = answer.strip().replace(' ', '').replace(',', '')
    return answer == expected_string

def validate_stage3_answer(answer, input_file):
    """
    Stage 3 expects users to process the full input file and decode the flag
    """
    # Process the full input file
    expected_binary = process_full_input(input_file)
    
    # Convert to ASCII
    expected_ascii = binary_to_ascii(expected_binary)
    
    # The expected flag is HTB{4_G00d_Cm05_3x4mpl3}
    return answer.strip() == "HTB{4_G00d_Cm05_3x4mpl3}"

def process_full_input(input_file):
    """
    Process the full input file according to the circuit logic
    """
    results = []
    
    with open(input_file, mode='r') as infile:
        csvreader = csv.reader(infile)
        next(csvreader)  # Skip header
        
        for row in csvreader:
            input1 = int(row[0])
            input2 = int(row[1])
            input3 = int(row[2])
            input4 = int(row[3])
            
            and_output1 = input1 & input2  # First AND operation
            and_output2 = input3 & input4  # Second AND operation
            final_output = and_output1 | and_output2  # Final OR operation
            
            results.append(str(final_output))
    
    return ''.join(results)

def binary_to_ascii(binary_string):
    """
    Convert binary string to ASCII text
    """
    # Group binary string into 8-bit chunks
    byte_chunks = [binary_string[i:i+8] for i in range(0, len(binary_string), 8)]
    
    # Convert each 8-bit chunk to its decimal value, then to ASCII character
    ascii_string = ''.join([chr(int(chunk, 2)) for chunk in byte_chunks])
    
    return ascii_string

# Example usage:
if __name__ == "__main__":
    print("Stage 1 validation test:")
    print(validate_stage1_answer("The circuit contains two AND gates and one OR gate"))  # Should return True
    
    print("\nStage 2 validation test:")
    sample_inputs = [
        [0, 1, 0, 0],
        [1, 0, 0, 1],
        [0, 0, 1, 1],
        [1, 1, 0, 0],
        [0, 1, 1, 1]
    ]
    expected_outputs = validate_stage2_sample_outputs(sample_inputs)
    print(f"Expected outputs for sample inputs: {expected_outputs}")
    print(validate_stage2_answer("0,0,1,1,1", sample_inputs))  # Should return True
    
    # For stage 3, you would need the full input.csv file
    # print(validate_stage3_answer("HTB{4_G00d_Cm05_3x4mpl3}", "input.csv"))
